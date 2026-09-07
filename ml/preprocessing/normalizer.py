import re
import unicodedata
from typing import Dict

# Ol Chiki digits 0-9: ᱐ ᱑ ᱒ ᱓ ᱔ ᱕ ᱖ ᱗ ᱘ ᱙ (U+1C50 to U+1C59)
OL_CHIKI_DIGITS = "᱐᱑᱒᱓᱔᱕᱖᱗᱘᱙"
DEVANAGARI_DIGITS = "०१२३४५६७८९"
LATIN_DIGITS = "0123456789"

DIGIT_MAP_TO_LATIN: Dict[str, str] = {}
for i in range(10):
    DIGIT_MAP_TO_LATIN[OL_CHIKI_DIGITS[i]] = LATIN_DIGITS[i]
    DIGIT_MAP_TO_LATIN[DEVANAGARI_DIGITS[i]] = LATIN_DIGITS[i]

class TextNormalizer:
    """
    Production-grade text normalization for Hindi (Devanagari) and Santhali (Ol Chiki).
    Ensures deterministic cache matching and high-quality translation inputs.
    """

    @staticmethod
    def normalize_unicode(text: str) -> str:
        if not text:
            return ""
        # Standardize Unicode to NFC form
        text = unicodedata.normalize("NFC", text)
        # Remove zero-width non-joiner and joiner unless critical
        text = text.replace("\u200c", "").replace("\u200d", "")
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def normalize_digits(text: str) -> str:
        """Converts Devanagari and Ol Chiki digits to standard ASCII digits for consistent numeracy processing."""
        res = []
        for char in text:
            res.append(DIGIT_MAP_TO_LATIN.get(char, char))
        return "".join(res)

    @classmethod
    def normalize(cls, text: str, lang: str = "hin") -> str:
        if not text:
            return ""
        text = cls.normalize_unicode(text)
        
        # Punctuation normalization
        text = text.replace("।", "।") # danda
        text = text.replace("॥", "॥")
        text = text.replace("?", "?").replace("!", "!").replace(",", ",")
        
        # Remove space before punctuation marks
        text = re.sub(r"\s+([।,॥\?!;\:\)\]])", r"\1", text)

        # Trim multiple punctuation
        text = re.sub(r"[\?!।\.]+$", lambda m: m.group(0)[0], text)
        
        # Lowercase for Latin or case-sensitive scripts
        if lang in ["en", "eng"]:
            text = text.lower()
            
        return text.strip()

    @classmethod
    def clean_for_cache(cls, text: str) -> str:
        """Removes trailing punctuation and normalizes spaces for exact cache lookup."""
        normalized = cls.normalize_unicode(text).lower()
        # Remove trailing question marks, periods, dandas for flexible matching
        cleaned = re.sub(r"[\?।!\.,;]+$", "", normalized).strip()
        return cleaned
