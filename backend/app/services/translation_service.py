from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.translation import Phrase, TranslationMemoryItem, GlossaryTerm, ReviewTask, ReviewDecision
from ml.translation.engine import LayeredTranslationEngine
from ml.translation.cache import PhraseCacheEngine

class TranslationService:
    @staticmethod
    def translate_text(
        db: Session,
        text: str,
        source_lang: str = "hin",
        target_lang: str = "sat",
        context_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        engine = LayeredTranslationEngine(db)
        return engine.translate(text, src_lang=source_lang, tgt_lang=target_lang, context_topic=context_topic)

    @staticmethod
    def add_verified_phrase(
        db: Session,
        source_text: str,
        target_text: str,
        source_lang: str = "hin",
        target_lang: str = "sat",
        domain: str = "classroom",
        class_grade: Optional[int] = 2,
        subject: Optional[str] = "General",
        audio_asset_path: Optional[str] = None
    ) -> Phrase:
        cache_key = PhraseCacheEngine.compute_cache_key(source_lang, target_lang, source_text)
        existing = db.query(Phrase).filter_by(cache_key=cache_key).first()
        if existing:
            existing.target_text = target_text
            existing.verification_status = "human_verified"
            existing.confidence = 1.0
            existing.version += 1
            if audio_asset_path:
                existing.audio_asset_path = audio_asset_path
            db.commit()
            db.refresh(existing)
            return existing

        phrase = Phrase(
            cache_key=cache_key,
            source_lang=source_lang,
            target_lang=target_lang,
            source_text=source_text,
            target_text=target_text,
            domain=domain,
            class_grade=class_grade,
            subject=subject,
            confidence=1.0,
            verification_status="human_verified",
            audio_asset_path=audio_asset_path,
            version=1
        )
        db.add(phrase)
        db.commit()
        db.refresh(phrase)
        return phrase

    @staticmethod
    def submit_for_review(
        db: Session,
        source_text: str,
        model_translation: str,
        source_lang: str = "hin",
        target_lang: str = "sat",
        model_name: Optional[str] = None
    ) -> ReviewTask:
        task = ReviewTask(
            source_text=source_text,
            model_translation=model_translation,
            source_lang=source_lang,
            target_lang=target_lang,
            model_name=model_name or "layered_engine",
            status="PENDING"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def record_review_decision(
        db: Session,
        task_id: str,
        reviewer_id: str,
        decision: str,  # APPROVE, EDIT, REJECT
        corrected_translation: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        task = db.query(ReviewTask).filter_by(id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Review task not found")

        dec = ReviewDecision(
            review_task_id=task.id,
            reviewer_id=reviewer_id,
            original_translation=task.model_translation,
            corrected_translation=corrected_translation,
            decision=decision,
            reason=reason
        )
        db.add(dec)

        task.status = decision
        db.commit()

        # If approved or edited, automatically feed into Translation Memory and Phrase Cache
        approved_target = corrected_translation if decision == "EDIT" else task.model_translation
        if decision in ["APPROVE", "EDIT"]:
            TranslationService.add_verified_phrase(
                db,
                source_text=task.source_text,
                target_text=approved_target,
                source_lang=task.source_lang,
                target_lang=task.target_lang
            )
            # Add to TM
            tm = TranslationMemoryItem(
                source_lang=task.source_lang,
                target_lang=task.target_lang,
                source_text=task.source_text,
                target_text=approved_target,
                domain="education",
                verification_status="human_verified",
                quality_score=1.0,
                source_type="reviewer_submission"
            )
            db.add(tm)
            db.commit()

        return {
            "task_id": task.id,
            "decision": decision,
            "approved_target": approved_target,
            "status": "RECORDED"
        }
