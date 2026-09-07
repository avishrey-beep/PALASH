from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.translation_service import TranslationService
from backend.app.services.auth_service import require_roles, get_current_user
from backend.app.models.translation import Phrase, GlossaryTerm, ReviewTask
from backend.app.models.user import User

router = APIRouter(prefix="/translation", tags=["Translation"])

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "hin"
    target_lang: str = "sat"
    context_topic: Optional[str] = None

class AddPhraseRequest(BaseModel):
    source_text: str
    target_text: str
    source_lang: str = "hin"
    target_lang: str = "sat"
    domain: str = "classroom"
    class_grade: Optional[int] = 2
    subject: Optional[str] = "General"
    audio_asset_path: Optional[str] = None

class ReviewDecisionRequest(BaseModel):
    decision: str  # APPROVE, EDIT, REJECT
    corrected_translation: Optional[str] = None
    reason: Optional[str] = None

@router.post("/translate")
def translate_text(req: TranslationRequest, db: Session = Depends(get_db)):
    """
    Executes layered translation (Cache -> TM -> Glossary -> Model -> Post-processing).
    Returns translated text, latency, confidence, and tier used.
    """
    return TranslationService.translate_text(
        db,
        text=req.text,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
        context_topic=req.context_topic
    )

@router.post("/phrases", status_code=status.HTTP_201_CREATED)
def add_verified_phrase(
    req: AddPhraseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "LANGUAGE_REVIEWER", "CURRICULUM_MANAGER"]))
):
    """Adds a human-verified classroom expression to the Tier 1 instant phrase cache."""
    phrase = TranslationService.add_verified_phrase(
        db,
        source_text=req.source_text,
        target_text=req.target_text,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
        domain=req.domain,
        class_grade=req.class_grade,
        subject=req.subject,
        audio_asset_path=req.audio_asset_path
    )
    return {
        "id": phrase.id,
        "cache_key": phrase.cache_key,
        "source_text": phrase.source_text,
        "target_text": phrase.target_text,
        "verification_status": phrase.verification_status
    }

@router.get("/phrases")
def list_phrases(
    target_lang: str = "sat",
    domain: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists pre-translated phrases in the cache."""
    q = db.query(Phrase).filter_by(target_lang=target_lang)
    if domain:
        q = q.filter_by(domain=domain)
    phrases = q.limit(limit).all()
    return [
        {
            "id": p.id,
            "source_text": p.source_text,
            "target_text": p.target_text,
            "domain": p.domain,
            "confidence": p.confidence,
            "audio_asset_path": p.audio_asset_path
        }
        for p in phrases
    ]

@router.get("/review/tasks")
def list_review_tasks(
    status_filter: str = "PENDING",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "LANGUAGE_REVIEWER"]))
):
    """Lists pending translation items in the human review queue."""
    tasks = db.query(ReviewTask).filter_by(status=status_filter).all()
    return [
        {
            "id": t.id,
            "source_text": t.source_text,
            "source_lang": t.source_lang,
            "target_lang": t.target_lang,
            "model_translation": t.model_translation,
            "model_name": t.model_name,
            "status": t.status
        }
        for t in tasks
    ]

@router.post("/review/tasks/{task_id}/decision")
def record_review_decision(
    task_id: str,
    req: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "LANGUAGE_REVIEWER"]))
):
    """Records a native-speaker reviewer decision (APPROVE, EDIT, REJECT) and updates the TM."""
    return TranslationService.record_review_decision(
        db,
        task_id=task_id,
        reviewer_id=current_user.id,
        decision=req.decision,
        corrected_translation=req.corrected_translation,
        reason=req.reason
    )

@router.get("/glossary")
def list_glossary_terms(
    target_lang: str = "sat",
    domain: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists educational terminology dictionary terms."""
    q = db.query(GlossaryTerm).filter_by(target_lang=target_lang)
    if domain:
        q = q.filter_by(domain=domain)
    terms = q.all()
    return [
        {
            "id": t.id,
            "hindi_term": t.hindi_term,
            "target_term": t.target_term,
            "domain": t.domain,
            "pronunciation": t.pronunciation,
            "approved_translation": t.approved_translation
        }
        for t in terms
    ]
