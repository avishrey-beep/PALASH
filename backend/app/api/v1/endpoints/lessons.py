from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.curriculum import Lesson, Curriculum

router = APIRouter(prefix="/lessons", tags=["Lessons"])


@router.get("")
def list_lessons(
    curriculum_id: Optional[str] = None,
    class_grade: Optional[int] = None,
    subject: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List lessons for the mobile lesson browser, newest curriculum first.

    Filterable by ``curriculum_id`` directly, or by ``class_grade``/``subject``
    which resolve through the parent Curriculum. Returns a lightweight summary
    (no full activities/assessments payload) plus total count for pagination;
    the client fetches the detail view via ``GET /lessons/{id}``.
    """
    query = db.query(Lesson).join(Curriculum, Lesson.curriculum_id == Curriculum.id)

    if curriculum_id:
        query = query.filter(Lesson.curriculum_id == curriculum_id)
    if class_grade is not None:
        query = query.filter(Curriculum.class_grade == class_grade)
    if subject:
        query = query.filter(Curriculum.subject == subject)

    total = query.count()
    lessons = (
        query.order_by(Lesson.unit_number, Lesson.lesson_number)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "lessons": [
            {
                "id": l.id,
                "curriculum_id": l.curriculum_id,
                "unit_number": l.unit_number,
                "lesson_number": l.lesson_number,
                "title_hindi": l.title_hindi,
                "topic": l.topic,
                # Counts only in the list view; full arrays are in the detail route.
                "learning_outcomes_count": len(l.learning_outcomes or []),
                "vocabulary_count": len(l.vocabulary or []),
                "version": l.current_version,
            }
            for l in lessons
        ],
    }


@router.get("/{lesson_id}")
def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    """Retrieves specific lesson details including learning outcomes and activities."""
    lesson = db.query(Lesson).filter_by(id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {
        "id": lesson.id,
        "curriculum_id": lesson.curriculum_id,
        "lesson_number": lesson.lesson_number,
        "title_hindi": lesson.title_hindi,
        "topic": lesson.topic,
        "learning_outcomes": lesson.learning_outcomes,
        "activities": lesson.activities,
        "assessments": lesson.assessments,
        "vocabulary": lesson.vocabulary,
        "version": lesson.current_version
    }
