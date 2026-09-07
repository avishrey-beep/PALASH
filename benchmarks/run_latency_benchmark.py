"""Server-side TRANSLATION latency benchmark (honest scope).

WHAT THIS USED TO DO, AND WHY IT WAS REMOVED (§2, §72)
------------------------------------------------------
The previous version fed a synthetic sine-wave WAV into a mock ASR that simply
echoed ``expected_text`` (it never decoded audio), ran a mock sine-wave TTS,
and then printed an "OVERALL MEASURED BENCHMARK SUMMARY" with ASR/TTS/end-to-end
percentiles against the <3s SLA. Every one of those numbers was fabricated: the
ASR and TTS stages did no real work, so their "latency" measured only the cost
of the mock. Reporting that as a measured end-to-end voice benchmark is exactly
the fabrication §72 forbids.

WHAT THIS MEASURES NOW
----------------------
Only the neural translation tier, which is real (IndicTrans2-320M running
locally). ASR and TTS now run on the device, so:

  * ASR latency, TTS latency, and true end-to-end voice latency CANNOT be
    measured here. They are collected on-device and persisted via
    POST /api/v1/speech/utterances. This script does not invent them.
  * The <3s end-to-end SLA is therefore NOT evaluated here -- translation is
    only one stage of that budget. This script reports translation latency as
    a component input to that budget, clearly labelled.

Cache hits (Tier 1/2) and neural inference (Tier 3) are reported separately,
because averaging a sub-millisecond cache hit with a multi-second neural
inference would produce a meaningless blended number.
"""

import sys
import os
import time
import json
from typing import List, Dict, Any

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from ml.translation.engine import LayeredTranslationEngine


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    return {
        "p50": round(sorted_vals[int(n * 0.50)], 2),
        "p90": round(sorted_vals[min(int(n * 0.90), n - 1)], 2),
        "p95": round(sorted_vals[min(int(n * 0.95), n - 1)], 2),
        "p99": round(sorted_vals[min(int(n * 0.99), n - 1)], 2),
        "avg": round(sum(sorted_vals) / n, 2),
    }


def run_latency_benchmark() -> Dict[str, Any]:
    print("=" * 70)
    print("SERVER-SIDE TRANSLATION LATENCY BENCHMARK")
    print("Scope: neural/cached TEXT translation only. NOT end-to-end voice.")
    print("ASR + TTS + VAD run on-device and are NOT measured here.")
    print("=" * 70)

    db = SessionLocal()
    engine = LayeredTranslationEngine(db)

    # Representative classroom sentences. The label records the EXPECTED tier,
    # but the actual tier taken is read from the engine result -- never assumed.
    test_cases = [
        ("बैठ जाओ", "Short command (expect cache)"),
        ("अपनी किताब खोलो", "Instruction (expect cache)"),
        ("गिनो और बताओ कितने आम हैं?", "Math question (expect cache)"),
        ("आज हम कक्षा दो में गणित का नया पाठ पढ़ेंगे", "Longer novel sentence (expect neural)"),
        ("बहुत अच्छा शाबाश बच्चों", "Praise expression (expect cache)"),
    ]

    iterations_per_case = 20
    cache_latencies: List[float] = []
    neural_latencies: List[float] = []
    results_by_case: Dict[str, Any] = {}

    try:
        for phrase, label in test_cases:
            print(f"\nEvaluating: '{phrase}' ({label})...")
            case_latencies: List[float] = []
            last: Dict[str, Any] = {}

            for _ in range(iterations_per_case):
                t0 = time.perf_counter()
                last = engine.translate(phrase, src_lang="hin", tgt_lang="sat")
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                case_latencies.append(elapsed_ms)

            tier = last.get("tier", "unknown")
            # Bucket by whether real neural inference ran, so the two regimes
            # are never blended into one misleading percentile.
            is_neural = str(tier).startswith("neural")
            if is_neural:
                neural_latencies.extend(case_latencies)
            else:
                cache_latencies.extend(case_latencies)

            results_by_case[label] = {
                "phrase": phrase,
                "tier_used": tier,
                "target_text": last.get("target_text"),
                "regime": "neural_inference" if is_neural else "cache_or_memory",
                "wall_clock_latency_ms": calculate_percentiles(case_latencies),
                # If the engine reported its own measured inference time, keep it.
                "engine_reported_inference_ms": last.get("inference_ms"),
            }

        report = {
            "measurement": "MEASURED",
            "scope": "server_side_text_translation_only",
            "not_measured_here": [
                "asr_latency_ms (on-device)",
                "tts_latency_ms (on-device)",
                "vad_latency_ms (on-device)",
                "end_to_end_voice_latency_ms (on-device; sum of all stages)",
            ],
            "end_to_end_sla_ms": 3000.0,
            "end_to_end_sla_evaluated_here": False,
            "end_to_end_sla_note": (
                "Translation is one stage of the <3s budget. End-to-end SLA can "
                "only be judged on-device where ASR/TTS latency is real."
            ),
            "cache_or_memory_latency_ms": calculate_percentiles(cache_latencies),
            "cache_or_memory_trials": len(cache_latencies),
            "neural_inference_latency_ms": calculate_percentiles(neural_latencies),
            "neural_inference_trials": len(neural_latencies),
            "cases": results_by_case,
        }

        print("\n" + "=" * 70)
        print("MEASURED TRANSLATION LATENCY (server-side text only):")
        c = report["cache_or_memory_latency_ms"]
        n = report["neural_inference_latency_ms"]
        print(
            f"  Cache/memory hits ({report['cache_or_memory_trials']} trials): "
            f"p50={c['p50']}ms p95={c['p95']}ms"
        )
        print(
            f"  Neural inference ({report['neural_inference_trials']} trials): "
            f"p50={n['p50']}ms p95={n['p95']}ms"
        )
        print("  End-to-end voice SLA: NOT evaluated here (device-only stages).")
        print("=" * 70)

        out_file = "storage/exports/translation_latency_report.json"
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to {out_file}")

        return report

    finally:
        db.close()


if __name__ == "__main__":
    run_latency_benchmark()
