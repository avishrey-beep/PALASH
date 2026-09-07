"""Control experiment: is the IndicTrans2 harness correct?

The classroom-corpus probe showed hin_Deva -> sat_Olck mostly NOT emitting Ol
Chiki. Two competing explanations:

  (A) the harness is wrong (bad input format / decode path / tag handling), or
  (B) the harness is right and this checkpoint's sat_Olck is genuinely weak.

This script distinguishes them. It sends the SAME sentences through the SAME
code path to well-resourced targets (ben_Beng, tam_Taml, guj_Gujr, mar_Deva)
whose scripts are unambiguous. If those land in the right script at a high
rate, the harness is validated and (B) holds for Santali.

Prints a per-target hit rate: fraction of outputs whose dominant script is the
script named in the target tag.

RUN 1 (no IndicProcessor) returned ben 0/6, tam 0/6, guj 0/6 -- impossible for
IndicTrans2, so explanation (A) held: the harness was missing the mandatory
IndicProcessor pre/post-processing. IndicTrans2 emits a UNIFIED DEVANAGARI
representation that postprocess_batch transliterates into the target script.
This run adds ml/translation/indictrans2_processor.py to the path and re-tests.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_TRANSLATION = _HERE.parents[0] / "translation"
if str(_TRANSLATION) not in sys.path:
    sys.path.insert(0, str(_TRANSLATION))

from indictrans2_processor import IndicProcessor
from probe_nllb_santali import SCRIPT_RANGES, char_ratio_in_range

# Short imperatives + declaratives, mirroring the classroom corpus mix.
PROBE_SENTENCES = [
    "बैठ जाओ।",
    "अपनी किताब खोलो।",
    "तुम्हारा नाम क्या है?",
    "सभी बच्चे विद्यालय जाते हैं।",
    "नीचे दिए गए रिक्त स्थान भरो।",
    "सही उत्तर पर गोला लगाओ।",
]

# (tag, script code expected) - well-resourced controls first, then Santali.
TARGETS = [
    ("ben_Beng", "Beng"),
    ("tam_Taml", "Taml"),
    ("guj_Gujr", "Gujr"),
    ("mar_Deva", "Deva"),
    ("sat_Olck", "Olck"),
    ("unr_Deva", "Deva"),
]

# Ranges the base probe does not register but this control needs.
EXTRA_RANGES = {
    "Taml": (0x0B80, 0x0BFF),
    "Gujr": (0x0A80, 0x0AFF),
}


def dominant_script(text: str, ranges: dict) -> tuple[str | None, float]:
    ratios = {
        code: char_ratio_in_range(text, lo, hi) for code, (lo, hi) in ranges.items()
    }
    if not ratios:
        return None, 0.0
    best = max(ratios, key=lambda k: ratios[k])
    if ratios[best] == 0.0:
        return None, 0.0
    return best, ratios[best]


def main() -> int:
    import torch
    from load_indictrans2 import load_model_and_tokenizer

    ranges = dict(SCRIPT_RANGES)
    ranges.update(EXTRA_RANGES)

    print("Loading IndicTrans2-320M ...", flush=True)
    model, tok, cfg = load_model_and_tokenizer()
    model.eval()
    proc = IndicProcessor(inference=True)

    def translate(text: str, src: str, tgt: str) -> tuple[str, str, float]:
        """Return (postprocessed, raw_decoder_output, latency_ms)."""
        pre = proc.preprocess(text, src, tgt)
        enc = tok(pre.text, return_tensors="pt")
        t = time.perf_counter()
        with torch.inference_mode():
            out = model.generate(
                **enc,
                num_beams=4,
                max_new_tokens=96,
                early_stopping=True,
                use_cache=False,
            )
        dt = (time.perf_counter() - t) * 1000.0
        tok._switch_to_target_mode()
        raw = tok.decode(out[0], skip_special_tokens=True)
        tok._switch_to_input_mode()
        hyp = proc.postprocess(raw, tgt, pre.placeholder_entity_map)
        return hyp, raw, dt

    print("\nCONTROL: same code path, different target languages.")
    print("If well-resourced targets hit their script, the harness is correct.\n")

    summary = []
    for tag, expect in TARGETS:
        hits = raw_hits = 0
        print(f"--- hin_Deva -> {tag}  (expect script {expect}) ---")
        for s in PROBE_SENTENCES:
            hyp, raw, dt = translate(s, "hin_Deva", tag)
            dom, ratio = dominant_script(hyp, ranges)
            raw_dom, _ = dominant_script(raw, ranges)
            ok = dom == expect
            hits += ok
            raw_hits += raw_dom == expect
            flag = "OK " if ok else "MISS"
            print(f"  [{flag}] script={dom or '-'}({ratio:.2f}) {dt:7.0f}ms  "
                  f"{s[:26]!r} -> {hyp[:44]!r}")
            if raw_dom != dom:
                print(f"         raw decoder output was {raw_dom or '-'}: {raw[:44]!r}")
        rate = hits / len(PROBE_SENTENCES)
        summary.append((tag, expect, hits, raw_hits, len(PROBE_SENTENCES), rate))
        print(f"    hit rate: {hits}/{len(PROBE_SENTENCES)} = {rate:.0%} "
              f"(raw decoder output alone: {raw_hits}/{len(PROBE_SENTENCES)})\n")

    print("=" * 66)
    print("CONTROL SUMMARY (target script hit rate)")
    print("=" * 66)
    for tag, expect, hits, raw_hits, n, rate in summary:
        bar = "#" * int(rate * 20)
        print(f"  {tag:10} expect {expect:5} {hits}/{n} {rate:5.0%} {bar:20}  raw {raw_hits}/{n}")
    ctrl = [r for t, e, h, rh, n, r in summary if t not in ("sat_Olck", "unr_Deva")]
    mean_ctrl = sum(ctrl) / len(ctrl) if ctrl else 0.0
    print(f"\n  mean control hit rate (well-resourced): {mean_ctrl:.0%}")
    print("  -> If this is high, the harness is CORRECT and any Santali")
    print("     weakness is a property of the checkpoint, not the code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
