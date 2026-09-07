from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.classroom import ClassroomSession, ContextItem
from ml.translation.engine import LayeredTranslationEngine

class ClassroomService:
    @staticmethod
    def create_session(
        db: Session,
        teacher_id: str,
        class_grade: int = 2,
        subject: str = "Mathematics",
        topic: str = "Addition up to 20",
        learning_outcome: Optional[str] = None,
        target_language: str = "sat",
        school_id: Optional[str] = None
    ) -> ClassroomSession:
        # Expire any previous active sessions for this teacher to prevent context leakage
        prev_sessions = db.query(ClassroomSession).filter_by(teacher_id=teacher_id, is_active=True).all()
        for s in prev_sessions:
            s.is_active = False
        db.commit()

        session = ClassroomSession(
            teacher_id=teacher_id,
            school_id=school_id or "GPS_DUMKA_01",
            class_grade=class_grade,
            subject=subject,
            topic=topic,
            learning_outcome=learning_outcome or f"Foundational understanding of {topic}",
            target_language=target_language,
            is_active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Add initial topic vocabulary context item
        item = ContextItem(
            session_id=session.id,
            item_type="topic_init",
            content={"topic": topic, "grade": class_grade, "subject": subject}
        )
        db.add(item)
        db.commit()

        return session

    @staticmethod
    def add_context_item(
        db: Session,
        session_id: str,
        item_type: str,  # dialogue, vocabulary, command, instruction
        content: Dict[str, Any]
    ) -> ContextItem:
        session = db.query(ClassroomSession).filter_by(id=session_id, is_active=True).first()
        if not session:
            raise HTTPException(status_code=404, detail="Active classroom session not found")

        item = ContextItem(
            session_id=session.id,
            item_type=item_type,
            content=content
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_session_context(db: Session, session_id: str) -> Dict[str, Any]:
        session = db.query(ClassroomSession).filter_by(id=session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        items = db.query(ContextItem).filter_by(session_id=session_id).all()
        return {
            "session_id": session.id,
            "teacher_id": session.teacher_id,
            "class_grade": session.class_grade,
            "subject": session.subject,
            "topic": session.topic,
            "learning_outcome": session.learning_outcome,
            "target_language": session.target_language,
            "is_active": session.is_active,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "recent_items": [
                {"id": it.id, "type": it.item_type, "content": it.content, "created_at": it.created_at.isoformat()}
                for it in items[-20:]  # Limit to 20 most recent items to preserve bounded memory
            ]
        }

    @classmethod
    def execute_context_command(
        cls,
        db: Session,
        session_id: str,
        command_text: str
    ) -> Dict[str, Any]:
        """
        Interprets context-aware teacher commands referring to current lesson context.
        Section 16:
        - 'Create a worksheet from today's lesson'
        - 'Give me three easy questions'
        - 'Explain this activity in the target language'
        - 'Give me flashcards for today's vocabulary'
        """
        session = db.query(ClassroomSession).filter_by(id=session_id, is_active=True).first()
        if not session:
            raise HTTPException(status_code=404, detail="Active session not found")

        cmd = command_text.strip().lower()
        engine = LayeredTranslationEngine(db)

        # Command: Give questions / worksheet
        if "question" in cmd or "प्रश्न" in cmd or "सवाल" in cmd:
            questions = [
                {
                    "prompt_hindi": f"गिनो और बताओ: {session.topic} में कितने हैं?",
                    "prompt_target": engine.translate(f"गिनो और बताओ: कितने हैं?", tgt_lang=session.target_language)["target_text"],
                    "difficulty": "EASY"
                },
                {
                    "prompt_hindi": "अपनी कॉपी में चित्र देखकर सही संख्या लिखो।",
                    "prompt_target": engine.translate("अपनी कॉपी में लिखो", tgt_lang=session.target_language)["target_text"],
                    "difficulty": "EASY"
                },
                {
                    "prompt_hindi": "दो और तीन मिलाकर कितने होते हैं?",
                    "prompt_target": engine.translate("तीन और दो मिलाकर कितने होते हैं?", tgt_lang=session.target_language)["target_text"],
                    "difficulty": "EASY"
                }
            ]
            return {
                "command": command_text,
                "action": "GENERATE_QUESTIONS",
                "session_topic": session.topic,
                "result": questions
            }

        # Command: Explain activity in target language
        elif "explain" in cmd or "activity" in cmd or "गतिविधि" in cmd or "समझाओ" in cmd:
            explanation_hi = f"बच्चों, आज हम {session.topic} सीखेंगे। कंकड़ या बीजों को मिलाकर गिनेंगे।"
            explanation_sat = engine.translate(explanation_hi, tgt_lang=session.target_language)["target_text"]
            return {
                "command": command_text,
                "action": "EXPLAIN_ACTIVITY",
                "explanation_hindi": explanation_hi,
                "explanation_target": explanation_sat,
                "target_language": session.target_language
            }

        # Command: Flashcards
        elif "flashcard" in cmd or "कार्ड" in cmd or "शब्द" in cmd:
            return {
                "command": command_text,
                "action": "GENERATE_FLASHCARDS",
                "session_topic": session.topic,
                "suggested_concepts": ["एक (mit')", "दो (bar)", "तीन (pe)", "गिनती (lekha)", "जोड़ (mesa)"]
            }

        # General contextual translation
        else:
            trans = engine.translate(command_text, tgt_lang=session.target_language)
            return {
                "command": command_text,
                "action": "CONTEXTUAL_TRANSLATION",
                "translation": trans["target_text"],
                "confidence": trans["confidence"],
                "tier": trans["tier"]
            }
