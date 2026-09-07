"""Cache-effectiveness experiment for the layered TRANSLATION engine (§45).

WHAT CHANGED AND WHY (§2, §72)
------------------------------
The previous version wrapped every pipeline in a mock ASR (which echoed the
expected text without decoding audio) and a mock sine-wave TTS, then reported
per-pipeline "latency" and hardcoded ``simulated_ram_mb`` figures (580 / 15 /
25). The audio stages did no real work, and the RAM numbers were invented, not
measured -- both are §72 fabrications. The conclusion string asserted a
"massive reduction ... proving indispensable" on the strength of those numbers.

This rewrite keeps the ONE real, defensible comparison the experiment was
built to make: how much the phrase cache + translation memory reduce
*translation* latency versus always paying for neural inference, and how often
they hit on a realistic classroom corpus. ASR/TTS ran on-device and are out of
scope here, so they are not simulated. No RAM figure is reported because none
is measured here.

  Pipeline A -- always neural: bypass cache/TM, force IndicTrans2 every time.
  Pipeline B -- layered: cache -> translation memory -> neural fallback.

Both measure wall-clock translation time only.
"""

import sys
import os
import time
import json
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from ml.translation.engine import LayeredTranslationEngine
from ml.translation.model_wrapper import TranslationModelWrapper


def run_cache_experiment() -> Dict[str, Any]:
    print("=" * 70)
    print("SECTION 45 CACHE EXPERIMENT: always-neural vs layered translation")
    print("Scope: TEXT translation latency only. ASR/TTS are on-device.")
    print("=" * 70)

    db = SessionLocal()
    layered_engine = LayeredTranslationEngine(db)
    direct_model = TranslationModelWrapper()

    if not direct_model.is_available():
        print(
            "Neural model not present; Pipeline A cannot run. Install the "
            "IndicTrans2 weights (see ml/translation/indictrans2_runtime.py) "
            "before benchmarking. Aborting rather than reporting fake numbers."
        )
        db.close()
        return {"error": "MODEL_UNAVAILABLE"}

    cached_sentences = [
        "बैठ जाओ", "खड़े हो जाओ", "अपनी किताब खोलो", "ध्यान से सुनो",
        "गिनो और बताओ", "कितने आम हैं?", "तीन और दो मिलाकर कितने होते हैं?",
        "बहुत अच्छा", "शाबाश बच्चों", "अपनी कॉपी में लिखो",
    ] * 2  # 20 likely-cached utterances

    novel_sentences = [
        "आज हम सब मिलकर कक्षा दो में एक नया खेल खेलेंगे",
        "इस पेड़ पर तीन चिड़ियाँ बैठी हुई हैं",
        "अपने बस्ते से पेंसिल और रबर निकालो",
        "श्यामपट्ट पर लिखे हुए अंकों को ध्यान से देखो",
        "क्या तुमने अपना गृहकार्य पूरा कर लिया है?",
    ] * 4  # 20 novel utterances

    test_corpus = cached_sentences + novel_sentences  # 40 total

    # --- PIPELINE A: always neural (bypass cache + TM) ---
    print("\nPipeline A (always neural, cache bypassed)...")
    latencies_a: List[float] = []
    for text in test_corpus:
        t0 = time.perf_counter()
        _ = direct_model.translate(text, src_lang="hin", tgt_lang="sat")
        latencies_a.append((time.perf_counter() - t0) * 1000.0)

    # --- PIPELINE B: layered cache -> TM -> neural fallback ---
    print("Pipeline B (layered: cache -> TM -> neural)...")
    latencies_b: List[float] = []
    cache_hits_b = 0
    tm_hits_b = 0
    for text in test_corpus:
        t0 = time.perf_counter()
        res = layered_engine.translate(text, src_lang="hin", tgt_lang="sat")
        latencies_b.append((time.perf_counter() - t0) * 1000.0)
        tier = str(res.get("tier", ""))
        if tier.startswith("cache"):
            cache_hits_b += 1
        elif tier == "translation_memory":
            tm_hits_b += 1

    db.close()

    def get_stats(vals: List[float]) -> Dict[str, float]:
        s = sorted(vals)
        n = len(s)
        return {
            "avg_ms": round(sum(s) / n, 2),
            "p50_ms": round(s[n // 2], 2),
            "p95_ms": round(s[min(int(n * 0.95), n - 1)], 2),
            "min_ms": round(s[0], 2),
            "max_ms": round(s[-1], 2),
        }

    stats_a = get_stats(latencies_a)
    stats_b = get_stats(latencies_b)

    hit_rate_b = round((cache_hits_b + tm_hits_b) / len(test_corpus) * 100.0, 1)
    speedup_b = round(stats_a["avg_ms"] / max(stats_b["avg_ms"], 0.01), 2)

    report = {
        "measurement": "MEASURED",
        "scope": "text_translation_latency_only",
        "corpus_size": len(test_corpus),
        "ram_note": (
            "RAM footprint is NOT measured by this script and is not reported. "
            "Any earlier 'simulated_ram_mb' figures were fabricated."
        ),
        "pipeline_a_always_neural": {
            "stats": stats_a,
            "cache_hit_rate_pct": 0.0,
        },
        "pipeline_b_layered": {
            "stats": stats_b,
            "cache_hit_rate_pct": hit_rate_b,
            "cache_hits": cache_hits_b,
            "translation_memory_hits": tm_hits_b,
            "speedup_vs_a": speedup_b,
        },
        "conclusion": (
            f"On this {len(test_corpus)}-sentence corpus the layered engine "
            f"served {hit_rate_b}% of requests from the phrase cache or "
            f"translation memory, giving a measured {speedup_b}x mean "
            f"translation-latency reduction versus always running neural "
            f"inference. This measures the translation stage only; end-to-end "
            f"voice latency and memory footprint are out of scope here."
        ),
    }

    print("\n" + "=" * 70)
    print("CACHE EXPERIMENT RESULTS (translation stage only):")
    print(
        f"  Pipeline A (always neural): avg={stats_a['avg_ms']}ms "
        f"p50={stats_a['p50_ms']}ms p95={stats_a['p95_ms']}ms | hit rate 0.0%"
    )
    print(
        f"  Pipeline B (layered):       avg={stats_b['avg_ms']}ms "
        f"p50={stats_b['p50_ms']}ms p95={stats_b['p95_ms']}ms | "
        f"hit rate {hit_rate_b}% (speedup {speedup_b}x)"
    )
    print(f"\nFinding: {report['conclusion']}")
    print("=" * 70)

    out_file = "storage/exports/cache_experiment_report.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report saved to {out_file}")

    return report


if __name__ == "__main__":
    run_cache_experiment()
