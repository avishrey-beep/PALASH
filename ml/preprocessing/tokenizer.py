import re
from typing import List

class SimpleTokenizer:
    """
    Lightweight rule-based tokenizer for Hindi and tribal languages.
    Splits on whitespace and isolates punctuation without heavy runtime dependencies.
    """

    PUNCT_PATTERN = re.compile(r"([।,॥\?!;\:\(\)\[\]\"'–—])")

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        if not text:
            return []
        # Add spaces around punctuation
        spaced = cls.PUNCT_PATTERN.sub(r" \1 ", text)
        tokens = [t for t in spaced.split() if t]
        return tokens

    @classmethod
    def detokenize(cls, tokens: List[str]) -> str:
        if not tokens:
            return ""
        text = " ".join(tokens)
        # Fix spaces before punctuation
        text = re.sub(r"\s+([।,॥\?!;\:\)\]])", r"\1", text)
        text = re.sub(r"([\(\[])\s+", r"\1", text)
        return text
