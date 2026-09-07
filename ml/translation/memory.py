import difflib
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.translation import TranslationMemoryItem
from ml.preprocessing.normalizer import TextNormalizer
from ml.preprocessing.tokenizer import SimpleTokenizer

class TranslationMemoryEngine:
    """
    Tier 2 Translation Memory (TM) for similarity retrieval.
    Enables retrieving verified translations of close utterances without blind substitution.
    """

    def __init__(self, db: Optional[Session] = None, similarity_threshold: float = 0.70):
        self.db = db
        self.similarity_threshold = similarity_threshold
        self._local_entries: List[Dict[str, Any]] = []

    def load_from_list(self, entries: List[Dict[str, Any]]):
        self._local_entries = entries

    @staticmethod
    def compute_similarity(s1: str, s2: str) -> float:
        # 1. Character-level Levenshtein ratio
        seq_ratio = difflib.SequenceMatcher(None, s1, s2).ratio()
        
        # 2. Token-level Jaccard similarity
        t1 = set(SimpleTokenizer.tokenize(s1.lower()))
        t2 = set(SimpleTokenizer.tokenize(s2.lower()))
        if not t1 or not t2:
            token_ratio = 0.0
        else:
            token_ratio = len(t1.intersection(t2)) / len(t1.union(t2))
            
        # Weighted composite similarity
        return (0.6 * seq_ratio) + (0.4 * token_ratio)

    def find_best_match(self, text: str, src_lang: str = "hin", tgt_lang: str = "sat") -> Optional[Dict[str, Any]]:
        norm_text = TextNormalizer.clean_for_cache(text)
        best_match = None
        best_score = 0.0

        # Check DB entries if available
        candidates = []
        if self.db:
            items = self.db.query(TranslationMemoryItem).filter_by(
                source_lang=src_lang,
                target_lang=tgt_lang
            ).limit(200).all()
            for item in items:
                candidates.append({
                    "source_text": item.source_text,
                    "target_text": item.target_text,
                    "quality_score": item.quality_score,
                    "verification_status": item.verification_status
                })
        
        candidates.extend(self._local_entries)

        for candidate in candidates:
            score = self.compute_similarity(norm_text, candidate["source_text"])
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match and best_score >= self.similarity_threshold:
            return {
                "matched_source": best_match["source_text"],
                "target_text": best_match["target_text"],
                "similarity_score": round(best_score, 3),
                "confidence": round(best_score * best_match.get("quality_score", 1.0), 3),
                "tier": "translation_memory",
                "verification_status": best_match.get("verification_status", "human_verified")
            }

        return None
