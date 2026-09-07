"""Tests for the Ol Chiki -> Devanagari speech bridge.

The expected values below are derived by hand from the Ol Chiki letter names
(each letter is one phoneme) and cross-checked against the 25 human-verified
Hindi->Santali phrases seeded in ``app.db``. They are NOT native-speaker
verified pronunciations -- see ``olchiki.PRONUNCIATION_DISCLAIMER``. What these
tests guarantee is that the mapping is correct, total and deterministic, and
that the output is Devanagari an Android Hindi TTS engine will actually voice.
"""

from __future__ import annotations

import unicodedata

import pytest

from ml.transliteration.olchiki import (
    OLCK_END,
    OLCK_START,
    PRONUNCIATION_DISCLAIMER,
    contains_ol_chiki,
    ol_chiki_to_devanagari,
    pronunciation_form,
)

_DEVA = (0x0900, 0x097F)


def xlit(text: str) -> str:
    """Transliterate. Output is already NFC; this is just a short alias."""
    return ol_chiki_to_devanagari(text)


def nfc(text: str) -> str:
    """Normalise an EXPECTED value.

    Devanagari nukta letters (ड़, ढ़) have both a precomposed codepoint and a
    base+U+093C form. NFC picks the decomposed one because those codepoints are
    composition exclusions. Expected values in this file are normalised so the
    tests assert on pronunciation, not on which form an editor happened to save.
    """
    return unicodedata.normalize("NFC", text)


def _ratio_in(text: str, lo: int, hi: int) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(lo <= ord(c) <= hi for c in letters) / len(letters)


# ---------------------------------------------------------------------------
# Real seeded phrases. These are the exact target_text values in the phrases
# table, so a regression here means classroom audio changes.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "olck,expected,gloss",
    [
        ("ᱫᱩᱲᱩᱵ ᱢᱮ", "दुड़ुब मे", "duṛub me - sit down"),
        ("ᱛᱤᱸᱜᱩᱱ ᱢᱮ", "तिंगुन मे", "tiṅgun me - stand up"),
        ("ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ", "पतब झिज मे", "potob jhij me - open your book"),
        ("ᱩᱞ", "उल", "ul - mango (word-initial vowel)"),
        ("ᱢᱮᱱᱟᱜ", "मेनाग", "menag - there is"),
    ],
)
def test_real_seeded_phrases(olck, expected, gloss):
    assert xlit(olck) == nfc(expected), gloss


def test_gaahlaa_ttuddaag_is_dropped_not_emitted():
    """U+1C79 has no Hindi equivalent. Emitting it unmapped would make the TTS
    engine skip the whole word, which is the failure this module prevents."""
    # ᱛᱤᱱᱟᱹᱜ = tinạg ("how many"), from the seeded phrase ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?
    assert xlit("ᱛᱤᱱᱟᱹᱜ") == nfc("तिनाग")
    assert "ᱹ" not in ol_chiki_to_devanagari("ᱛᱤᱱᱟᱹᱜ")


def test_full_seeded_question_including_punctuation_and_hyphen():
    # ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?  "how many mangoes are there?"
    assert xlit("ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?") == nfc("तिनाग उल मेनाग-आ?")


# ---------------------------------------------------------------------------
# Syllable assembly: the abugida/alphabet mismatch
# ---------------------------------------------------------------------------
def test_consonant_cluster_gets_virama_but_word_final_does_not():
    """ᱜᱤᱫᱽᱨᱟᱹ = gidrā ("child"). The medial d..r cluster needs a virama; a
    word-final consonant must not have one or some engines clip it."""
    assert xlit("ᱜᱤᱫᱽᱨᱟᱹ") == nfc("गिद्रा")
    # ᱵ is word-final here and must stay bare.
    assert xlit("ᱫᱩᱲᱩᱵ") == nfc("दुड़ुब")
    assert not ol_chiki_to_devanagari("ᱫᱩᱲᱩᱵ").endswith("्")


def test_word_initial_vowel_uses_independent_form_not_matra():
    assert xlit("ᱩᱞ") == nfc("उल")      # उ, not ु
    assert xlit("ᱟᱢ") == nfc("आम")
    assert xlit("ᱮᱱ") == nfc("एन")


def test_la_vowel_maps_to_devanagari_inherent_vowel():
    """ᱚ LA after a consonant is the inherent vowel, so no matra is emitted."""
    assert xlit("ᱯᱚᱛᱚᱵ") == nfc("पतब")
    assert xlit("ᱚᱞ") == nfc("अल")  # word-initial -> अ


def test_aspiration_modifies_preceding_consonant_in_place():
    """ᱷ OH is a modifier, not a standalone ह."""
    assert xlit("ᱡᱷ") == nfc("झ")   # ज + ᱷ -> झ
    assert xlit("ᱠᱷ") == nfc("ख")
    assert xlit("ᱛᱷ") == nfc("थ")
    assert xlit("ᱵᱷ") == nfc("भ")
    assert xlit("ᱲᱷ") == nfc("ढ़")


def test_stray_aspiration_with_no_preceding_consonant_becomes_ha():
    assert xlit("ᱷᱟ") == nfc("हा")


def test_nasalisation_becomes_anusvara():
    assert xlit("ᱛᱤᱸᱜᱩᱱ") == nfc("तिंगुन")
    assert "ं" in ol_chiki_to_devanagari("ᱛᱤᱸ")


def test_nasal_on_bare_consonant_surfaces_the_consonant_first():
    """An anusvara needs a syllable to attach to; a pending bare consonant must
    be emitted before it, or the mark would lead the token."""
    out = ol_chiki_to_devanagari("ᱢᱸ")
    assert out == "मं"
    assert not out.startswith("ं")


def test_mucaad_punctuation_maps_to_danda():
    assert xlit("ᱫᱩᱲᱩᱵ ᱢᱮ ᱾") == nfc("दुड़ुब मे ।")
    assert xlit("᱿") == nfc("॥")


def test_ol_chiki_digits_fold_to_ascii():
    assert xlit("᱕") == nfc("5")
    assert xlit("᱒᱕") == nfc("25")


# ---------------------------------------------------------------------------
# Totality and safety
# ---------------------------------------------------------------------------
def test_every_codepoint_in_the_block_is_handled():
    """A gap here means real Santali text reaches the TTS engine with an
    unmappable codepoint and is silently skipped."""
    unhandled = []
    for cp in range(OLCK_START, OLCK_END + 1):
        ch = chr(cp)
        out = ol_chiki_to_devanagari(ch)
        if any(OLCK_START <= ord(c) <= OLCK_END for c in out):
            unhandled.append(f"U+{cp:04X}")
    assert not unhandled, f"Ol Chiki codepoints passed through unmapped: {unhandled}"


def test_output_contains_no_ol_chiki_for_real_sentence():
    santali = "ᱥᱟᱱᱟᱢ ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ ᱵᱤᱨᱫᱟᱹᱜᱟᱲ ᱨᱮ ᱛᱟᱦᱮᱸᱱᱟ ᱾"
    out = ol_chiki_to_devanagari(santali)
    assert not contains_ol_chiki(out)
    assert _ratio_in(out, *_DEVA) == 1.0


def test_non_ol_chiki_input_passes_through_untouched():
    """Mixed-script and pure-Hindi strings must be safe to pass through."""
    for text in ("बैठ जाओ।", "hello world", "कक्षा 3", ""):
        assert ol_chiki_to_devanagari(text) == text


def test_transliteration_is_deterministic():
    santali = "ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?"
    assert len({ol_chiki_to_devanagari(santali) for _ in range(20)}) == 1


def test_idempotent_on_already_converted_text():
    once = ol_chiki_to_devanagari("ᱫᱩᱲᱩᱵ ᱢᱮ")
    assert ol_chiki_to_devanagari(once) == once


# ---------------------------------------------------------------------------
# Detection + the honest-labelling payload
# ---------------------------------------------------------------------------
def test_contains_ol_chiki_detection():
    assert contains_ol_chiki("ᱫᱩᱲᱩᱵ ᱢᱮ")
    assert contains_ol_chiki("mixed ᱢᱮ text")
    assert not contains_ol_chiki("बैठ जाओ।")
    assert not contains_ol_chiki("")


def test_pronunciation_form_labels_santali_as_unverified():
    """§52/§72: the payload must never imply the pronunciation is correct."""
    p = pronunciation_form("ᱫᱩᱲᱩᱵ ᱢᱮ")
    assert p["speech_text"] == nfc("दुड़ुब मे")
    assert p["transliterated"] is True
    assert p["script_from"] == "Olck" and p["script_to"] == "Deva"
    assert p["disclaimer"] == PRONUNCIATION_DISCLAIMER
    assert p["verified_by_native_speaker"] is False


def test_pronunciation_form_adds_no_disclaimer_for_hindi():
    p = pronunciation_form("बैठ जाओ।")
    assert p["speech_text"] == nfc("बैठ जाओ।")
    assert p["transliterated"] is False
    assert p["disclaimer"] is None
