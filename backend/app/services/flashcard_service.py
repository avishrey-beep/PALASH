import hashlib
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.content import Flashcard
from ml.translation.engine import LayeredTranslationEngine

class FlashcardService:
    @staticmethod
    def get_deterministic_id(concept: str, category: str, target_lang: str) -> str:
        raw = f"{category.strip().lower()}:{concept.strip().lower()}:{target_lang.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def create_or_get_flashcard(
        cls,
        db: Session,
        concept: str,
        category: str,
        hindi_term: str,
        target_language: str = "sat",
        target_term: Optional[str] = None,
        pronunciation: Optional[str] = None
    ) -> Dict[str, Any]:
        det_id = cls.get_deterministic_id(concept, category, target_language)
        existing = db.query(Flashcard).filter_by(deterministic_id=det_id).first()
        if existing:
            return {
                "flashcard_id": existing.id,
                "deterministic_id": existing.deterministic_id,
                "concept": existing.concept,
                "category": existing.category,
                "hindi_term": existing.hindi_term,
                "target_term": existing.target_term,
                "target_language": existing.target_language,
                "pronunciation": existing.pronunciation,
                "image_asset_path": existing.image_asset_path,
                "audio_asset_path": existing.audio_asset_path
            }

        # Resolve target translation if not passed
        engine = LayeredTranslationEngine(db)
        resolved_target = target_term or engine.translate(hindi_term, src_lang="hin", tgt_lang=target_language)["target_text"]

        fc = Flashcard(
            deterministic_id=det_id,
            concept=concept,
            category=category,
            hindi_term=hindi_term,
            target_term=resolved_target,
            target_language=target_language,
            pronunciation=pronunciation,
            image_asset_path=f"images/flashcards/{concept.lower()}.png",
            audio_asset_path=f"audio/flashcards/{det_id[:12]}.wav"
        )
        db.add(fc)
        db.commit()
        db.refresh(fc)

        return {
            "flashcard_id": fc.id,
            "deterministic_id": fc.deterministic_id,
            "concept": fc.concept,
            "category": fc.category,
            "hindi_term": fc.hindi_term,
            "target_term": fc.target_term,
            "target_language": fc.target_language,
            "pronunciation": fc.pronunciation,
            "image_asset_path": fc.image_asset_path,
            "audio_asset_path": fc.audio_asset_path
        }

    @staticmethod
    def list_flashcards(
        db: Session,
        category: Optional[str] = None,
        target_language: str = "sat"
    ) -> List[Dict[str, Any]]:
        query = db.query(Flashcard).filter_by(target_language=target_language)
        if category:
            query = query.filter_by(category=category)
        cards = query.all()
        return [
            {
                "id": c.id,
                "concept": c.concept,
                "category": c.category,
                "hindi_term": c.hindi_term,
                "target_term": c.target_term,
                "target_language": c.target_language,
                "pronunciation": c.pronunciation,
                "image_asset_path": c.image_asset_path,
                "audio_asset_path": c.audio_asset_path
            }
            for c in cards
        ]
