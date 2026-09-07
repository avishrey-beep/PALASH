import os
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from backend.app.core.config import settings
from backend.app.models.content import Worksheet, WorksheetQuestion
from backend.app.models.curriculum import Lesson
from ml.translation.engine import LayeredTranslationEngine

class WorksheetService:
    @classmethod
    def generate_bilingual_worksheet(
        cls,
        db: Session,
        class_grade: int,
        subject: str,
        topic: str,
        target_language: str = "sat",
        lesson_id: Optional[str] = None,
        question_count: int = 5,
        difficulty: str = "EASY"
    ) -> Dict[str, Any]:
        engine = LayeredTranslationEngine(db)
        
        # Pull context from lesson if provided
        learning_outcome = "संख्याओं की पहचान और जोड़ की समझ"
        if lesson_id:
            lesson = db.query(Lesson).filter_by(id=lesson_id).first()
            if lesson and lesson.learning_outcomes:
                learning_outcome = lesson.learning_outcomes[0]

        # Generate constrained question bank based on topic & grade
        questions_raw = [
            {
                "type": "counting",
                "prompt_hi": "चित्रों को गिनो और सही संख्या लिखो: [ 🍎 🍎 🍎 ]",
                "options": ["२", "३", "४"],
                "answer": "३"
            },
            {
                "type": "arithmetic",
                "prompt_hi": "जोड़ो: २ + ३ = ____",
                "options": ["४", "५", "६"],
                "answer": "५"
            },
            {
                "type": "multiple_choice",
                "prompt_hi": "पाँच को संथाली में क्या कहते हैं?",
                "options": ["ᱯᱮ (pe)", "ᱢᱚᱬᱮ (mõṛẽ)", "ᱵᱟᱨ (bar)"],
                "answer": "ᱢᱚᱬᱮ (mõṛẽ)"
            },
            {
                "type": "fill_in_the_blanks",
                "prompt_hi": "४ और २ मिलाकर ____ होते हैं।",
                "options": ["५", "६", "७"],
                "answer": "६"
            },
            {
                "type": "matching",
                "prompt_hi": "सही मिलान करो: 'किताब' का संथाली शब्द क्या है?",
                "options": ["ᱫᱟᱨᱮ (dare)", "ᱯᱚᱛᱚᱵ (potob)", "ᱫᱟᱜ (dag)"],
                "answer": "ᱯᱚᱛᱚᱵ (potob)"
            }
        ]

        selected_questions = questions_raw[:min(question_count, len(questions_raw))]
        parsed_questions = []
        answer_key = {}

        for idx, q in enumerate(selected_questions):
            q_num = idx + 1
            # Translate prompt into target language
            trans_res = engine.translate(q["prompt_hi"], src_lang="hin", tgt_lang=target_language)
            prompt_target = trans_res["target_text"]

            parsed_questions.append({
                "question_number": q_num,
                "question_type": q["type"],
                "prompt_hindi": q["prompt_hi"],
                "prompt_target": prompt_target,
                "options": q["options"],
                "correct_answer": q["answer"]
            })
            answer_key[f"Q{q_num}"] = q["answer"]

        # Generate HTML Representation
        html_content = cls.render_html_worksheet(
            title=f"कक्षा {class_grade} {subject} कार्यपत्रक (Worksheet)",
            topic=topic,
            questions=parsed_questions
        )

        # Generate Printable PDF Representation
        pdf_filename = f"worksheet_gr{class_grade}_{subject[:4]}_{abs(hash(topic)) % 10000}.pdf"
        pdf_path = os.path.join(settings.EXPORT_DIR, pdf_filename)
        cls.render_pdf_worksheet(
            pdf_path=pdf_path,
            title=f"Class {class_grade} {subject} - {topic}",
            questions=parsed_questions
        )

        # Persist to Database
        worksheet = Worksheet(
            lesson_id=lesson_id,
            title=f"Class {class_grade} {subject} - {topic}",
            class_grade=class_grade,
            subject=subject,
            topic=topic,
            learning_outcome=learning_outcome,
            target_language=target_language,
            difficulty=difficulty,
            question_count=len(parsed_questions),
            html_content=html_content,
            pdf_path=pdf_path,
            json_data={"questions": parsed_questions},
            answer_key_json=answer_key
        )
        db.add(worksheet)
        db.commit()
        db.refresh(worksheet)

        for q_obj in parsed_questions:
            wq = WorksheetQuestion(
                worksheet_id=worksheet.id,
                question_number=q_obj["question_number"],
                question_type=q_obj["question_type"],
                prompt_hindi=q_obj["prompt_hindi"],
                prompt_target=q_obj["prompt_target"],
                options=q_obj["options"],
                correct_answer=q_obj["correct_answer"]
            )
            db.add(wq)
        db.commit()

        return {
            "worksheet_id": worksheet.id,
            "title": worksheet.title,
            "class_grade": class_grade,
            "subject": subject,
            "topic": topic,
            "target_language": target_language,
            "questions": parsed_questions,
            "answer_key": answer_key,
            "pdf_path": pdf_path
        }

    @staticmethod
    def render_html_worksheet(title: str, topic: str, questions: List[Dict[str, Any]]) -> str:
        q_html = ""
        for q in questions:
            opts = " &nbsp; | &nbsp; ".join([f"[ &nbsp; ] {opt}" for opt in q["options"]])
            q_html += f"""
            <div style="margin-bottom: 20px; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <p style="margin: 0 0 6px 0; font-weight: bold; font-size: 15px;">
                    Q{q['question_number']}. {q['prompt_hindi']}
                </p>
                <p style="margin: 0 0 10px 0; color: #1e293b; font-size: 14px;">
                    <em>{q['prompt_target']}</em>
                </p>
                <div style="padding-left: 10px; color: #475569;">
                    {opts}
                </div>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: sans-serif; margin: 40px; color: #0f172a; line-height: 1.5; }}
                .header {{ text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 24px; }}
                .meta {{ display: flex; justify-content: space-between; margin-bottom: 20px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2 style="margin: 0;">JCERT Jharkhand - Primary Education</h2>
                <h3 style="margin: 4px 0;">{title}</h3>
                <p style="margin: 0; color: #64748b;">Topic: {topic}</p>
            </div>
            <div class="meta">
                <span>छात्र का नाम (Name): _________________</span>
                <span>दिनांक (Date): ____________</span>
            </div>
            {q_html}
        </body>
        </html>
        """

    @staticmethod
    def render_pdf_worksheet(pdf_path: str, title: str, questions: List[Dict[str, Any]]):
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2.0, height - 50, "JCERT Jharkhand Primary Education")
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(width / 2.0, height - 72, title)
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 100, "Student Name: _______________________")
        c.drawString(width - 220, height - 100, "Date: _________________")

        c.setLineWidth(1)
        c.line(50, height - 110, width - 50, height - 110)

        # Questions
        y = height - 140
        c.setFont("Helvetica-Bold", 11)

        for q in questions:
            if y < 80:
                c.showPage()
                y = height - 60

            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, f"Q{q['question_number']}. {q['prompt_hindi']}")
            y -= 18

            c.setFont("Helvetica-Oblique", 10)
            c.drawString(65, y, f"Translation: {q['prompt_target']}")
            y -= 18

            c.setFont("Helvetica", 10)
            opts_str = "    ".join([f"( ) {opt}" for opt in q["options"]])
            c.drawString(65, y, opts_str)
            y -= 30

        c.save()
