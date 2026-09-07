import hashlib
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.translation import Phrase
from ml.preprocessing.normalizer import TextNormalizer

class PhraseCacheEngine:
    """
    Tier 1 Instant Phrase Cache for common classroom expressions.
    Operates with deterministic hashing and sub-10ms lookup latency.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        # In-memory LRU / hash map for extreme speed in hot paths
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def compute_cache_key(src_lang: str, tgt_lang: str, text: str) -> str:
        clean_text = TextNormalizer.clean_for_cache(text)
        raw_key = f"{src_lang}:{tgt_lang}:{clean_text}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def add_to_memory(self, cache_key: str, data: Dict[str, Any]):
        self._memory_cache[cache_key] = data

    def lookup(self, text: str, src_lang: str = "hin", tgt_lang: str = "sat") -> Optional[Dict[str, Any]]:
        cache_key = self.compute_cache_key(src_lang, tgt_lang, text)
        
        # 1. Check in-memory hot cache
        if cache_key in self._memory_cache:
            hit = self._memory_cache[cache_key]
            return {
                "target_text": hit["target_text"],
                "confidence": hit.get("confidence", 1.0),
                "tier": "cache_memory",
                "audio_asset_path": hit.get("audio_asset_path"),
                "verification_status": hit.get("verification_status", "human_verified")
            }

        # 2. Check Database if session available
        if self.db:
            phrase = self.db.query(Phrase).filter_by(cache_key=cache_key).first()
            if phrase:
                result = {
                    "target_text": phrase.target_text,
                    "confidence": phrase.confidence,
                    "tier": "cache_exact",
                    "audio_asset_path": phrase.audio_asset_path,
                    "verification_status": phrase.verification_status
                }
                # Populate hot cache
                self._memory_cache[cache_key] = result
                # Increment usage frequency
                try:
                    phrase.usage_frequency += 1
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                return result

        return None
