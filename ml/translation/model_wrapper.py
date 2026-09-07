"""Tier 3 of the layered translation engine: real neural machine translation.

WHAT CHANGED AND WHY
--------------------
This module previously reported success while translating nothing. With a model
"loaded" it returned ``f"[ONNX Translated] {text}"``; otherwise it substituted
tokens one at a time from a 25-entry hardcoded Hindi->Santali morpheme table and
reported ``0.50 + 0.45 * (matched / total)`` as a confidence score. That is a
mockup on three counts: the output was not a translation, word-by-word
substitution is the mechanism §46 rules out as a primary strategy, and a
coverage ratio presented as a probability is what §52 forbids.

It now delegates to the validated IndicTrans2-320M checkpoint via
``indictrans2_runtime``. The returned dict keeps its original keys so
``engine.py`` and the five services that call it are unaffected.

CONFIDENCE IS NOW ``None`` (§52)
-------------------------------
No calibrated quality estimator exists for this model on this language pair, so
none is reported. ``confidence`` stays in the payload for schema compatibility
but is ``None``, with ``confidence_basis`` explaining why. Downstream code must
treat ``None`` as "unknown", not as zero -- ``engine.py`` does.

THE GLOSSARY IS NO LONGER APPLIED TOKEN-WISE
--------------------------------------------
``matched_terms`` is still accepted and still returned for display, so teachers
can see which curriculum terms occur in the sentence. It is no longer spliced
into the output: overwriting words inside fluent neural output degrades it.
Enforcing terminology properly needs constrained decoding, which is not
implemented -- so this reports rather than claims.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ml.preprocessing.normalizer import TextNormalizer
from ml.translation.indictrans2_runtime import (
    MODEL_ID,
    MODEL_LICENSE,
    UnsupportedLanguagePair,
    get_runtime,
)

logger = logging.getLogger(__name__)

# Reported instead of a number, so no consumer can mistake a heuristic for a
# probability. See the module docstring.
CONFIDENCE_BASIS_UNCALIBRATED = (
    "No calibrated quality estimator is available for this model and language "
    "pair. No confidence score is reported."
)


class TranslationModelWrapper:
    """Tier 3 neural MT. Thin adapter over the shared IndicTrans2 runtime.

    Cheap to construct: holds no weights. The model is a process-wide singleton
    in ``indictrans2_runtime``, because ``LayeredTranslationEngine`` -- and
    therefore this class -- is instantiated per request by five services.
    """

    def __init__(self, model_path: Optional[str] = None, framework: str = "PYTORCH"):
        # model_path/framework are retained for call-site compatibility.
        # The checkpoint location is resolved by the runtime (env-overridable
        # via INDICTRANS2_MODEL_DIR).
        self.model_path = model_path
        self.framework = framework
        self._runtime = get_runtime()

    def is_available(self) -> bool:
        """True if a real translation can be produced right now.

        Reflects actual load state, so a missing or broken checkpoint reports
        unavailable instead of silently degrading to fabricated output.
        """
        self._runtime.load()
        return self._runtime.is_loaded

    def info(self) -> Dict[str, Any]:
        return self._runtime.info()

    def translate(
        self,
        text: str,
        src_lang: str = "hin",
        tgt_lang: str = "sat",
        matched_terms: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Translate a full sentence with the neural model.

        Never raises: on any failure it returns ``target_text=""`` with
        ``tier="unavailable"`` and a machine-readable ``error``. Callers must
        surface that as "translation unavailable" -- returning the input text,
        or a partially substituted version of it, would look like a successful
        translation to a teacher who cannot read the target script.
        """
        norm_text = TextNormalizer.normalize(text, src_lang)

        base: Dict[str, Any] = {
            "source_text": norm_text,
            "confidence": None,
            "confidence_basis": CONFIDENCE_BASIS_UNCALIBRATED,
            "model_id": MODEL_ID,
            "model_license": MODEL_LICENSE,
            "framework": "PYTORCH",
            # Retained for display only; not spliced into the output.
            "matched_glossary": matched_terms or [],
        }

        if not norm_text:
            return {**base, "target_text": "", "tier": "empty", "error": None}

        try:
            out = self._runtime.translate(norm_text, src_lang, tgt_lang)
        except UnsupportedLanguagePair as exc:
            # §61: an unsupported pair is reported, never substituted.
            return {
                **base,
                "target_text": "",
                "tier": "unsupported_language_pair",
                "error": "UNSUPPORTED_LANGUAGE_PAIR",
                "error_detail": exc.reason,
                "src_lang": exc.src_lang,
                "tgt_lang": exc.tgt_lang,
            }
        except Exception as exc:  # noqa: BLE001 - must not 500 the request
            logger.exception("Tier 3 neural translation failed")
            return {
                **base,
                "target_text": "",
                "tier": "unavailable",
                "error": "MODEL_UNAVAILABLE",
                "error_detail": f"{type(exc).__name__}: {exc}",
            }

        return {
            **base,
            "target_text": out.target_text,
            "tier": "neural_indictrans2",
            "error": None,
            "src_tag": out.src_tag,
            "tgt_tag": out.tgt_tag,
            "inference_ms": out.inference_ms,
            "num_beams": out.num_beams,
            # MEASURED vs NOT_MEASURED per target language, so the UI can flag
            # Mundari output as unverified rather than implying parity with
            # Santali.
            "adequacy": out.adequacy,
            "truncated": out.truncated,
        }
