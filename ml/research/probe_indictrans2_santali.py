"""Phase 1 probe: IndicTrans2-320M hin_Deva -> sat_Olck, measured.

Reuses the methodology of probe_nllb_santali.py so the two models can be
compared directly:

  * same CLASSROOM_CORPUS (speaker-independent behaviour probe, no reference
    translations)
  * same generation settings (num_beams=4, max_new_tokens=96, early_stopping)
  * same pure functions (score_output / analyse_outputs / is_degenerate /
    percentiles / get_rss_mb) and same ProbeReport/SentenceResult shapes
  * identical warm-up exclusion, category latency percentiles, round-trip chrF

Differences (inherent to the model):
  * IndicTrans2 is a custom arch with dual SPM vocab; loaded via
    load_indictrans2.py shim (ONNX stub + tokenizer base seeding + tie_weights
    kwarg + sinusoidal position-table rebuild). Inputs are
    ``<src_tag> <tgt_tag> <text>``, not a per-call lang attribute.
  * No forced_bos_token_id: the language pair is carried in the input text via
    language tags.
  * IndicTrans2 requires the IndicProcessor pre/post-processing wrapper it was
    trained against (ml/translation/indictrans2_processor.py). The model emits
    a UNIFIED DEVANAGARI representation for most targets; postprocessing
    transliterates it into the target script. Both steps are mandatory --
    omitting them makes every target look like Devanagari.

MEASUREMENT HISTORY (kept deliberately; see docs/feasibility-phase1.md)
  Run 1 of this probe is VOID. Two harness defects, both since fixed:
    1. IndicProcessor pre/postprocessing was not applied at all.
    2. transformers v5 zero-filled the non-persistent sinusoidal position
       buffer, making the encoder a bag of words. from_pretrained reported no
       missing/unexpected/mismatched keys, so this was silent. Output was
       fluent but word-scrambled and still passed script checks.
  Do not compare run-1 numbers with anything below.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_TRANSLATION = _HERE.parents[0] / "translation"
if str(_TRANSLATION) not in sys.path:
    sys.path.insert(0, str(_TRANSLATION))

from indictrans2_processor import (
    OLCK_POSTPROCESS_IS_LOSSY,
    IndicProcessor,
)
from probe_nllb_santali import (
    CLASSROOM_CORPUS,
    SCRIPT_RANGES,
    SentenceResult,
    analyse_outputs,
    get_rss_mb,
    host_info,
    percentiles,
    score_output,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ProbeReport:
    status: str
    model_id: str
    model_license: str
    device: str
    torch_version: str
    dtype: str
    measurement_host: dict = field(default_factory=dict)
    tokenizer_has_sat_olck: bool | None = None
    tokenizer_has_hoc: bool | None = None
    model_load_seconds: float | None = None
    rss_after_load_mb: float | None = None
    rss_peak_mb: float | None = None
    num_sentences: int = 0
    latency_ms: dict = field(default_factory=dict)
    output_validity: dict = field(default_factory=dict)
    round_trip: dict | None = None
    notes: list = field(default_factory=list)
    sentences: list = field(default_factory=list)


def write_report(report: ProbeReport, out_path: str) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--beams", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    ap.add_argument("--round-trip", action="store_true", default=True)
    ap.add_argument("--limit", type=int, default=0, help="limit corpus size (0=all)")
    ap.add_argument(
        "--out",
        default=str(REPO_ROOT / "benchmarks" / "results" / "phase1_indictrans2_hin_sat.json"),
    )
    args = ap.parse_args()

    report = ProbeReport(
        status="RUNNING",
        model_id="ai4bharat/indictrans2-indic-indic-dist-320M",
        model_license="MIT",
        device="cpu",
        torch_version="",
        dtype="float32",
        measurement_host=host_info(),
    )

    import torch
    from load_indictrans2 import load_model_and_tokenizer

    report.torch_version = torch.__version__
    report.notes.append("language-pair carried in input text (inline tags), no forced_bos used")

    src_tag, tgt_tag = "hin_Deva", "sat_Olck"
    tgt_script = tgt_tag.split("_", 1)[1]
    src_script = src_tag.split("_", 1)[1]
    if tgt_script not in SCRIPT_RANGES:
        report.notes.append(f"no Unicode range registered for script '{tgt_script}'")
    report.notes.append(f"target script under test: {tgt_script}")

    print("[2/5] Loading model + tokenizer (local 1.28 GB checkpoint) ...", flush=True)
    t0 = time.perf_counter()
    model, tok, cfg = load_model_and_tokenizer()
    model.eval()
    proc = IndicProcessor(inference=True)
    report.model_load_seconds = round(time.perf_counter() - t0, 2)
    report.rss_after_load_mb = round(get_rss_mb() or -1, 1)

    # Guard the exact defect that voided run 1: a zero position table is silent
    # (from_pretrained reports no missing keys) and produces scrambled output.
    pe = model.model.encoder.embed_positions.weights
    if bool((pe == 0).all()):
        raise RuntimeError("sinusoidal position table is all zero; output would be scrambled")
    report.notes.append(
        f"sinusoidal position table VERIFIED non-degenerate: shape {tuple(pe.shape)}, "
        f"PE[0] vs PE[1] mean|delta| = {(pe[0] - pe[1]).abs().mean().item():.6f}"
    )
    report.notes.append("IndicProcessor pre/postprocessing APPLIED (mandatory for IndicTrans2)")
    report.notes.append(f"sat_Olck postprocess caveat: {OLCK_POSTPROCESS_IS_LOSSY}")
    print(f"      loaded in {report.model_load_seconds}s | RSS {report.rss_after_load_mb} MB")
    print(f"      encoder_vocab={cfg.encoder_vocab_size} decoder_vocab={cfg.decoder_vocab_size} "
          f"share_out_emb={cfg.share_decoder_input_output_embed}")

    n_params = sum(p.numel() for p in model.parameters())
    report.notes.append(f"parameter count (MEASURED): {n_params:,}")
    report.notes.append(f"fp32 weight footprint (COMPUTED): {n_params * 4 / 1e6:.0f} MB")
    report.tokenizer_has_sat_olck = tgt_tag in tok.src_encoder
    report.tokenizer_has_hoc = "hoc_Deva" in tok.src_encoder

    corpus = CLASSROOM_CORPUS if not args.limit else CLASSROOM_CORPUS[: args.limit]
    report.notes.append(
        f"tokenizer src_encoder has '{tgt_tag}': {report.tokenizer_has_sat_olck} "
        f"(id {tok.src_encoder.get(tgt_tag)})"
    )

    def translate_one(text: str, src: str, tgt: str) -> tuple[str, float]:
        # IndicProcessor is mandatory: it normalizes/masks entities on the way
        # in and transliterates the model's unified-Devanagari output into the
        # target script on the way out.
        pre = proc.preprocess(text, src, tgt)
        enc = tok(pre.text, return_tensors="pt")
        t = time.perf_counter()
        with torch.inference_mode():
            out = model.generate(
                **enc,
                num_beams=args.beams,
                max_new_tokens=args.max_new_tokens,
                early_stopping=True,
                use_cache=False,  # v5 cache object incompatible with custom past_key_values code
            )
        dt = (time.perf_counter() - t) * 1000.0
        raw = tok.decode(out[0], skip_special_tokens=True)
        hyp = proc.postprocess(raw, tgt, pre.placeholder_entity_map)
        return hyp, dt

    print("[3/5] Warm-up pass ...", flush=True)
    _w, _wt = translate_one("बैठ जाओ।", src_tag, tgt_tag)
    report.notes.append(f"warm-up latency EXCLUDED from percentiles: {_wt:.1f} ms")

    print(f"[4/5] Translating {len(corpus)} sentences {src_tag} -> {tgt_tag} ...", flush=True)
    results: list[SentenceResult] = []
    peak = report.rss_after_load_mb or 0.0
    by_category: dict[str, list[float]] = {}

    for i, (category, src_text) in enumerate(corpus, 1):
        hyp, dt = translate_one(src_text, src_tag, tgt_tag)
        scores = score_output(hyp, src_text, tgt_script, src_script)
        sr = SentenceResult(
            source=src_text,
            hypothesis=hyp,
            latency_ms=round(dt, 2),
            n_src_chars=len(src_text),
            n_out_chars=len(hyp),
            **scores,
        )
        results.append(sr)
        by_category.setdefault(category, []).append(dt)
        rss = get_rss_mb()
        if rss:
            peak = max(peak, rss)
        dom = sr.dominant_script
        print(
            f"      [{i}/{len(corpus)}] {dt:7.1f} ms  script={dom or '-'}"
            f"({sr.script_ratios.get(dom, 0.0) if dom else 0.0:.2f})"
            f"  {src_text[:30]!r} -> {hyp[:40]!r}"
        )

    report.rss_peak_mb = round(peak, 1)
    report.num_sentences = len(results)
    report.latency_ms = percentiles([r.latency_ms for r in results])
    report.latency_ms["by_category"] = {
        k: percentiles(v) for k, v in sorted(by_category.items())
    }

    report.output_validity, validity_notes = analyse_outputs(results, tgt_script)
    report.notes.extend(validity_notes)
    n_copied = report.output_validity["n_source_script_copied"]
    n_degen = report.output_validity["n_degenerate_or_empty"]

    if args.round_trip:
        print("[5/5] Round-trip sat_Olck -> hin_Deva (WEAK adequacy signal) ...", flush=True)
        try:
            from sacrebleu.metrics import CHRF

            chrf = CHRF()
            scores = []
            for r in results:
                back, _dt = translate_one(r.hypothesis, tgt_tag, src_tag)
                r.round_trip_hi = back
                sc = chrf.sentence_score(back, [r.source]).score
                r.round_trip_chrf = round(sc, 2)
                scores.append(sc)
                print(f"      chrF={sc:5.1f}  {r.source[:30]!r} -> back {back[:40]!r}")
            report.round_trip = {
                "metric": "chrF (sacrebleu) between original Hindi and Hindi round-tripped via Santali",
                "interpretation": (
                    "WEAK SIGNAL ONLY. High chrF suggests meaning survived both hops; "
                    "low chrF cannot distinguish a bad hin->sat hop from a bad sat->hin hop. "
                    "Not a substitute for native-speaker evaluation."
                ),
                "mean_chrf": round(statistics.fmean(scores), 2) if scores else None,
                "median_chrf": round(statistics.median(scores), 2) if scores else None,
                "min_chrf": round(min(scores), 2) if scores else None,
                "max_chrf": round(max(scores), 2) if scores else None,
            }
        except Exception as e:  # pragma: no cover
            report.notes.append(f"round-trip skipped: {type(e).__name__}: {e}")

    report.sentences = [asdict(r) for r in results]
    report.status = "COMPLETED"
    write_report(report, args.out)

    print("\n" + "=" * 72)
    print("PHASE 1 PROBE COMPLETE (MEASURED on x86-64 dev host, CPU, fp32)")
    print("=" * 72)
    print(f"  model              : {report.model_id}  [{report.model_license}]")
    print(f"  params (measured)  : {n_params:,}")
    print(f"  load time          : {report.model_load_seconds} s")
    print(f"  RSS after load     : {report.rss_after_load_mb} MB   peak: {report.rss_peak_mb} MB")
    print(f"  latency p50/p90/p95: {report.latency_ms.get('p50_ms')} / "
          f"{report.latency_ms.get('p90_ms')} / {report.latency_ms.get('p95_ms')} ms")
    ov = report.output_validity
    print(f"  declared tgt script: {tgt_script}   observed: {ov['observed_dominant_script']}"
          f"{'  <-- TAG MISLABELLED' if ov['tag_script_mismatch'] else ''}")
    print(f"  mean ratio / script: {ov['mean_letter_ratio_by_script']}")
    print(f"  in observed script : {ov['n_output_in_observed_script_ge_0.9']}/{len(results)}")
    print(f"  source copied      : {n_copied}/{len(results)}")
    print(f"  degenerate         : {n_degen}/{len(results)}")
    print(f"  COLLAPSE           : {ov['collapse']['n_distinct_sources']} distinct inputs -> "
          f"{ov['collapse']['n_distinct_outputs']} distinct outputs "
          f"({ov['collapse']['n_collision_groups']} collision group(s))")
    for c in ov["collapse"]["collisions"]:
        print(f"      x{c['n_sources']} -> {c['output'][:40]!r}")
        for s in c["sources"]:
            print(f"            from {s!r}")
    if report.round_trip:
        print(f"  round-trip chrF    : mean {report.round_trip.get('mean_chrf')} "
              f"(WEAK signal, not adequacy)")
    print(f"\n  report -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
