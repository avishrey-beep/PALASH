"""Pure-Python reimplementation of IndicTransToolkit's IndicProcessor.

WHY THIS EXISTS
---------------
IndicTrans2 is NOT a plain "tokenize -> generate -> detokenize" model. Its
official inference pipeline applies a mandatory pre/post-processing wrapper
(``IndicTransToolkit.IndicProcessor``) that the model was trained against:

  preprocess :  punctuation norm -> numeral folding -> entity masking ->
                indic normalization -> trivial tokenization ->
                transliterate(src_script -> Devanagari) -> prepend lang tags
  generate   :  the model emits a UNIFIED DEVANAGARI representation
  postprocess:  restore entities -> transliterate(Devanagari -> tgt_script) ->
                trivial detokenization

Skipping the postprocess step makes every Indic target look like Devanagari,
which is exactly the false negative this project hit: a control run reported
hin->ben, hin->tam and hin->guj at a 0% target-script hit rate, which cannot be
true of IndicTrans2. The harness was wrong, not the model.

The upstream toolkit ships as Cython and requires an MSVC toolchain that is not
available on this host, so it is reimplemented here in pure Python against the
same reference source (IndicTransToolkit/processor.pyx, main branch). Only
``indic-nlp-library`` (pure Python, its actual worker dependency) is required.

FIDELITY
--------
Ported verbatim from processor.pyx: ``_flores_codes``, the digit translation
table, ``_PUNC_REPLACEMENTS``, ``_URL/_NUMERAL/_EMAIL/_OTHER_PATTERN``,
``_INDIC_FAILURE_CASES``, ``_punc_norm``, ``_wrap_with_placeholders``,
``_normalize``, ``_do_indic_tokenize_and_transliterate``, ``_preprocess``,
``_postprocess``.

Deliberate deviations, each labelled:
  * ``regex`` -> ``re``. The four entity patterns use no ``regex``-only syntax
    (no ``\\p{...}``, no variable-width lookbehind), so ``re`` is equivalent.
    ``_URL_PATTERN``'s ``(?<![\\w/.])`` is fixed-width and accepted by ``re``.
  * The English path (``sacremoses``) is imported lazily. This project's source
    language is Hindi; if ``eng_Latn`` is ever used without sacremoses
    installed, the call raises rather than silently degrading.
  * Placeholder maps are returned explicitly instead of being pushed onto a
    module-level ``Queue``. The queue makes pre/post calls order-coupled and is
    not thread-safe for concurrent requests; returning the map is equivalent
    for a single sentence and safe under concurrency.

KNOWN UPSTREAM LIMITATION (this is a finding, not a bug in this file)
---------------------------------------------------------------------
``_flores_codes["sat_Olck"] == "or"`` (Odia). Santali output is therefore
transliterated into the ODIA script, not Ol Chiki. Separately,
``indic-nlp-library`` has no Ol Chiki script range at all, so a "hi" -> "sat"
transliteration is a silent no-op that returns Devanagari. Consequence: the
sanctioned IndicTrans2 pipeline cannot emit Ol Chiki. See
``OLCK_POSTPROCESS_IS_LOSSY`` below and the ``olck_mode`` argument.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from indicnlp.normalize.indic_normalize import IndicNormalizerFactory
from indicnlp.tokenize import indic_detokenize, indic_tokenize
from indicnlp.transliterate.unicode_transliterate import UnicodeIndicTransliterator

# --------------------------------------------------------------------------
# FLORES tag -> ISO code used by indic-nlp-library. Verbatim from processor.pyx.
# --------------------------------------------------------------------------
FLORES_CODES: Dict[str, str] = {
    "asm_Beng": "as", "awa_Deva": "hi", "ben_Beng": "bn", "bho_Deva": "hi",
    "brx_Deva": "hi", "doi_Deva": "hi", "eng_Latn": "en", "gom_Deva": "kK",
    "gon_Deva": "hi", "guj_Gujr": "gu", "hin_Deva": "hi", "hne_Deva": "hi",
    "kan_Knda": "kn", "kas_Arab": "ur", "kas_Deva": "hi", "kha_Latn": "en",
    "lus_Latn": "en", "mag_Deva": "hi", "mai_Deva": "hi", "mal_Mlym": "ml",
    "mar_Deva": "mr", "mni_Beng": "bn", "mni_Mtei": "hi", "npi_Deva": "ne",
    "ory_Orya": "or", "pan_Guru": "pa", "san_Deva": "hi", "sat_Olck": "or",
    "snd_Arab": "ur", "snd_Deva": "hi", "tam_Taml": "ta", "tel_Telu": "te",
    "urd_Arab": "ur", "unr_Deva": "hi",
}

# Scripts for which the SOURCE side is NOT transliterated to Devanagari.
NO_TRANSLITERATE_SCRIPTS = frozenset({"Arab", "Aran", "Olck", "Mtei", "Latn"})

# Documented consequence of FLORES_CODES["sat_Olck"] == "or"; see module docstring.
OLCK_POSTPROCESS_IS_LOSSY = (
    "sat_Olck postprocessing transliterates to ISO 'or' (Odia). indic-nlp-library "
    "has no Ol Chiki script range, so Ol Chiki cannot be produced by the upstream "
    "pipeline. Raw decoder output is the only place Ol Chiki can appear."
)

# --------------------------------------------------------------------------
# Indic digits -> ASCII. Verbatim from processor.pyx.
# --------------------------------------------------------------------------
_DIGIT_SOURCES = (
    "\u09e6\u0ae6\u0ce6\u0966\u0660\uabf0\u0b66\u0a66\u1c50\u06f0",  # 0
    "\u09e7\u0ae7\u0967\u0ce7\u06f1\uabf1\u0b67\u0a67\u1c51\u0c67",  # 1
    "\u09e8\u0ae8\u0968\u0ce8\u06f2\uabf2\u0b68\u0a68\u1c52\u0c68",  # 2
    "\u09e9\u0ae9\u0969\u0ce9\u06f3\uabf3\u0b69\u0a69\u1c53\u0c69",  # 3
    "\u09ea\u0aea\u096a\u0cea\u06f4\uabf4\u0b6a\u0a6a\u1c54\u0c6a",  # 4
    "\u09eb\u0aeb\u096b\u0ceb\u06f5\uabf5\u0b6b\u0a6b\u1c55\u0c6b",  # 5
    "\u09ec\u0aec\u096c\u0cec\u06f6\uabf6\u0b6c\u0a6c\u1c56\u0c6c",  # 6
    "\u09ed\u0aed\u096d\u0ced\u06f7\uabf7\u0b6d\u0a6d\u1c57\u0c6d",  # 7
    "\u09ee\u0aee\u096e\u0cee\u06f8\uabf8\u0b6e\u0a6e\u1c58\u0c6e",  # 8
    "\u09ef\u0aef\u096f\u0cef\u06f9\uabf9\u0b6f\u0a6f\u1c59\u0c6f",  # 9
)
DIGITS_TRANSLATION_TABLE: Dict[int, str] = {
    ord(ch): str(value)
    for value, chars in enumerate(_DIGIT_SOURCES)
    for ch in chars
}
DIGITS_TRANSLATION_TABLE.update({c: chr(c) for c in range(ord("0"), ord("9") + 1)})

# --------------------------------------------------------------------------
# Punctuation. Verbatim from processor.pyx.
# --------------------------------------------------------------------------
_PUNC_REPLACEMENTS: List[Tuple[re.Pattern, object]] = [
    (re.compile(r"\r"), ""),
    (re.compile(r"\(\s*"), "("),
    (re.compile(r"\s*\)"), ")"),
    (re.compile(r"\s:\s?"), ":"),
    (re.compile(r"\s;\s?"), ";"),
    (re.compile(r"[`´‘‚’]"), "'"),
    (re.compile(r"[„“”«»]"), '"'),
    (re.compile(r"[–—]"), "-"),
    (re.compile(r"\.\.\."), "..."),
    (re.compile(r" %"), "%"),
    (re.compile(r"nº "), "nº "),
    (re.compile(r" ºC"), " ºC"),
    (re.compile(r" [?!;]"), lambda m: m.group(0).strip()),
    (re.compile(r", "), ", "),
]

_MULTISPACE_REGEX = re.compile(r"[ ]{2,}")
_DIGIT_SPACE_PERCENT = re.compile(r"(\d) %")
_DOUBLE_QUOT_PUNC = re.compile(r"\"([,\.]+)")
_DIGIT_NBSP_DIGIT = re.compile(r"(\d) (\d)")
_END_BRACKET_SPACE_PUNC_REGEX = re.compile(r"\) ([\.!:?;,])")

_URL_PATTERN = re.compile(
    r"\b(?<![\w/.])(?:(?:https?|ftp)://)?(?:(?:[\w-]+\.)+(?!\.))(?:[\w/\-?#&=%.]+)+(?!\.\w+)\b"
)
_NUMERAL_PATTERN = re.compile(
    r"(~?\d+\.?\d*\s?%?\s?-?\s?~?\d+\.?\d*\s?%|~?\d+%|"
    r"\d+[-\/.,:']\d+[-\/.,:'+]\d+(?:\.\d+)?|\d+[-\/.:'+]\d+(?:\.\d+)?)"
)
_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}")
_OTHER_PATTERN = re.compile(r"[A-Za-z0-9]*[#|@]\w+")

# Placeholder spellings the model is known to emit instead of "<IDn>".
_INDIC_FAILURE_CASES: List[str] = [
    "آی ڈی ", "ꯑꯥꯏꯗꯤ", "आईडी", "आई . डी . ", "आई . डी .", "आई. डी. ",
    "आई. डी.", "आय. डी. ", "आय. डी.", "आय . डी . ",
    "आय . डी ." "आइ . डी . ",  # noqa: ISC001 - upstream has a missing comma here
    "आइ . डी .", "आइ. डी. ", "आइ. डी.", "ऐटि", "آئی ڈی ", "ᱟᱭᱰᱤ ᱾",
    "आयडी", "ऐडि", "आइडि", "ᱟᱭᱰᱤ",
]


@dataclass
class PreprocessResult:
    """A tagged model input plus the entity map needed to postprocess it."""

    text: str
    placeholder_entity_map: Dict[str, str] = field(default_factory=dict)


class IndicProcessor:
    """Pure-Python port of IndicTransToolkit.IndicProcessor.

    Args:
        inference: when True, mask entities (URLs/emails/numerals/handles)
            behind ``<IDn>`` placeholders and restore them after decoding.
        olck_mode: how to postprocess a ``sat_Olck`` target.
            ``"upstream"`` reproduces the toolkit exactly (transliterates to
            Odia via ISO ``"or"``); ``"raw"`` returns the decoder output
            untransliterated so genuine Ol Chiki survives. Both are wrong in
            different ways -- see ``OLCK_POSTPROCESS_IS_LOSSY``. Defaults to
            ``"upstream"`` so measurements describe the sanctioned pipeline.
    """

    def __init__(self, inference: bool = True, olck_mode: str = "upstream") -> None:
        if olck_mode not in ("upstream", "raw"):
            raise ValueError("olck_mode must be 'upstream' or 'raw'")
        self.inference = inference
        self.olck_mode = olck_mode
        self._xliterator = UnicodeIndicTransliterator()
        self._normalizer_factory = IndicNormalizerFactory()
        self._normalizer_cache: Dict[str, object] = {}
        self._en_tools: Optional[tuple] = None

    # -- English tooling, imported lazily (see module docstring) -----------
    def _english_tools(self):
        if self._en_tools is None:
            from sacremoses import MosesDetokenizer, MosesPunctNormalizer, MosesTokenizer

            self._en_tools = (
                MosesTokenizer(lang="en"),
                MosesPunctNormalizer(),
                MosesDetokenizer(lang="en"),
            )
        return self._en_tools

    def _normalizer(self, iso_code: str):
        if iso_code not in self._normalizer_cache:
            self._normalizer_cache[iso_code] = self._normalizer_factory.get_normalizer(
                iso_code
            )
        return self._normalizer_cache[iso_code]

    # -- punctuation -------------------------------------------------------
    @staticmethod
    def _punc_norm(text: str) -> str:
        for pattern, repl in _PUNC_REPLACEMENTS:
            text = pattern.sub(repl, text)
        text = _MULTISPACE_REGEX.sub(" ", text)
        text = _END_BRACKET_SPACE_PUNC_REGEX.sub(r")\1", text)
        text = _DIGIT_SPACE_PERCENT.sub(r"\1%", text)
        text = _DOUBLE_QUOT_PUNC.sub(r'\1"', text)
        text = _DIGIT_NBSP_DIGIT.sub(r"\1.\2", text)
        return text.strip()

    # -- entity masking ----------------------------------------------------
    @staticmethod
    def _wrap_with_placeholders(text: str) -> Tuple[str, Dict[str, str]]:
        """Replace entities with ``<IDn>`` and build the restoration map.

        The map is intentionally over-populated with many spellings of the same
        placeholder (``< ID1 >``, ``[ID1]``, ``आईडी1`` ...) because the decoder
        frequently mangles or transliterates the marker.
        """
        serial_no = 1
        placeholder_entity_map: Dict[str, str] = {}
        for pattern in (_EMAIL_PATTERN, _URL_PATTERN, _NUMERAL_PATTERN, _OTHER_PATTERN):
            for match in set(pattern.findall(text)):
                if pattern is _URL_PATTERN and len(match.replace(".", "")) < 4:
                    continue
                if pattern is _NUMERAL_PATTERN:
                    stripped = match.replace(" ", "").replace(".", "").replace(":", "")
                    if len(stripped) < 4:
                        continue

                n = serial_no
                for key in (
                    f"<ID{n}>", f"< ID{n} >", f"[ID{n}]", f"[ ID{n} ]",
                    f"[ID {n}]", f"<ID{n}]", f"< ID{n}]", f"<ID{n} ]",
                    f"<id{n}>", f"< id{n} >", f"[id{n}]", f"[ id{n} ]",
                    f"[id {n}]", f"<id{n}]", f"< id{n}]", f"<id{n} ]",
                ):
                    placeholder_entity_map[key] = match
                for case in _INDIC_FAILURE_CASES:
                    for key in (
                        f"<{case}{n}>", f"< {case}{n} >", f"< {case} {n} >",
                        f"<{case} {n}]", f"< {case} {n} ]", f"[{case}{n}]",
                        f"[{case} {n}]", f"[ {case}{n} ]", f"[ {case} {n} ]",
                        f"{case} {n}", f"{case}{n}",
                    ):
                        placeholder_entity_map[key] = match

                text = text.replace(match, f"<ID{n}>")
                serial_no += 1

        text = re.sub(r"\s+", " ", text).replace(">/", ">").replace("]/", "]")
        return text, placeholder_entity_map

    def _normalize(self, text: str) -> Tuple[str, Dict[str, str]]:
        text = text.translate(DIGITS_TRANSLATION_TABLE)
        if self.inference:
            return self._wrap_with_placeholders(text)
        return text, {}

    # -- preprocess --------------------------------------------------------
    def _do_indic_tokenize_and_transliterate(
        self, sentence: str, normalizer, iso_lang: str, transliterate: bool
    ) -> str:
        normed = normalizer.normalize(sentence.strip())
        joined = " ".join(indic_tokenize.trivial_tokenize(normed, iso_lang))
        if transliterate:
            joined = self._xliterator.transliterate(joined, iso_lang, "hi")
            joined = joined.replace(" ् ", "्")
        return joined

    def preprocess(
        self, sent: str, src_lang: str, tgt_lang: Optional[str] = None,
        is_target: bool = False,
    ) -> PreprocessResult:
        """Return the tagged model input for one sentence."""
        iso_lang = FLORES_CODES.get(src_lang, "hi")
        script_part = src_lang.split("_")[1]

        sent = self._punc_norm(sent)
        sent, entity_map = self._normalize(sent)

        do_transliterate = script_part not in NO_TRANSLITERATE_SCRIPTS

        if iso_lang == "en":
            en_tok, en_norm, _ = self._english_tools()
            processed = " ".join(
                en_tok.tokenize(en_norm.normalize(sent.strip()), escape=False)
            )
        else:
            processed = self._do_indic_tokenize_and_transliterate(
                sent, self._normalizer(iso_lang), iso_lang, do_transliterate
            )

        processed = processed.strip()
        if is_target:
            return PreprocessResult(processed, entity_map)
        return PreprocessResult(f"{src_lang} {tgt_lang} {processed}", entity_map)

    def preprocess_batch(
        self, batch: List[str], src_lang: str, tgt_lang: Optional[str] = None,
        is_target: bool = False,
    ) -> List[PreprocessResult]:
        return [self.preprocess(s, src_lang, tgt_lang, is_target) for s in batch]

    # -- postprocess -------------------------------------------------------
    def postprocess(
        self, sent, lang: str = "hin_Deva",
        placeholder_entity_map: Optional[Dict[str, str]] = None,
    ) -> str:
        """Restore entities and transliterate Devanagari output to ``lang``."""
        if isinstance(sent, (tuple, list)):
            sent = sent[0]
        placeholder_entity_map = placeholder_entity_map or {}

        lang_code, script_code = lang.split("_", 1)
        iso_lang = FLORES_CODES.get(lang, "hi")

        if script_code in ("Arab", "Aran"):
            sent = (
                sent.replace(" ؟", "؟")
                .replace(" ۔", "۔")
                .replace(" ،", "،")
                .replace("ٮ۪", "ؠ")
            )
        if lang_code == "ory":
            sent = sent.replace("ଯ଼", "ୟ")

        for k, v in placeholder_entity_map.items():
            sent = sent.replace(k, v)

        if lang == "eng_Latn":
            _, _, en_detok = self._english_tools()
            return en_detok.detokenize(sent.split(" "))

        # Documented deviation: upstream would transliterate Ol Chiki targets
        # into Odia. "raw" skips that so genuine Ol Chiki is not destroyed.
        if script_code == "Olck" and self.olck_mode == "raw":
            return sent.strip()

        xlated = self._xliterator.transliterate(sent, "hi", iso_lang)
        return indic_detokenize.trivial_detokenize(xlated, iso_lang)

    def postprocess_batch(
        self, sents: List[str], lang: str = "hin_Deva",
        placeholder_entity_maps: Optional[List[Dict[str, str]]] = None,
    ) -> List[str]:
        maps = placeholder_entity_maps or [{}] * len(sents)
        return [self.postprocess(s, lang, m) for s, m in zip(sents, maps)]
