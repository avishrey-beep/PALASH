"""
Phase 1 feasibility probe: does Hindi -> Santali neural translation actually
work, and at what CPU latency?

This script makes NO claims it does not measure. It:
  1. Verifies the requested target language is a real tag in the checkpoint,
     and ABORTS rather than produce a result for an unsupported language.
  2. Loads the model (default facebook/nllb-200-distilled-600M, CC-BY-NC-4.0).
  3. Translates a real Hindi primary-classroom corpus on CPU.
  4. Measures per-sentence wall-clock latency (p50/p90/p95/p99), overall and
     per utterance category, plus RSS after load and peak RSS.
  5. Applies output checks that do NOT require a Santali speaker:
       - which script is the output ACTUALLY in? (all registered scripts are
         measured, because a checkpoint's tag can be mislabelled)
       - did the model just copy the source script through?
       - is the output degenerate (empty / repetition loop)?
       - OUTPUT COLLAPSE: do distinct inputs yield byte-identical outputs?
  6. Round-trips Hindi -> target -> Hindi and reports chrF against the
     original Hindi as a WEAK adequacy signal only.

Adequacy of the target-language text CANNOT be established by this script.
That requires native-speaker review. Two things it CAN establish objectively:
a mislabelled script tag, and output collapse — both are decisive on their own.

Usage:
    python -m ml.research.probe_nllb_santali --tgt-lang sat_Beng
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path

# --- Unicode blocks we use for objective, speaker-independent script checks ---
# Keyed by the ISO 15924 script code used in FLORES-style tags (xxx_Yyyy).
SCRIPT_RANGES: dict[str, tuple[int, int]] = {
    "Olck": (0x1C50, 0x1C7F),  # Ol Chiki (official Santali script)
    "Deva": (0x0900, 0x097F),  # Devanagari
    "Beng": (0x0980, 0x09FF),  # Bengali/Assamese
    "Orya": (0x0B00, 0x0B7F),  # Odia
    "Mtei": (0xABC0, 0xABFF),  # Meitei Mayek
    "Latn": (0x0041, 0x024F),  # Latin
    "Arab": (0x0600, 0x06FF),  # Arabic
}
OL_CHIKI_RANGE = SCRIPT_RANGES["Olck"]
DEVANAGARI_RANGE = SCRIPT_RANGES["Deva"]

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class SentenceResult:
    source: str
    hypothesis: str
    latency_ms: float
    n_src_chars: int
    n_out_chars: int
    # Ratio of output letters falling in EVERY registered script range, not just
    # the one the language tag claims. A checkpoint's tag can be mislabelled
    # (facebook/nllb-200-distilled-600M declares `sat_Beng` but emits Ol Chiki),
    # so measuring only the declared script yields 0.0 and reads as failure when
    # the model is in fact producing valid target-language text.
    script_ratios: dict = field(default_factory=dict)
    dominant_script: str | None = None  # highest-ratio script, or None if no letters
    target_script_ratio: float = 0.0  # ratio for the script named in the tag
    source_script_ratio: float = 0.0  # ratio for the source script (copy detector)
    copied_source: bool = False
    degenerate: bool = False
    round_trip_hi: str | None = None
    round_trip_chrf: float | None = None


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
    tokenizer_has_unr: bool | None = None
    model_load_seconds: float | None = None
    rss_after_load_mb: float | None = None
    rss_peak_mb: float | None = None
    num_sentences: int = 0
    latency_ms: dict = field(default_factory=dict)
    output_validity: dict = field(default_factory=dict)
    round_trip: dict = field(default_factory=dict)
    sentences: list = field(default_factory=list)
    notes: list = field(default_factory=list)


# Real Hindi primary-classroom utterances (FLN-style instructions, questions,
# commands, numbers, names). Source side authored for this evaluation; the
# Santali side is deliberately NOT provided because we have no verified
# reference translations. This probe measures behaviour, not accuracy.
CLASSROOM_CORPUS: list[tuple[str, str]] = [
    ("command_short", "बैठ जाओ।"),
    ("command_short", "खड़े हो जाओ।"),
    ("command_short", "ध्यान से सुनो।"),
    ("command_short", "अपनी किताब खोलो।"),
    ("instruction", "अपनी कॉपी में आज की तारीख लिखो।"),
    ("instruction", "वस्तुओं को गिनो और संख्या लिखो।"),
    ("instruction", "चित्र देखो और नाम बताओ।"),
    ("question_number", "कितने आम हैं?"),
    ("question_number", "तीन और दो मिलाकर कितने होते हैं?"),
    ("question_number", "बीस में से पाँच निकालो, कितने बचे?"),
    ("question_wh", "यह कौन सा रंग है?"),
    ("question_wh", "तुम्हारा नाम क्या है?"),
    ("praise", "बहुत अच्छा।"),
    ("praise", "शाबाश बच्चों।"),
    ("named_entity", "सीता के पास चार पेंसिल हैं।"),
    ("named_entity", "राजू ने दो रोटी खाईं।"),
    ("longer", "आज हम कक्षा दो में जोड़ के बारे में सीखेंगे और बीस तक की संख्याओं को जोड़ना सीखेंगे।"),
    ("longer", "इस पेड़ पर तीन चिड़ियाँ बैठी हुई हैं और दो चिड़ियाँ उड़ रही हैं।"),
    ("longer", "अपने बस्ते से पेंसिल और रबर निकालकर मेज पर रखो।"),
    ("assessment", "नीचे दिए गए रिक्त स्थान भरो।"),
    ("assessment", "सही उत्तर पर गोला लगाओ।"),
    ("assessment", "मिलान करो और जोड़े बनाओ।"),
]


def char_ratio_in_range(text: str, lo: int, hi: int) -> float:
    """Fraction of *letter* characters that fall in the given Unicode range."""
    letters = [c for c in text if unicodedata.category(c).startswith("L")]
    if not letters:
        return 0.0
    n = sum(1 for c in letters if lo <= ord(c) <= hi)
    return n / len(letters)


def has_char_repetition_loop(text: str) -> bool:
    """Detect an intra-word character loop, e.g. 'एम्मोआउआउआउआउआउ'.

    Whitespace-delimited n-gram counting cannot see this: the whole loop is a
    single token, so `is_degenerate`'s token checks score it as ordinary output.
    Observed for real -- one such output also took 20,348 ms to generate, so
    missing it understates both the failure rate and the latency tail.

    Only tokens of >= 12 characters are considered, and a bigram/trigram must
    repeat >= 4 times AND cover >= 60% of the token. Long legitimate Indic
    words (विद्यालय = 8, ᱵᱤᱨᱫᱟᱹᱜᱟᱲ = 9) fall under the length gate.
    """
    for tok in text.split():
        if len(tok) < 12:
            continue
        for n in (2, 3, 4):
            if len(tok) < n * 4:
                continue
            grams = [tok[i : i + n] for i in range(len(tok) - n + 1)]
            _gram, count = Counter(grams).most_common(1)[0]
            if count >= 4 and (count * n) / len(tok) >= 0.6:
                return True
    return False


def is_degenerate(text: str) -> bool:
    """Detect empty output or a repetition loop.

    Three distinct failure modes, all real in observed seq2seq output:

      * unigram domination - one token occupies most of the output
        ("ᱚᱞ ᱚᱞ ᱚᱞ ᱚᱞ ...")
      * repeated n-gram block - a phrase cycles
        ("सही उदाहरण के लिए उदाहरण के लिए उदाहरण के लिए"), which unigram
        counting alone does NOT catch: there the most frequent token holds only
        3/10 of the output while a trigram covers 9/10 of it.
      * intra-word character loop - "एम्मोआउआउआउआउआउ", a single token with no
        spaces, invisible to both token-level checks above.

    Thresholds are deliberately conservative; a false positive here would
    discard a valid translation, which is worse than missing one loop.
    """
    t = text.strip()
    if not t:
        return True
    toks = t.split()
    if not toks:
        return True

    # A short output made entirely of one repeated token is degenerate even
    # below the length gate below.
    if len(toks) >= 2 and len(set(toks)) == 1:
        return True

    # Character-level check runs before the token-count gate: a character loop
    # is frequently a single token, so it never reaches the checks below.
    if has_char_repetition_loop(t):
        return True

    if len(toks) < 6:
        return False

    # Unigram domination.
    if max(toks.count(x) for x in set(toks)) / len(toks) >= 0.5:
        return True

    # Repeated n-gram block. `coverage` is the fraction of the output occupied
    # by the repeats of the single most frequent n-gram.
    for n in range(2, min(5, len(toks) // 2 + 1)):
        grams = [tuple(toks[i : i + n]) for i in range(len(toks) - n + 1)]
        _gram, count = Counter(grams).most_common(1)[0]
        coverage = (count * n) / len(toks)
        if (count >= 3 and coverage >= 0.5) or (count >= 2 and coverage >= 0.75):
            return True

    return False


def get_rss_mb() -> float | None:
    try:
        import psutil  # type: ignore

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        return None


def host_info() -> dict:
    import platform

    info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "logical_cpus": os.cpu_count(),
    }
    try:
        import psutil  # type: ignore

        info["total_ram_gb"] = round(psutil.virtual_memory().total / 1e9, 1)
    except Exception:
        pass
    info["IMPORTANT"] = (
        "These latencies are MEASURED on this x86-64 development host, NOT on "
        "the 2 GB Android target. They are an upper bound on quality and a "
        "LOWER bound on latency. Android numbers remain NOT MEASURED."
    )
    return info


def percentiles(vals: list[float]) -> dict:
    if not vals:
        return {}
    s = sorted(vals)

    def pct(p: float) -> float:
        # nearest-rank percentile
        k = max(0, min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1)))))
        return round(s[k], 2)

    return {
        "n": len(s),
        "mean_ms": round(statistics.fmean(s), 2),
        "p50_ms": pct(50),
        "p90_ms": pct(90),
        "p95_ms": pct(95),
        "p99_ms": pct(99),
        "min_ms": round(s[0], 2),
        "max_ms": round(s[-1], 2),
    }


def score_output(hypothesis: str, source: str, tgt_script: str, src_script: str) -> dict:
    """Speaker-independent per-sentence checks. Pure function, no model needed.

    Measures the output against EVERY registered script, not just the one the
    language tag claims, because a checkpoint's tag can be mislabelled.
    """
    ratios = {
        code: round(char_ratio_in_range(hypothesis, lo, hi), 3)
        for code, (lo, hi) in SCRIPT_RANGES.items()
    }
    dominant = max(ratios, key=lambda k: ratios[k]) if ratios else None
    if dominant is not None and ratios[dominant] == 0.0:
        dominant = None  # no letters in any registered script
    src_ratio = ratios.get(src_script, 0.0)
    return {
        "script_ratios": ratios,
        "dominant_script": dominant,
        "target_script_ratio": ratios.get(tgt_script, 0.0),
        "source_script_ratio": src_ratio,
        "copied_source": (hypothesis.strip() == source.strip()) or src_ratio > 0.5,
        "degenerate": is_degenerate(hypothesis),
    }


def analyse_outputs(
    results: "list[SentenceResult]", tgt_script: str
) -> tuple[dict, list[str]]:
    """Corpus-level speaker-independent analysis. Pure function, no model needed.

    Returns (output_validity_block, notes). Detects two things that are decisive
    on their own and require no target-language knowledge:

      * a mislabelled script tag — e.g. facebook/nllb-200-distilled-600M
        declares `sat_Beng` but emits Ol Chiki. Reporting only the declared
        script yields 0.0 and reads as total failure when the model is in fact
        producing valid target-language text.
      * output collapse — distinct source sentences producing byte-identical
        target text. The model cannot be conveying both meanings, whatever the
        target language is.
    """
    n = max(len(results), 1)

    mean_by_script = {
        code: round(statistics.fmean([r.script_ratios.get(code, 0.0) for r in results]), 3)
        for code in SCRIPT_RANGES
    } if results else {}
    observed_script = max(mean_by_script, key=lambda k: mean_by_script[k]) if mean_by_script else None
    if observed_script and mean_by_script[observed_script] == 0.0:
        observed_script = None
    tag_mislabelled = bool(observed_script and observed_script != tgt_script)

    # Normalise to NFC so a difference in Unicode composition is not mistaken
    # for a difference in content.
    collapse_groups: dict[str, list[str]] = {}
    for r in results:
        key = unicodedata.normalize("NFC", r.hypothesis.strip())
        collapse_groups.setdefault(key, []).append(r.source)
    collisions = [
        {"output": out, "n_sources": len(srcs), "sources": srcs}
        for out, srcs in collapse_groups.items()
        if len(srcs) > 1
    ]
    n_distinct_src = len({unicodedata.normalize("NFC", r.source.strip()) for r in results})

    n_in_declared = sum(1 for r in results if r.target_script_ratio >= 0.9)
    n_in_observed = sum(
        1 for r in results
        if observed_script and r.script_ratios.get(observed_script, 0.0) >= 0.9
    )
    n_copied = sum(1 for r in results if r.copied_source)
    n_degen = sum(1 for r in results if r.degenerate)

    validity = {
        "definition": "speaker-independent checks only; adequacy NOT assessed",
        "declared_target_script": tgt_script,
        "observed_dominant_script": observed_script,
        "tag_script_mismatch": tag_mislabelled,
        "mean_letter_ratio_by_script": mean_by_script,
        "n_output_in_declared_script_ge_0.9": n_in_declared,
        "n_output_in_observed_script_ge_0.9": n_in_observed,
        "n_source_script_copied": n_copied,
        "n_degenerate_or_empty": n_degen,
        "pct_output_in_observed_script": round(100.0 * n_in_observed / n, 1),
        "collapse": {
            "definition": (
                "Distinct source sentences producing byte-identical target output "
                "(NFC-normalised). Any collision is objective evidence that at least "
                "one meaning is not being conveyed. Requires no target-language "
                "knowledge to interpret."
            ),
            "n_distinct_sources": n_distinct_src,
            "n_distinct_outputs": len(collapse_groups),
            "n_collision_groups": len(collisions),
            "collisions": collisions,
        },
    }

    notes: list[str] = []
    if tag_mislabelled:
        notes.append(
            f"TAG MISLABELLED: declared target script '{tgt_script}' but output is "
            f"{mean_by_script[observed_script]:.3f} '{observed_script}'. Do not read the "
            f"declared-script count as a failure."
        )
    if collisions:
        notes.append(
            f"OUTPUT COLLAPSE: {n_distinct_src} distinct inputs -> {len(collapse_groups)} "
            f"distinct outputs across {len(collisions)} collision group(s). "
            f"Speaker-independent evidence of inadequate output."
        )
    return validity, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="facebook/nllb-200-distilled-600M")
    ap.add_argument("--src-lang", default="hin_Deva")
    ap.add_argument("--tgt-lang", default="sat_Olck")
    ap.add_argument("--beams", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    ap.add_argument("--round-trip", action="store_true", default=True)
    ap.add_argument("--limit", type=int, default=0, help="limit corpus size (0=all)")
    ap.add_argument(
        "--out",
        default=str(REPO_ROOT / "benchmarks" / "results" / "phase1_nllb_hin_sat.json"),
    )
    args = ap.parse_args()

    report = ProbeReport(
        status="RUNNING",
        model_id=args.model,
        model_license="cc-by-nc-4.0 (NON-COMMERCIAL; research/eval only)",
        device="cpu",
        torch_version="",
        dtype="float32",
        measurement_host=host_info(),
    )

    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    report.torch_version = torch.__version__
    torch.set_num_threads(os.cpu_count() or 4)

    print(f"[1/5] Loading tokenizer for {args.model} ...", flush=True)
    tok = AutoTokenizer.from_pretrained(args.model)

    # --- Verify language coverage from the tokenizer itself (ground truth) ---
    # NOTE: NLLB language tags are ADDED tokens. `get_vocab()` on transformers v5
    # does not surface them, so querying it produces a false negative. The
    # authoritative source is `added_tokens_encoder`.
    added = dict(getattr(tok, "added_tokens_encoder", {}) or {})
    lang_tags = sorted(k for k in added if len(k) == 8 and k[3] == "_")
    report.notes.append(f"tokenizer exposes {len(lang_tags)} language tags via added_tokens_encoder")

    def has_lang(prefix: str) -> list[str]:
        return [t for t in lang_tags if t.startswith(prefix)]

    sat_variants = has_lang("sat")
    report.tokenizer_has_sat_olck = "sat_Olck" in lang_tags
    report.tokenizer_has_hoc = bool(has_lang("hoc"))
    report.tokenizer_has_unr = bool(has_lang("unr"))
    report.notes.append(f"Santali tag variants present in this checkpoint: {sat_variants}")
    report.notes.append(f"Ol Chiki (Olck) tags present: {[t for t in lang_tags if t.endswith('Olck')]}")

    print(f"      language tags in checkpoint : {len(lang_tags)}")
    print(f"      Santali variants           : {sat_variants or 'NONE'}")
    print(f"      sat_Olck (Ol Chiki) present: {report.tokenizer_has_sat_olck}")
    print(f"      hoc_* (Ho) present         : {report.tokenizer_has_hoc}")
    print(f"      unr_* (Mundari) present    : {report.tokenizer_has_unr}")

    if args.tgt_lang not in lang_tags:
        report.status = "ABORTED_TARGET_TAG_NOT_IN_CHECKPOINT"
        report.notes.append(
            f"Requested target '{args.tgt_lang}' is not a tag in this checkpoint. "
            f"Available Santali variant(s): {sat_variants}. Refusing to run so that no "
            f"unsupported-language result is produced."
        )
        write_report(report, args.out)
        print(f"\nABORT: '{args.tgt_lang}' is not in this checkpoint. Available: {sat_variants}")
        return 2

    tgt_script = args.tgt_lang.split("_", 1)[1]
    if tgt_script not in SCRIPT_RANGES:
        report.notes.append(f"no Unicode range registered for script '{tgt_script}'")
    report.notes.append(f"target script under test: {tgt_script}")

    print(f"[2/5] Loading model weights (this downloads ~2.5 GB on first run) ...", flush=True)
    t0 = time.perf_counter()
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model, dtype=torch.float32)
    model.eval()
    report.model_load_seconds = round(time.perf_counter() - t0, 2)
    report.rss_after_load_mb = round(get_rss_mb() or -1, 1)
    print(f"      loaded in {report.model_load_seconds}s | RSS {report.rss_after_load_mb} MB")

    n_params = sum(p.numel() for p in model.parameters())
    report.notes.append(f"parameter count (MEASURED): {n_params:,}")
    report.notes.append(
        f"fp32 weight footprint (COMPUTED): {n_params * 4 / 1e6:.0f} MB"
    )

    corpus = CLASSROOM_CORPUS if not args.limit else CLASSROOM_CORPUS[: args.limit]
    tgt_id = tok.convert_tokens_to_ids(args.tgt_lang)
    src_id = tok.convert_tokens_to_ids(args.src_lang)
    report.notes.append(f"forced_bos_token_id({args.tgt_lang}) = {tgt_id}")

    def translate_one(text: str, src: str, tgt: str) -> tuple[str, float]:
        tok.src_lang = src
        enc = tok(text, return_tensors="pt")
        bos = tok.convert_tokens_to_ids(tgt)
        t = time.perf_counter()
        with torch.inference_mode():
            out = model.generate(
                **enc,
                forced_bos_token_id=bos,
                num_beams=args.beams,
                max_new_tokens=args.max_new_tokens,
                early_stopping=True,
            )
        dt = (time.perf_counter() - t) * 1000.0
        hyp = tok.batch_decode(out, skip_special_tokens=True)[0]
        return hyp, dt

    # warm-up (excluded from statistics: first call pays lazy-init cost)
    print("[3/5] Warm-up pass ...", flush=True)
    _w, _wt = translate_one("बैठ जाओ।", args.src_lang, args.tgt_lang)
    report.notes.append(f"warm-up latency EXCLUDED from percentiles: {_wt:.1f} ms")

    print(f"[4/5] Translating {len(corpus)} sentences {args.src_lang} -> {args.tgt_lang} ...", flush=True)
    results: list[SentenceResult] = []
    peak = report.rss_after_load_mb or 0.0
    by_category: dict[str, list[float]] = {}

    src_script = args.src_lang.split("_", 1)[1]

    for i, (category, src_text) in enumerate(corpus, 1):
        hyp, dt = translate_one(src_text, args.src_lang, args.tgt_lang)
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
                back, _dt = translate_one(r.hypothesis, args.tgt_lang, args.src_lang)
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


def write_report(report: ProbeReport, out_path: str) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
