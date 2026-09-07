"""Layered translation orchestration: Tier 1 cache -> Tier 2 memory -> Tier 3 neural.

TIER ORDER (§62)
----------------
  Tier 1  exact phrase cache      human-verified, instant, offline-capable
  Tier 2  translation memory      fuzzy match above 0.85 string similarity
  Tier 3  IndicTrans2-320M        real neural MT, whole-sentence context (§46)

CONFIDENCE REPORTING (§52)
--------------------------
Each tier's number means something different, so each is labelled with its
basis rather than all three being flattened into one "confidence" field:

  Tier 1  HUMAN_VERIFIED      a reviewer approved this exact pair
  Tier 2  STRING_SIMILARITY   character overlap with a verified source
                              sentence. Measures how alike the INPUTS are, not
                              the probability that the output is correct.
  Tier 3  NOT_CALIBRATED      no quality estimator exists; ``confidence`` is
                              None and ``confidence_level`` is "UNCALIBRATED".

``confidence`` may therefore be ``None``. Consumers must treat that as unknown,
never as zero.
"""

import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ml.preprocessing.normalizer import TextNormalizer
from ml.translation.cache import PhraseCacheEngine
from ml.translation.glossary import GlossaryEngine
from ml.translation.memory import TranslationMemoryEngine
from ml.translation.model_wrapper import TranslationModelWrapper
from ml.transliteration.olchiki import contains_ol_chiki, ol_chiki_to_devanagari

# Target languages written in Ol Chiki, which no Android TTS voice can speak.
# See ml/transliteration/olchiki.py for why a Devanagari form is attached.
_OL_CHIKI_LANGS = frozenset({"sat"})

CONFIDENCE_BASIS = {
    "HUMAN_VERIFIED": "A language reviewer approved this exact source/target pair.",
    "STRING_SIMILARITY": (
        "Character-level similarity between the input and a verified source "
        "sentence. Measures input resemblance, not output correctness."
    ),
    "NOT_CALIBRATED": (
        "No calibrated quality estimator is available for this model and "
        "language pair. No confidence score is reported."
    ),
}


class LayeredTranslationEngine:
    """Orchestrates the tiered fallback for classroom translation.

    Cheap to construct -- the neural weights live in a process-wide singleton
    (``ml.translation.indictrans2_runtime``), not on this object, because five
    services build one of these per request.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.cache = PhraseCacheEngine(db)
        self.memory = TranslationMemoryEngine(db, similarity_threshold=0.75)
        self.glossary = GlossaryEngine(db)
        self.model = TranslationModelWrapper()

    @staticmethod
    def _attach_pronunciation(payload: Dict[str, Any], tgt_lang: str) -> Dict[str, Any]:
        """Add a speakable Devanagari form for Ol Chiki output.

        An Android Hindi TTS engine skips Ol Chiki codepoints silently and
        produces no audio, so the device needs a transliterated form to voice.
        It is explicitly marked approximate and not native-verified: the audio
        is Santali words spoken with Hindi phonetics.
        """
        target = payload.get("target_text") or ""
        if tgt_lang in _OL_CHIKI_LANGS and contains_ol_chiki(target):
            payload["pronunciation_deva"] = ol_chiki_to_devanagari(target)
            payload["pronunciation_is_approximate"] = True
            payload["pronunciation_verified_by_native_speaker"] = False
        else:
            payload["pronunciation_deva"] = None
            payload["pronunciation_is_approximate"] = False
            payload["pronunciation_verified_by_native_speaker"] = False
        return payload

    def translate(
        self,
        text: str,
        src_lang: str = "hin",
        tgt_lang: str = "sat",
        context_topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        # Step 1: Normalization
        norm_text = TextNormalizer.normalize(text, src_lang)
        if not norm_text:
            return self._attach_pronunciation(
                {
                    "source_text": text,
                    "target_text": "",
                    "confidence": None,
                    "confidence_level": "UNCALIBRATED",
                    "confidence_basis": "Empty input after normalization.",
                    "tier": "empty",
                    "latency_ms": 0.0,
                    "verification_status": "unverified",
                    "matched_glossary": [],
                    "error": None,
                },
                tgt_lang,
            )

        # Step 2: Tier 1 exact phrase cache lookup
        cache_hit = self.cache.lookup(norm_text, src_lang, tgt_lang)
        if cache_hit:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return self._attach_pronunciation(
                {
                    "source_text": norm_text,
                    "target_text": cache_hit["target_text"],
                    "confidence": cache_hit["confidence"],
                    "confidence_level": "HIGH",
                    "confidence_basis": CONFIDENCE_BASIS["HUMAN_VERIFIED"],
                    "tier": cache_hit["tier"],
                    "latency_ms": round(latency_ms, 2),
                    "audio_asset_path": cache_hit.get("audio_asset_path"),
                    "verification_status": cache_hit.get(
                        "verification_status", "human_verified"
                    ),
                    "matched_glossary": [],
                    "error": None,
                },
                tgt_lang,
            )

        # Step 3: Tier 2 translation memory retrieval
        tm_hit = self.memory.find_best_match(norm_text, src_lang, tgt_lang)
        if tm_hit and tm_hit["similarity_score"] >= 0.85:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return self._attach_pronunciation(
                {
                    "source_text": norm_text,
                    "target_text": tm_hit["target_text"],
                    "confidence": tm_hit["confidence"],
                    "confidence_level": "MEDIUM",
                    "confidence_basis": CONFIDENCE_BASIS["STRING_SIMILARITY"],
                    "tier": tm_hit["tier"],
                    "similarity_score": tm_hit["similarity_score"],
                    "latency_ms": round(latency_ms, 2),
                    "verification_status": tm_hit["verification_status"],
                    "matched_glossary": [],
                    "error": None,
                },
                tgt_lang,
            )

        # Step 4: Terminology matching. Reported for the teacher's benefit, not
        # spliced into the neural output -- see model_wrapper's docstring.
        matched_terms = self.glossary.find_matching_terms(norm_text, tgt_lang)

        # Step 5: Tier 3 neural inference
        model_result = self.model.translate(norm_text, src_lang, tgt_lang, matched_terms)
        target_text = model_result["target_text"]

        # Step 6: Punctuation preservation. Only meaningful when something was
        # actually translated; appending "?" to an empty failure payload would
        # dress a failure up as output. The model emits its own sentence-final
        # mark -- Ol Chiki MUCAAD (᱾/᱿) for sat_Olck, danda for Devanagari --
        # so we must recognise those before appending, or we double-punctuate.
        _SENT_FINAL = ("?", "।", ".", "᱾", "᱿")  # ? । . ᱾ ᱿
        if target_text:
            if "?" in norm_text and not target_text.rstrip().endswith(_SENT_FINAL):
                target_text += "?"
            elif "।" in norm_text and not target_text.rstrip().endswith(_SENT_FINAL):
                target_text += "।"

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # §52: no calibrated estimator exists for Tier 3, so no score is
        # invented. None means unknown, not zero.
        conf = model_result.get("confidence")
        if conf is None:
            conf_level = "UNCALIBRATED"
        elif conf >= 0.85:
            conf_level = "HIGH"
        elif conf >= 0.60:
            conf_level = "MEDIUM"
        else:
            conf_level = "LOW"

        failed = bool(model_result.get("error")) or not target_text
        payload = {
            "source_text": norm_text,
            "target_text": target_text,
            "confidence": conf,
            "confidence_level": conf_level,
            "confidence_basis": model_result.get(
                "confidence_basis", CONFIDENCE_BASIS["NOT_CALIBRATED"]
            ),
            "tier": model_result["tier"],
            "latency_ms": round(latency_ms, 2),
            "verification_status": "unavailable" if failed else "machine_generated",
            "matched_glossary": matched_terms,
            "model_id": model_result.get("model_id"),
            "error": model_result.get("error"),
            "error_detail": model_result.get("error_detail"),
            # MEASURED for Santali, NOT_MEASURED for Mundari (§61).
            "adequacy": model_result.get("adequacy"),
            "truncated": model_result.get("truncated"),
            "inference_ms": model_result.get("inference_ms"),
        }
        return self._attach_pronunciation(payload, tgt_lang)
