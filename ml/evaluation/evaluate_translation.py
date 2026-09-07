import json
from typing import List, Dict, Any
from ml.translation.engine import LayeredTranslationEngine
from ml.evaluation.metrics import EvaluationMetrics

def evaluate_test_set(test_pairs: List[Dict[str, Any]], engine: LayeredTranslationEngine) -> Dict[str, Any]:
    """
    Evaluates translation system over a benchmark set.
    Measures BLEU, chrF, Terminology Accuracy, latency breakdown, and tier usage.
    """
    sources = []
    references = []
    hypotheses = []
    latencies = []
    tiers_count = {}
    mandatory_terms_list = []

    for item in test_pairs:
        src = item["source"]
        ref = item["reference"]
        sources.append(src)
        references.append(ref)
        
        mandatory = item.get("mandatory_terms", [])
        mandatory_terms_list.append(mandatory)

        # Run translation
        res = engine.translate(src, src_lang=item.get("src_lang", "hin"), tgt_lang=item.get("tgt_lang", "sat"))
        hyp = res["target_text"]
        hypotheses.append(hyp)
        latencies.append(res["latency_ms"])

        tier = res["tier"]
        tiers_count[tier] = tiers_count.get(tier, 0) + 1

    bleu = EvaluationMetrics.calculate_bleu(hypotheses, [references])
    chrf = EvaluationMetrics.calculate_chrf(hypotheses, [references])
    term_acc = EvaluationMetrics.calculate_terminology_accuracy(hypotheses, mandatory_terms_list)

    avg_latency = sum(latencies) / max(len(latencies), 1)
    p50_latency = sorted(latencies)[len(latencies) // 2] if latencies else 0.0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0

    return {
        "sample_count": len(test_pairs),
        "metrics": {
            "bleu": bleu,
            "chrf": chrf,
            "terminology_accuracy": term_acc
        },
        "latency_ms": {
            "avg": round(avg_latency, 2),
            "p50": round(p50_latency, 2),
            "p95": round(p95_latency, 2)
        },
        "tier_distribution": tiers_count
    }

if __name__ == "__main__":
    # Self-test benchmark
    test_set = [
        {"source": "बैठ जाओ", "reference": "ᱫᱩᱲᱩᱵ ᱢᱮ", "mandatory_terms": ["ᱫᱩᱲᱩᱵ"]},
        {"source": "अपनी किताब खोलो", "reference": "ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ", "mandatory_terms": ["ᱯᱚᱛᱚᱵ"]},
        {"source": "गिनो और बताओ", "reference": "ᱞᱮᱠᱷᱟᱭ ᱢᱮ ᱟᱨ ᱞᱟᱹᱭ ᱢᱮ", "mandatory_terms": ["ᱞᱮᱠᱷᱟᱭ"]},
        {"source": "कितने आम हैं?", "reference": "ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?", "mandatory_terms": ["ᱩᱞ"]},
        {"source": "बहुत अच्छा", "reference": "ᱟᱹᱰᱤ ᱵᱷᱟᱹᱜᱤ", "mandatory_terms": ["ᱵᱷᱟᱹᱜᱤ"]}
    ]
    engine = LayeredTranslationEngine()
    report = evaluate_test_set(test_set, engine)
    print("Translation Evaluation Report:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
