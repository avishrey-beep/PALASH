"""Real IndicTrans2-320M inference for Tier 3 of the layered translation engine.

WHY THIS EXISTS
---------------
``model_wrapper.py`` previously returned ``f"[ONNX Translated] {text}"`` when a
model was "loaded" and, otherwise, a word-by-word substitution over 25
hardcoded morphemes -- exactly the mechanism §46 forbids as a primary
translation strategy. Meanwhile a validated 1.3 GB IndicTrans2-320M checkpoint
sat unused in ``storage/models/indictrans2-320m``. This module wires it in.

MODEL PROVENANCE (§60)
----------------------
  model      : ai4bharat/indictrans2-indic-indic-dist-320M
  licence    : MIT (permits commercial use, modification, redistribution)
  local path : storage/models/indictrans2-320m  (1.28 GB, fp32)
  attribution: AI4Bharat, IIT Madras. "IndicTrans2: High-Quality and
               Accessible Machine Translation Models for all 22 Scheduled
               Indian Languages" (Gala et al., TMLR 2023).
  note       : the model card documents this checkpoint was distilled/stitched
               from Indic-En + En-Indic 200M, so Indic->Indic pivots through an
               English representation internally.

MEASURED CAPABILITY, Phase 1 (see docs/feasibility-phase1.md)
-------------------------------------------------------------
  hin_Deva -> sat_Olck : WORKS. Emits Ol Chiki directly (ratio 0.986 over 22
      classroom sentences), 0/22 degenerate, 22 distinct inputs -> 22 distinct
      outputs. p50/p90/p95 = 1158/2214/2666 ms on x86-64 CPU fp32.
  hin_Deva -> unr_Deva : tag present (id 121515) and output is fluent
      Devanagari, but whether it is Mundari or Hindi is NOT MEASURED. Exposed,
      flagged unverified.
  hoc (Ho)             : NO language tag exists in the SRC vocabulary.
      Genuinely unsupported; raises rather than silently substituting Hindi.

TWO LOAD-TIME HAZARDS, both handled by load_indictrans2.py
----------------------------------------------------------
  1. transformers v5 materialises modules on the meta device and zero-fills
     every tensor absent from the checkpoint. The sinusoidal position table is
     registered ``persistent=False``, so it is absent by design and gets
     zeroed -- silently, with 0 missing/unexpected/mismatched keys reported. A
     zero table makes the encoder a bag of words: fluent, word-scrambled
     output that passes every script and vocabulary check.
     ``_restore_sinusoidal_positions`` rebuilds it; ``_assert_healthy`` below
     refuses to serve if it is still degenerate.
  2. ``IndicProcessor`` pre/post-processing is mandatory, not optional. The
     model consumes ``"<src_tag> <tgt_tag> <text>"`` and emits a unified
     Devanagari representation for most targets. Skipping postprocess makes
     every Indic target look like Devanagari.

KNOWN OPEN ISSUE
----------------
``use_cache=False`` is a workaround, not a fix: transformers v5 passes an
``EncoderDecoderCache`` while the checkpoint's vendored modeling code indexes
``past_key_values[0][0].shape[2]``. Disabling the KV cache makes generation
recompute the full prefix each step, so the latency figures above are a
pessimistic bound. This must be resolved before quoting production latency.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

MODEL_ID = "ai4bharat/indictrans2-indic-indic-dist-320M"
MODEL_LICENSE = "MIT"
MODEL_REVISION = "local-snapshot"

# Backend language codes (Language.code / SUPPORTED_LANGUAGES) -> FLORES tags
# used inline by the model. Verified against tokenizer.src_encoder in Phase 1.
FLORES_TAGS: Dict[str, str] = {
    "hin": "hin_Deva",   # id 8
    "sat": "sat_Olck",   # id 29925  -- MEASURED working
    "unr": "unr_Deva",   # id 121515 -- present but adequacy NOT MEASURED
}

# Languages the backend advertises but this model genuinely cannot translate.
# §61: do not claim support because a config file lists a language.
UNSUPPORTED_LANGUAGES: Dict[str, str] = {
    "hoc": (
        "IndicTrans2 has no 'hoc' (Ho) language tag in its source vocabulary. "
        "Translating Ho would require substituting a different language, which "
        "would silently produce wrong text."
    ),
}

# Adequacy status per target, surfaced to clients so the UI can label output.
ADEQUACY: Dict[str, str] = {
    "sat": "MEASURED",
    "unr": "NOT_MEASURED",
    "hin": "MEASURED",
}

_DEFAULT_MAX_NEW_TOKENS = 96
_DEFAULT_NUM_BEAMS = 4


class UnsupportedLanguagePair(ValueError):
    """Raised when the requested pair cannot be served honestly."""

    def __init__(self, src_lang: str, tgt_lang: str, reason: str) -> None:
        super().__init__(reason)
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.reason = reason


@dataclass
class TranslationOutput:
    """One neural translation plus the metadata needed to report it honestly."""

    target_text: str
    src_tag: str
    tgt_tag: str
    inference_ms: float
    num_beams: int
    adequacy: str
    truncated: bool


def model_dir() -> str:
    """Resolve the checkpoint directory, overridable for deployment."""
    env = os.environ.get("INDICTRANS2_MODEL_DIR")
    if env:
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(
        os.path.join(here, "..", "..", "storage", "models", "indictrans2-320m")
    )


def is_model_present() -> bool:
    """True if the checkpoint looks complete enough to attempt a load.

    Checked before loading so a missing model degrades to Tier 1/2 with a clear
    reason instead of raising deep inside ``from_pretrained``.
    """
    d = model_dir()
    required = (
        "config.json", "dict.SRC.json", "dict.TGT.json",
        "model.SRC", "model.TGT",
    )
    if not os.path.isdir(d):
        return False
    if not all(os.path.exists(os.path.join(d, f)) for f in required):
        return False
    return any(
        f.endswith((".safetensors", ".bin")) for f in os.listdir(d)
    )


class IndicTrans2Runtime:
    """Process-wide lazily-loaded IndicTrans2 singleton.

    ``LayeredTranslationEngine`` is constructed per request by five different
    services, so the model cannot live on the engine instance: that would load
    1.3 GB of weights on every call. Access it only through ``get_runtime()``.

    Inference is serialised behind a lock. ``model.generate`` is not documented
    thread-safe on a shared module, and FastAPI runs sync endpoints in a
    threadpool. Serialising is also the right call for CPU inference, where
    concurrent generation would thrash rather than parallelise.
    """

    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._processor = None
        self._load_lock = threading.Lock()
        self._infer_lock = threading.Lock()
        self._load_error: Optional[str] = None
        self._load_seconds: Optional[float] = None

    # -- lifecycle ---------------------------------------------------------
    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def _assert_healthy(self, model) -> None:
        """Refuse to serve a model whose position table was zeroed.

        This is the defect that voided an entire measurement run while
        reporting no loading errors at all. Cheap to check, catastrophic to
        miss, so it is asserted on every load rather than trusted.
        """
        import torch

        pe = model.model.encoder.embed_positions.weights
        if bool((pe == 0).all()):
            raise RuntimeError(
                "IndicTrans2 sinusoidal position table is all zero after load; "
                "encoder would behave as a bag of words and emit fluent but "
                "word-scrambled text. Refusing to serve."
            )
        if bool(torch.isnan(pe).any()):
            raise RuntimeError("IndicTrans2 position table contains NaN.")

    def load(self) -> None:
        """Load weights. Idempotent, safe under concurrent first requests."""
        if self._model is not None or self._load_error is not None:
            return
        with self._load_lock:
            if self._model is not None or self._load_error is not None:
                return
            try:
                if not is_model_present():
                    raise FileNotFoundError(
                        f"IndicTrans2 checkpoint not found at {model_dir()}. "
                        "Set INDICTRANS2_MODEL_DIR or install the model."
                    )
                t0 = time.perf_counter()
                # Imported here, not at module scope: importing torch and
                # loading 1.3 GB must not happen just because a module that
                # touches translation was imported.
                from ml.research.load_indictrans2 import load_model_and_tokenizer
                from ml.translation.indictrans2_processor import IndicProcessor

                model, tokenizer, _cfg = load_model_and_tokenizer()
                self._assert_healthy(model)
                model.eval()

                # olck_mode="raw" is required. The upstream processor maps
                # sat_Olck -> ISO "or", so its postprocess step would convert
                # genuine Ol Chiki output into Odia. See
                # indictrans2_processor.OLCK_POSTPROCESS_IS_LOSSY.
                self._processor = IndicProcessor(inference=True, olck_mode="raw")
                self._tokenizer = tokenizer
                self._model = model
                self._load_seconds = time.perf_counter() - t0
                logger.info(
                    "IndicTrans2 loaded in %.2fs from %s",
                    self._load_seconds, model_dir(),
                )
            except Exception as exc:  # noqa: BLE001 - degrade, do not crash
                self._load_error = f"{type(exc).__name__}: {exc}"
                logger.error("IndicTrans2 load failed: %s", self._load_error)

    # -- inference ---------------------------------------------------------
    @staticmethod
    def resolve_tags(src_lang: str, tgt_lang: str) -> tuple[str, str]:
        """Map backend language codes to FLORES tags, or refuse.

        Raises ``UnsupportedLanguagePair`` rather than falling back to a
        different language, which is what §61 forbids.
        """
        for code in (src_lang, tgt_lang):
            if code in UNSUPPORTED_LANGUAGES:
                raise UnsupportedLanguagePair(
                    src_lang, tgt_lang, UNSUPPORTED_LANGUAGES[code]
                )
            if code not in FLORES_TAGS:
                raise UnsupportedLanguagePair(
                    src_lang, tgt_lang,
                    f"No IndicTrans2 language tag is mapped for '{code}'. "
                    f"Supported: {sorted(FLORES_TAGS)}.",
                )
        if src_lang == tgt_lang:
            raise UnsupportedLanguagePair(
                src_lang, tgt_lang,
                "Source and target language are the same.",
            )
        return FLORES_TAGS[src_lang], FLORES_TAGS[tgt_lang]

    def translate(
        self,
        text: str,
        src_lang: str = "hin",
        tgt_lang: str = "sat",
        num_beams: int = _DEFAULT_NUM_BEAMS,
        max_new_tokens: int = _DEFAULT_MAX_NEW_TOKENS,
    ) -> TranslationOutput:
        """Translate one sentence. Raises if the model is unavailable."""
        src_tag, tgt_tag = self.resolve_tags(src_lang, tgt_lang)

        self.load()
        if self._model is None:
            raise RuntimeError(
                f"IndicTrans2 is unavailable: {self._load_error}"
            )

        import torch

        # Whole-sentence context, per §46. The pre/postprocess pair is
        # mandatory; see the module docstring.
        pre = self._processor.preprocess(text, src_tag, tgt_tag)
        enc = self._tokenizer(pre.text, return_tensors="pt")

        t0 = time.perf_counter()
        with self._infer_lock:
            with torch.inference_mode():
                out = self._model.generate(
                    **enc,
                    num_beams=num_beams,
                    max_new_tokens=max_new_tokens,
                    early_stopping=True,
                    # See KNOWN OPEN ISSUE in the module docstring.
                    use_cache=False,
                )
        inference_ms = (time.perf_counter() - t0) * 1000.0

        raw = self._tokenizer.decode(out[0], skip_special_tokens=True)
        target_text = self._processor.postprocess(
            raw, tgt_tag, pre.placeholder_entity_map
        )

        return TranslationOutput(
            target_text=target_text.strip(),
            src_tag=src_tag,
            tgt_tag=tgt_tag,
            inference_ms=round(inference_ms, 2),
            num_beams=num_beams,
            adequacy=ADEQUACY.get(tgt_lang, "NOT_MEASURED"),
            # generate() stops at max_new_tokens without signalling; a hypothesis
            # at the cap was probably cut off.
            truncated=int(out[0].shape[-1]) >= max_new_tokens,
        )

    def info(self) -> Dict[str, Any]:
        """Diagnostics for the models/health endpoints. Never fabricated."""
        return {
            "model_id": MODEL_ID,
            "license": MODEL_LICENSE,
            "revision": MODEL_REVISION,
            "model_dir": model_dir(),
            "present_on_disk": is_model_present(),
            "loaded": self.is_loaded,
            "load_seconds": (
                round(self._load_seconds, 2) if self._load_seconds else None
            ),
            "load_error": self._load_error,
            "supported_targets": sorted(FLORES_TAGS),
            "unsupported": UNSUPPORTED_LANGUAGES,
            "adequacy": ADEQUACY,
            "kv_cache_enabled": False,
            "kv_cache_note": (
                "use_cache=False workaround for a transformers v5 "
                "EncoderDecoderCache incompatibility; latency is a pessimistic "
                "bound."
            ),
        }


_runtime: Optional[IndicTrans2Runtime] = None
_runtime_lock = threading.Lock()


def get_runtime() -> IndicTrans2Runtime:
    """The process-wide runtime. Does not load weights on its own."""
    global _runtime
    if _runtime is None:
        with _runtime_lock:
            if _runtime is None:
                _runtime = IndicTrans2Runtime()
    return _runtime


def warmup() -> Dict[str, Any]:
    """Force the load now so the first real request is not the one that waits.

    Loading is ~10 s and ~1.4 GB peak RSS (MEASURED, x86-64 CPU fp32), so
    without this the first classroom translation pays that cost.
    """
    rt = get_runtime()
    rt.load()
    return rt.info()
