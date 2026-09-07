"""Tests for the IndicTrans2 pre/post-processing port and the two harness fixes.

Every test here encodes a defect that actually occurred during Phase 1 and was
caught only by a control experiment, not by inspection. See
`docs/feasibility-phase1.md` corrections 3, 4 and 5.

The processor tests are pure (no model load). The position-table test builds one
small embedding module directly rather than loading the 1.28 GB checkpoint, so
the whole file stays fast.
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from ml.research.probe_nllb_santali import has_char_repetition_loop, is_degenerate
from ml.translation.indictrans2_processor import (
    FLORES_CODES,
    NO_TRANSLITERATE_SCRIPTS,
    IndicProcessor,
)

# Devanagari range, for asserting the model's unified-Devanagari intermediate.
_DEVA = (0x0900, 0x097F)


def _ratio_in(text: str, lo: int, hi: int) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(lo <= ord(c) <= hi for c in letters) / len(letters)


# ---------------------------------------------------------------------------
# Correction 5: intra-word character repetition loops
# ---------------------------------------------------------------------------


def test_char_repetition_loop_catches_real_measured_output():
    """The exact output that slipped through both token-level checks.

    'एम्मोआउआउआउआउआउ' is one whitespace-delimited token, so unigram domination
    and n-gram block detection both scored it as ordinary output -- while it
    also took 20,348 ms to generate.
    """
    assert has_char_repetition_loop("एम्मोआउआउआउआउआउ")
    assert is_degenerate("एम्मोआउआउआउआउआउ")


def test_char_repetition_loop_catches_latin_and_odia_loops():
    # Observed while the position table was zeroed.
    assert is_degenerate("ଗଲ. A. A. A. A. A. A. A. A. A. A. A. A. A. A")


@pytest.mark.parametrize(
    "text",
    [
        # Real measured IndicTrans2 Santali outputs -- must NOT be flagged.
        "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱪᱮᱫ?",
        "ᱥᱟᱱᱟᱢ ᱜᱤᱫᱽᱨᱟᱹ ᱜᱮ ᱵᱤᱨᱫᱟᱹᱜᱟᱲ ᱨᱮᱭ ᱥᱮᱱᱚᱜᱼᱟ ᱾",
        "ᱞᱟᱛᱟᱨ ᱨᱮ ᱚᱞ ᱟᱠᱟᱱ ᱴᱷᱟᱶ ᱠᱚ ᱯᱮᱨᱮᱪ ᱢᱮ ᱾",
        # Long legitimate words must stay under the length gate.
        "विद्यालय",
        "प्रेरणादायक",
        "तिरैप्पटत्तैप्",
    ],
)
def test_char_repetition_loop_no_false_positives(text):
    assert not has_char_repetition_loop(text)


# ---------------------------------------------------------------------------
# Correction 3: the mandatory IndicProcessor wrapper
# ---------------------------------------------------------------------------


def test_preprocess_prepends_both_language_tags():
    ip = IndicProcessor()
    out = ip.preprocess("सभी बच्चे विद्यालय जाते हैं।", "hin_Deva", "ben_Beng").text
    assert out.startswith("hin_Deva ben_Beng ")


def test_preprocess_folds_indic_numerals_to_ascii():
    ip = IndicProcessor()
    out = ip.preprocess("कक्षा ३ में २५ छात्र।", "hin_Deva", "sat_Olck").text
    assert "3" in out and "25" in out
    assert "३" not in out and "२५" not in out


def test_preprocess_masks_entities_and_postprocess_restores_them():
    """Entity round-trip. Emails must survive translation untouched."""
    ip = IndicProcessor(inference=True)
    pre = ip.preprocess("मुझे mail@school.in पर लिखो।", "hin_Deva", "sat_Olck")
    assert "mail@school.in" not in pre.text
    assert "ID1" in pre.text
    # Simulate the decoder returning the placeholder in a mangled spelling.
    assert ip.postprocess("< ID1 > ᱨᱮ ᱚᱞ ᱢᱮ", "sat_Olck", pre.placeholder_entity_map) \
        .startswith("mail@school.in")


def test_preprocess_skips_source_transliteration_for_listed_scripts():
    """Ol Chiki / Arabic / Meitei / Latin sources are not folded to Devanagari."""
    assert "Olck" in NO_TRANSLITERATE_SCRIPTS
    ip = IndicProcessor()
    santali = "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱪᱮᱫ"
    out = ip.preprocess(santali, "sat_Olck", "hin_Deva").text
    assert "ᱟᱢᱟᱜ" in out, "Ol Chiki source must survive preprocessing unchanged"


@pytest.mark.parametrize(
    "lang,lo,hi",
    [
        ("ben_Beng", 0x0980, 0x09FF),
        ("tam_Taml", 0x0B80, 0x0BFF),
        ("guj_Gujr", 0x0A80, 0x0AFF),
        ("ory_Orya", 0x0B00, 0x0B7F),
    ],
)
def test_postprocess_transliterates_devanagari_into_target_script(lang, lo, hi):
    """The step whose absence caused correction 3.

    IndicTrans2 emits a unified Devanagari representation; without this the
    output stays Devanagari and every Indic target looks identical.
    """
    ip = IndicProcessor()
    deva = "सभी बच्चे विद्यालय जाते हैं ।"
    assert _ratio_in(deva, *_DEVA) == 1.0
    out = ip.postprocess(deva, lang)
    assert _ratio_in(out, lo, hi) > 0.9
    assert _ratio_in(out, *_DEVA) == 0.0


def test_sat_olck_upstream_postprocess_yields_odia_not_ol_chiki():
    """Documents the upstream hazard rather than pretending it is fixed.

    FLORES_CODES maps sat_Olck -> 'or', and indic-nlp-library has no Ol Chiki
    range, so Devanagari leaking into a Santali output becomes ODIA silently.
    """
    assert FLORES_CODES["sat_Olck"] == "or"
    ip = IndicProcessor(olck_mode="upstream")
    out = ip.postprocess("सभी बच्चे विद्यालय जाते हैं ।", "sat_Olck")
    assert _ratio_in(out, 0x0B00, 0x0B7F) > 0.9  # Odia
    assert _ratio_in(out, 0x1C50, 0x1C7F) == 0.0  # NOT Ol Chiki


def test_sat_olck_postprocess_preserves_genuine_ol_chiki():
    """Why the hazard above is latent, not fatal: the model emits Ol Chiki
    directly for sat_Olck, and a Devanagari->Odia map is a no-op on it."""
    santali = "ᱥᱟᱱᱟᱢ ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ ᱵᱤᱨᱫᱟᱹᱜᱟᱲ ᱨᱮ ᱛᱟᱦᱮᱸᱱᱟ ।"
    for mode in ("upstream", "raw"):
        out = IndicProcessor(olck_mode=mode).postprocess(santali, "sat_Olck")
        assert _ratio_in(out, 0x1C50, 0x1C7F) == 1.0, mode


def test_olck_mode_rejects_unknown_value():
    with pytest.raises(ValueError):
        IndicProcessor(olck_mode="odia")


# ---------------------------------------------------------------------------
# Correction 4: transformers v5 zero-fills the non-persistent position table
# ---------------------------------------------------------------------------


def test_zeroed_sinusoidal_position_table_is_restored():
    """Regression test for the silent bug that scrambled all output.

    from_pretrained reported 0 missing / 0 unexpected / 0 mismatched keys, so
    nothing surfaced. A zero table gives every position the same vector, which
    makes the encoder a bag of words: fluent but word-scrambled output that
    still passes every script and vocabulary check.
    """
    from ml.research.load_indictrans2 import (
        _install_onnx_stub,
        _load_package,
        _restore_sinusoidal_positions,
    )

    _install_onnx_stub()
    _load_package()
    from indtrans2c.modeling_indictrans import IndicTransSinusoidalPositionalEmbedding

    pe = IndicTransSinusoidalPositionalEmbedding(256, 512, padding_idx=1)
    assert not bool((pe.weights == 0).all()), "fresh module must build its table"

    # Reproduce exactly what v5's meta-device load leaves behind.
    pe.register_buffer("weights", torch.zeros_like(pe.weights), persistent=False)
    assert bool((pe.weights == 0).all())
    assert torch.equal(pe.weights[0], pe.weights[1]), "zeroed table: all positions equal"

    class Wrapper(torch.nn.Module):
        def __init__(self, child):
            super().__init__()
            self.embed_positions = child

    n = _restore_sinusoidal_positions(Wrapper(pe))
    assert n == 1
    assert not bool((pe.weights == 0).all())
    assert not torch.equal(pe.weights[0], pe.weights[1]), "positions must differ"


def test_restore_raises_when_no_position_modules_found():
    """A silent no-op here would reintroduce the scrambling bug."""
    from ml.research.load_indictrans2 import (
        _install_onnx_stub,
        _load_package,
        _restore_sinusoidal_positions,
    )

    _install_onnx_stub()
    _load_package()
    with pytest.raises(RuntimeError, match="no IndicTransSinusoidalPositionalEmbedding"):
        _restore_sinusoidal_positions(torch.nn.Linear(2, 2))
