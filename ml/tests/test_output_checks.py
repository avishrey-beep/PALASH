"""Tests for the speaker-independent output checks in the Phase 1 probe.

These are pure functions, so they run without loading any model. The
`test_measured_*` tests replay the ACTUAL measured NLLB-200 outputs from
`benchmarks/results/phase1_nllb_hin_satBeng.json` and assert the two findings
that were established from them:

  1. The `sat_Beng` tag is mislabelled — the checkpoint emits Ol Chiki.
  2. "sit down" and "stand up" collapse to byte-identical Santali.

Both were initially misread during Phase 1 (the first as "model produces no
target-script output", because only the tag-declared script was measured).
These tests exist so that neither can regress silently.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ml.research.probe_nllb_santali import (
    SCRIPT_RANGES,
    SentenceResult,
    analyse_outputs,
    char_ratio_in_range,
    is_degenerate,
    score_output,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MEASURED_JSON = REPO_ROOT / "benchmarks" / "results" / "phase1_nllb_hin_satBeng.json"

OL_CHIKI_SIT = "ᱡᱟᱱᱟᱢ ᱢᱮ ᱾"  # measured NLLB output for both बैठ जाओ। and खड़े हो जाओ।


def make(source: str, hypothesis: str, tgt="Olck", src="Deva") -> SentenceResult:
    return SentenceResult(
        source=source,
        hypothesis=hypothesis,
        latency_ms=0.0,
        n_src_chars=len(source),
        n_out_chars=len(hypothesis),
        **score_output(hypothesis, source, tgt, src),
    )


# --------------------------------------------------------------------------
# char_ratio_in_range
# --------------------------------------------------------------------------

def test_char_ratio_counts_only_letters():
    # Punctuation and spaces must not dilute the ratio.
    assert char_ratio_in_range("ᱡᱟᱱᱟᱢ ᱢᱮ ᱾", *SCRIPT_RANGES["Olck"]) == 1.0
    assert char_ratio_in_range("बैठ जाओ।", *SCRIPT_RANGES["Deva"]) == 1.0


def test_char_ratio_no_letters_is_zero_not_error():
    assert char_ratio_in_range("123 !?", *SCRIPT_RANGES["Olck"]) == 0.0
    assert char_ratio_in_range("", *SCRIPT_RANGES["Olck"]) == 0.0


def test_char_ratio_mixed_script():
    # The mockup's word-by-word output looked like this: mixed Ol Chiki + Devanagari.
    mixed = "ᱛᱤᱱᱟᱹᱜ आम ᱠᱟᱱᱟ"
    olck = char_ratio_in_range(mixed, *SCRIPT_RANGES["Olck"])
    deva = char_ratio_in_range(mixed, *SCRIPT_RANGES["Deva"])
    assert 0.0 < olck < 1.0
    assert 0.0 < deva < 1.0
    assert olck + deva == pytest.approx(1.0)


# --------------------------------------------------------------------------
# is_degenerate
# --------------------------------------------------------------------------

def test_degenerate_detects_empty_and_whitespace():
    assert is_degenerate("")
    assert is_degenerate("   \n ")


def test_degenerate_detects_repetition_loop():
    """A cycling phrase, which unigram counting alone does NOT catch.

    Real measured round-trip output. Tokens: 10. The most frequent single token
    holds only 3/10, below any sane unigram threshold — but the trigram
    "उदाहरण के लिए" repeats 3x and covers 9/10 of the output.
    """
    assert is_degenerate("सही उदाहरण के लिए उदाहरण के लिए उदाहरण के लिए")


def test_degenerate_detects_single_token_repeated():
    assert is_degenerate("ᱚᱞ ᱚᱞ ᱚᱞ")
    assert is_degenerate("ᱚᱞ ᱚᱞ")


def test_degenerate_allows_normal_output():
    assert not is_degenerate(OL_CHIKI_SIT)
    assert not is_degenerate("अपनी कॉपी में आज की तारीख लिखो।")


def test_degenerate_does_not_flag_long_legitimate_sentence():
    """Guard against over-eager repetition detection.

    A false positive discards a valid translation, which is worse than missing
    a loop. This is a real 18-token classroom sentence with two naturally
    recurring tokens (में, सीखेंगे).
    """
    assert not is_degenerate(
        "आज हम कक्षा दो में जोड़ के बारे में सीखेंगे और बीस तक की संख्याओं को जोड़ना सीखेंगे।"
    )
    assert not is_degenerate("इस पेड़ पर तीन चिड़ियाँ बैठी हुई हैं और दो चिड़ियाँ उड़ रही हैं।")


# --------------------------------------------------------------------------
# score_output — source-copy detection
# --------------------------------------------------------------------------

def test_score_output_flags_verbatim_copy():
    s = make("बैठ जाओ।", "बैठ जाओ।")
    assert s.copied_source
    assert s.dominant_script == "Deva"


def test_score_output_does_not_flag_real_translation():
    s = make("बैठ जाओ।", OL_CHIKI_SIT)
    assert not s.copied_source
    assert s.dominant_script == "Olck"
    assert s.script_ratios["Olck"] == 1.0
    assert s.script_ratios["Deva"] == 0.0


def test_score_output_dominant_is_none_when_no_letters():
    s = make("कितने आम हैं?", "123 ?!")
    assert s.dominant_script is None


# --------------------------------------------------------------------------
# analyse_outputs — mislabelled tag
# --------------------------------------------------------------------------

def test_mislabelled_tag_is_detected():
    """Declared script Beng, actual output Olck => must report the mismatch.

    This is the check whose absence caused a false 'no target-script output'
    reading during Phase 1.
    """
    results = [make("बैठ जाओ।", OL_CHIKI_SIT, tgt="Beng")]
    validity, notes = analyse_outputs(results, tgt_script="Beng")

    assert validity["declared_target_script"] == "Beng"
    assert validity["observed_dominant_script"] == "Olck"
    assert validity["tag_script_mismatch"] is True
    # The declared-script count is 0 but the observed-script count is not.
    assert validity["n_output_in_declared_script_ge_0.9"] == 0
    assert validity["n_output_in_observed_script_ge_0.9"] == 1
    assert any("TAG MISLABELLED" in n for n in notes)


def test_matching_tag_reports_no_mismatch():
    results = [make("बैठ जाओ।", OL_CHIKI_SIT, tgt="Olck")]
    validity, notes = analyse_outputs(results, tgt_script="Olck")
    assert validity["tag_script_mismatch"] is False
    assert validity["n_output_in_declared_script_ge_0.9"] == 1
    assert not any("TAG MISLABELLED" in n for n in notes)


# --------------------------------------------------------------------------
# analyse_outputs — collapse
# --------------------------------------------------------------------------

def test_collapse_detects_identical_outputs_for_distinct_inputs():
    results = [
        make("बैठ जाओ।", OL_CHIKI_SIT),
        make("खड़े हो जाओ।", OL_CHIKI_SIT),
        make("बहुत अच्छा।", "ᱵᱟᱲᱟᱭ ᱠᱟᱛᱮ ᱾"),
    ]
    validity, notes = analyse_outputs(results, tgt_script="Olck")
    c = validity["collapse"]

    assert c["n_distinct_sources"] == 3
    assert c["n_distinct_outputs"] == 2
    assert c["n_collision_groups"] == 1
    assert c["collisions"][0]["n_sources"] == 2
    assert set(c["collisions"][0]["sources"]) == {"बैठ जाओ।", "खड़े हो जाओ।"}
    assert any("OUTPUT COLLAPSE" in n for n in notes)


def test_no_collapse_when_all_outputs_distinct():
    results = [
        make("बैठ जाओ।", "ᱫᱩᱲᱩᱵ ᱢᱮ"),
        make("खड़े हो जाओ।", "ᱛᱮᱸᱜᱚ ᱢᱮ"),
    ]
    validity, notes = analyse_outputs(results, tgt_script="Olck")
    assert validity["collapse"]["n_collision_groups"] == 0
    assert not any("OUTPUT COLLAPSE" in n for n in notes)


def test_collapse_normalises_unicode_before_comparing():
    """NFD vs NFC of the same text must not read as two distinct outputs.

    Uses Bengali U+09CB (ো), which canonically decomposes to U+09C7 U+09BE.
    Devanagari vowel signs deliberately are NOT used here: ै (U+0948) has no
    canonical decomposition, so NFC and NFD are byte-identical and the test
    would prove nothing. Bengali is also the script the NLLB `sat_Beng` tag
    names, making this the relevant case.
    """
    import unicodedata

    composed = "ো"          # BENGALI VOWEL SIGN O
    decomposed = "ো"   # VOWEL SIGN E + VOWEL SIGN AA
    assert composed != decomposed  # genuinely different byte sequences...
    assert unicodedata.normalize("NFC", decomposed) == composed  # ...same content

    results = [make("a", composed, tgt="Beng"), make("b", decomposed, tgt="Beng")]
    validity, _ = analyse_outputs(results, tgt_script="Beng")
    assert validity["collapse"]["n_collision_groups"] == 1
    assert validity["collapse"]["n_distinct_outputs"] == 1


def test_empty_corpus_does_not_crash():
    validity, notes = analyse_outputs([], tgt_script="Olck")
    assert validity["collapse"]["n_distinct_outputs"] == 0
    assert validity["observed_dominant_script"] is None
    assert notes == []


# --------------------------------------------------------------------------
# Replay of the ACTUAL measured NLLB-200 run
# --------------------------------------------------------------------------

@pytest.mark.skipif(
    not MEASURED_JSON.exists(),
    reason="measured probe output not present; run ml/research/probe_nllb_santali.py",
)
class TestMeasuredNllbRun:
    """Assertions against real measured data, not fixtures.

    Only `source` and `hypothesis` are read from the JSON — both are raw model
    I/O. The scores are recomputed here, so these tests validate the analysis
    code against ground truth rather than against a previously stored verdict.
    """

    @staticmethod
    def load() -> list[SentenceResult]:
        data = json.loads(MEASURED_JSON.read_text(encoding="utf-8"))
        return [make(s["source"], s["hypothesis"], tgt="Beng") for s in data["sentences"]]

    def test_measured_output_is_ol_chiki_despite_beng_tag(self):
        validity, _ = analyse_outputs(self.load(), tgt_script="Beng")
        m = validity["mean_letter_ratio_by_script"]
        assert m["Olck"] == pytest.approx(1.0, abs=1e-3)
        assert m["Beng"] == pytest.approx(0.0, abs=1e-3)
        assert m["Deva"] == pytest.approx(0.0, abs=1e-3)
        assert validity["tag_script_mismatch"] is True
        assert validity["observed_dominant_script"] == "Olck"

    def test_measured_no_source_copying_and_no_degeneracy(self):
        validity, _ = analyse_outputs(self.load(), tgt_script="Beng")
        assert validity["n_source_script_copied"] == 0
        assert validity["n_degenerate_or_empty"] == 0

    def test_measured_sit_down_and_stand_up_collapse(self):
        """The decisive speaker-independent quality finding."""
        validity, _ = analyse_outputs(self.load(), tgt_script="Beng")
        c = validity["collapse"]
        assert c["n_distinct_sources"] == 22
        assert c["n_distinct_outputs"] == 21
        assert c["n_collision_groups"] == 1

        collision = c["collisions"][0]
        assert collision["output"] == OL_CHIKI_SIT
        assert set(collision["sources"]) == {"बैठ जाओ।", "खड़े हो जाओ।"}
