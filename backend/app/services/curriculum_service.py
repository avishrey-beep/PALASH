import os
import re
import hashlib
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from backend.app.core.config import settings
from backend.app.models.curriculum import Curriculum, CurriculumVersion, Lesson, LessonVersion

class CurriculumService:
    @staticmethod
    def calculate_checksum(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @classmethod
    def parse_curriculum_text(cls, raw_text: str) -> Dict[str, Any]:
        """
        Extracts structured pedagogical components from curriculum text:
        Lessons, Learning Outcomes, Activities, Assessments, and Vocabulary.
        """
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        title = "JCERT Primary Curriculum"
        class_grade = 2
        subject = "Mathematics"
        lessons = []
        current_lesson = None

        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("GRADE:"):
                try:
                    class_grade = int(line.replace("GRADE:", "").strip())
                except ValueError:
                    class_grade = 2
            elif line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
            elif line.startswith("LESSON:") or line.startswith("पाठ:"):
                if current_lesson:
                    lessons.append(current_lesson)
                lesson_title = re.sub(r"^(LESSON:|पाठ:)", "", line).strip()
                current_lesson = {
                    "lesson_number": len(lessons) + 1,
                    "title_hindi": lesson_title,
                    "topic": lesson_title,
                    "learning_outcomes": [],
                    "activities": [],
                    "assessments": [],
                    "vocabulary": []
                }
            elif current_lesson:
                if line.startswith("OUTCOME:") or line.startswith("उद्देश्य:"):
                    current_lesson["learning_outcomes"].append(re.sub(r"^(OUTCOME:|उद्देश्य:)", "", line).strip())
                elif line.startswith("ACTIVITY:") or line.startswith("गतिविधि:"):
                    current_lesson["activities"].append(re.sub(r"^(ACTIVITY:|गतिविधि:)", "", line).strip())
                elif line.startswith("ASSESSMENT:") or line.startswith("मूल्यांकन:"):
                    current_lesson["assessments"].append(re.sub(r"^(ASSESSMENT:|मूल्यांकन:)", "", line).strip())
                elif line.startswith("VOCAB:") or line.startswith("शब्दावली:"):
                    vocab_items = [v.strip() for v in re.sub(r"^(VOCAB:|शब्दावली:)", "", line).split(",") if v.strip()]
                    current_lesson["vocabulary"].extend(vocab_items)

        if current_lesson:
            lessons.append(current_lesson)

        # Fallback if no explicit tags found
        if not lessons:
            lessons.append({
                "lesson_number": 1,
                "title_hindi": title,
                "topic": title,
                "learning_outcomes": ["Foundational literacy and concept mastery"],
                "activities": ["Teacher demonstration and peer practice"],
                "assessments": ["Oral questioning and workbook practice"],
                "vocabulary": ["जोड़", "गिनती"]
            })

        return {
            "title": title,
            "class_grade": class_grade,
            "subject": subject,
            "lessons": lessons
        }

    @classmethod
    def ingest_document(
        cls,
        db: Session,
        file: UploadFile,
        title: Optional[str] = None,
        class_grade: Optional[int] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Validation: file size and extension
        filename = file.filename or "curriculum.txt"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file format {ext}")

        content = file.file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="File exceeds maximum allowed upload size")

        checksum = cls.calculate_checksum(content)

        # Save original file securely
        save_name = f"{checksum[:12]}_{filename}"
        save_path = os.path.join(settings.UPLOAD_DIR, save_name)
        with open(save_path, "wb") as f:
            f.write(content)

        # 2. Text Extraction
        raw_text = content.decode("utf-8", errors="ignore")
        parsed = cls.parse_curriculum_text(raw_text)

        curriculum_title = title or parsed["title"]
        grade = class_grade or parsed["class_grade"]
        subj = subject or parsed["subject"]

        # 3. Create or Update Curriculum
        curriculum = db.query(Curriculum).filter_by(title=curriculum_title, class_grade=grade, subject=subj).first()
        if not curriculum:
            curriculum = Curriculum(
                title=curriculum_title,
                state="Jharkhand",
                board="JCERT",
                class_grade=grade,
                subject=subj,
                medium="Hindi",
                current_version=1
            )
            db.add(curriculum)
            db.commit()
            db.refresh(curriculum)
            version_num = 1
        else:
            curriculum.current_version += 1
            version_num = curriculum.current_version
            db.commit()

        # 4. Save Version Record
        c_ver = CurriculumVersion(
            curriculum_id=curriculum.id,
            version_number=version_num,
            checksum=checksum,
            source_file_path=save_path,
            status="PUBLISHED",
            changelog=f"Ingested from file {filename} (v{version_num})"
        )
        db.add(c_ver)
        db.commit()

        # 5. Ingest / Update Lessons
        created_lessons = []
        for l_data in parsed["lessons"]:
            lesson = db.query(Lesson).filter_by(
                curriculum_id=curriculum.id,
                lesson_number=l_data["lesson_number"]
            ).first()

            if not lesson:
                lesson = Lesson(
                    curriculum_id=curriculum.id,
                    unit_number=1,
                    lesson_number=l_data["lesson_number"],
                    title_hindi=l_data["title_hindi"],
                    topic=l_data["topic"],
                    learning_outcomes=l_data["learning_outcomes"],
                    activities=l_data["activities"],
                    assessments=l_data["assessments"],
                    vocabulary=l_data["vocabulary"],
                    current_version=1
                )
                db.add(lesson)
                db.commit()
                db.refresh(lesson)
            else:
                lesson.title_hindi = l_data["title_hindi"]
                lesson.topic = l_data["topic"]
                lesson.learning_outcomes = l_data["learning_outcomes"]
                lesson.activities = l_data["activities"]
                lesson.assessments = l_data["assessments"]
                lesson.vocabulary = l_data["vocabulary"]
                lesson.current_version += 1
                db.commit()

            # Lesson Version
            l_ver = LessonVersion(
                lesson_id=lesson.id,
                version_number=lesson.current_version,
                checksum=cls.calculate_checksum(str(l_data).encode("utf-8")),
                content_json=l_data,
                status="PUBLISHED"
            )
            db.add(l_ver)
            created_lessons.append(lesson.id)

        db.commit()

        return {
            "curriculum_id": curriculum.id,
            "title": curriculum.title,
            "version": version_num,
            "checksum": checksum,
            "lessons_count": len(created_lessons),
            "status": "INGESTED_AND_PUBLISHED"
        }
