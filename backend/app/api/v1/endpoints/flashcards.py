from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.flashcard_service import FlashcardService

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])

class CreateFlashcardRequest(BaseModel):
    concept: str
    category: str
    hindi_term: str
    target_language: str = "sat"
    target_term: Optional[str] = None
    pronunciation: Optional[str] = None

@router.post("")
def create_flashcard(req: CreateFlashcardRequest, db: Session = Depends(get_db)):
    """Creates or retrieves a deterministic multilingual flashcard."""
    return FlashcardService.create_or_get_flashcard(
        db=db,
        concept=req.concept,
        category=req.category,
        hindi_term=req.hindi_term,
        target_language=req.target_language,
        target_term=req.target_term,
        pronunciation=req.pronunciation
    )

@router.get("")
def list_flashcards(category: Optional[str] = None, target_language: str = "sat", db: Session = Depends(get_db)):
    """Lists flashcards by category and language."""
    return FlashcardService.list_flashcards(db=db, category=category, target_language=target_language)
