import re
from typing import List, Tuple, Optional
from ml.preprocessing.normalizer import TextNormalizer

class DatasetCleaner:
    """
    Validation, cleaning, and deduplication pipeline for bilingual educational datasets.
    """

    @staticmethod
    def is_devanagari(text: str) -> bool:
        # Devanagari Unicode block: U+0900 to U+097F
        return bool(re.search(r"[\u0900-\u097F]", text))

    @staticmethod
    def is_ol_chiki(text: str) -> bool:
        # Ol Chiki Unicode block: U+1C50 to U+1C7F
        return bool(re.search(r"[\u1C50-\u1C7F]", text))

    @classmethod
    def clean_pair(cls, src_text: str, tgt_text: str, src_lang: str = "hin", tgt_lang: str = "sat") -> Optional[Tuple[str, str]]:
        if not src_text or not tgt_text:
            return None
        
        src_clean = TextNormalizer.normalize(src_text, src_lang)
        tgt_clean = TextNormalizer.normalize(tgt_text, tgt_lang)

        # 1. Length validation (avoid empty or excessively long utterances)
        if len(src_clean) < 2 or len(tgt_clean) < 2:
            return None
        if len(src_clean) > 500 or len(tgt_clean) > 500:
            return None

        # 2. Length ratio check (ratio should be within 0.25 to 4.0)
        len_ratio = len(src_clean) / max(len(tgt_clean), 1)
        if len_ratio < 0.25 or len_ratio > 4.0:
            return None

        # 3. Script validation if expected
        if src_lang == "hin" and not cls.is_devanagari(src_clean):
            # Might be numeric or Latin borrow, accept if contains numbers or punctuation
            if not re.search(r"[0-9a-zA-Z]", src_clean):
                return None

        return src_clean, tgt_clean

    @classmethod
    def deduplicate(cls, pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        seen = set()
        deduped = []
        for src, tgt in pairs:
            key = (src.strip().lower(), tgt.strip())
            if key not in seen:
                seen.add(key)
                deduped.append((src, tgt))
        return deduped
