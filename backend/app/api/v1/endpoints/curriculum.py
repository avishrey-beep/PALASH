from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.curriculum_service import CurriculumService
from backend.app.services.auth_service import require_roles, get_current_user
from backend.app.models.curriculum import Curriculum, CurriculumVersion, Lesson
from backend.app.models.user import User

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

@router.post("/upload")
def upload_curriculum(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    class_grade: Optional[int] = Form(None),
    subject: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "CURRICULUM_MANAGER"]))
):
    """
    Ingests curriculum document (PDF, DOCX, TXT, JSON).
    Performs security validation, structural segmentation, outcome extraction, and versioning.
    """
    return CurriculumService.ingest_document(
        db=db,
        file=file,
        title=title,
        class_grade=class_grade,
        subject=subject
    )

@router.get("")
def list_curricula(class_grade: Optional[int] = None, subject: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists versioned curricula matching grade and subject filters."""
    query = db.query(Curriculum)
    if class_grade:
        query = query.filter_by(class_grade=class_grade)
    if subject:
        query = query.filter_by(subject=subject)
    curricula = query.all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "state": c.state,
            "board": c.board,
            "class_grade": c.class_grade,
            "subject": c.subject,
            "current_version": c.current_version,
            "description": c.description,
            "lessons_count": len(c.lessons)
        }
        for c in curricula
    ]

@router.get("/{curriculum_id}")
def get_curriculum_detail(curriculum_id: str, db: Session = Depends(get_db)):
    """Retrieves detailed curriculum information and its associated lessons."""
    c = db.query(Curriculum).filter_by(id=curriculum_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    
    return {
        "id": c.id,
        "title": c.title,
        "class_grade": c.class_grade,
        "subject": c.subject,
        "current_version": c.current_version,
        "lessons": [
            {
                "id": l.id,
                "lesson_number": l.lesson_number,
                "title_hindi": l.title_hindi,
                "topic": l.topic,
                "learning_outcomes": l.learning_outcomes,
                "activities": l.activities,
                "assessments": l.assessments,
                "vocabulary": l.vocabulary,
                "version": l.current_version
            }
            for l in c.lessons
        ]
    }
