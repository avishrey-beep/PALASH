from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.classroom_service import ClassroomService

router = APIRouter(prefix="/context", tags=["Classroom Context"])

class AddContextItemRequest(BaseModel):
    item_type: str  # dialogue, vocabulary, command, instruction
    content: Dict[str, Any]

class ContextCommandRequest(BaseModel):
    command: str

@router.post("/{session_id}/items")
def add_context_item(session_id: str, req: AddContextItemRequest, db: Session = Depends(get_db)):
    """Appends an interaction item (dialogue or instruction) to temporary classroom context."""
    item = ClassroomService.add_context_item(
        db=db,
        session_id=session_id,
        item_type=req.item_type,
        content=req.content
    )
    return {
        "item_id": item.id,
        "session_id": item.session_id,
        "item_type": item.item_type
    }

@router.get("/{session_id}")
def get_context(session_id: str, db: Session = Depends(get_db)):
    """Retrieves current classroom context and recent bounded dialogue history."""
    return ClassroomService.get_session_context(db, session_id)

@router.post("/{session_id}/command")
def execute_context_command(session_id: str, req: ContextCommandRequest, db: Session = Depends(get_db)):
    """
    Executes context-aware commands (Section 16):
    e.g. 'Create a worksheet from today's lesson', 'Give me three easy questions',
    'Explain this activity in the target language', 'Give me flashcards for today's vocabulary'.
    """
    return ClassroomService.execute_context_command(
        db=db,
        session_id=session_id,
        command_text=req.command
    )
