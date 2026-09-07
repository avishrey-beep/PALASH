"""Diagnostic: why does the target language tag not switch the output script?

The control run (control_indictrans2_targets.py) showed hin->ben/tam/guj all
returning Devanagari, which cannot be a property of IndicTrans2 (it is strong
on Bengali). So the harness is at fault. This script isolates the cause by
varying one factor at a time on a fixed sentence set:

  factor 1: tag order      "<src> <tgt> text"  vs  "<tgt> <src> text"
  factor 2: decoding       greedy (num_beams=1) vs beam search (num_beams=4)
  factor 3: use_cache      False (custom model is incompatible with the v5
                           cache object when True)

Prints the dominant output script per cell. The cell that yields the expected
script identifies the correct calling convention.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from probe_nllb_santali import SCRIPT_RANGES, char_ratio_in_range

RANGES = dict(SCRIPT_RANGES)
RANGES.update({"Taml": (0x0B80, 0x0BFF), "Gujr": (0x0A80, 0x0AFF)})

SENTENCES = [
    "सभी बच्चे विद्यालय जाते हैं।",
    "अपनी किताब खोलो।",
]
CASES = [("ben_Beng", "Beng"), ("tam_Taml", "Taml"), ("sat_Olck", "Olck")]


def dom(text: str) -> tuple[str | None, float]:
    ratios = {c: char_ratio_in_range(text, lo, hi) for c, (lo, hi) in RANGES.items()}
    best = max(ratios, key=lambda k: ratios[k]) if ratios else None
    if best is None or ratios[best] == 0.0:
        return None, 0.0
    return best, ratios[best]


def main() -> int:
    import torch
    from load_indictrans2 import load_model_and_tokenizer

    print("Loading IndicTrans2-320M ...", flush=True)
    model, tok, cfg = load_model_and_tokenizer()
    model.eval()

    def run(prompt: str, beams: int) -> str:
        enc = tok(prompt, return_tensors="pt")
        with torch.inference_mode():
            out = model.generate(
                **enc,
                num_beams=beams,
                max_new_tokens=64,
                early_stopping=True,
                use_cache=False,
            )
        tok._switch_to_target_mode()
        hyp = tok.decode(out[0], skip_special_tokens=True)
        tok._switch_to_input_mode()
        return hyp

    for tgt, expect in CASES:
        print(f"\n{'='*70}\nTARGET {tgt}  (expect script {expect})\n{'='*70}")
        for sent in SENTENCES:
            print(f"\n  source: {sent!r}")
            for order_name, prompt in (
                ("src tgt", f"hin_Deva {tgt} {sent}"),
                ("tgt src", f"{tgt} hin_Deva {sent}"),
            ):
                for beams in (1, 4):
                    hyp = run(prompt, beams)
                    d, r = dom(hyp)
                    ok = "OK " if d == expect else "   "
                    print(f"    [{ok}] order={order_name:8} beams={beams}  "
                          f"script={d or '-'}({r:.2f})  -> {hyp[:46]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
