from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.classroom_service import ClassroomService
from backend.app.services.auth_service import get_current_user
from backend.app.models.classroom import ClassroomSession
from backend.app.models.user import User

router = APIRouter(prefix="/classrooms", tags=["Classroom Sessions"])

class CreateSessionRequest(BaseModel):
    class_grade: int = 2
    subject: str = "Mathematics"
    topic: str = "Addition up to 20"
    learning_outcome: Optional[str] = None
    target_language: str = "sat"
    school_id: Optional[str] = None

@router.post("/sessions")
def create_session(
    req: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a temporary, privacy-respecting classroom session for a teacher."""
    session = ClassroomService.create_session(
        db=db,
        teacher_id=current_user.id,
        class_grade=req.class_grade,
        subject=req.subject,
        topic=req.topic,
        learning_outcome=req.learning_outcome,
        target_language=req.target_language,
        school_id=req.school_id or current_user.school_id
    )
    return {
        "session_id": session.id,
        "class_grade": session.class_grade,
        "subject": session.subject,
        "topic": session.topic,
        "learning_outcome": session.learning_outcome,
        "target_language": session.target_language,
        "expires_at": session.expires_at.isoformat()
    }

@router.get("/sessions/active")
def get_active_session(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieves teacher's currently active classroom session."""
    session = db.query(ClassroomSession).filter_by(teacher_id=current_user.id, is_active=True).first()
    if not session:
        return {"active_session": None}
    return {
        "active_session": {
            "session_id": session.id,
            "class_grade": session.class_grade,
            "subject": session.subject,
            "topic": session.topic,
            "target_language": session.target_language,
            "expires_at": session.expires_at.isoformat()
        }
    }

@router.post("/sessions/{session_id}/end")
def end_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Ends classroom session and expires ephemeral context."""
    session = db.query(ClassroomSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_active = False
    db.commit()
    return {"status": "SESSION_ENDED", "session_id": session_id}
