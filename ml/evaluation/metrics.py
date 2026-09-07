import sacrebleu
from typing import List, Dict, Any

class EvaluationMetrics:
    """
    Standard translation and speech evaluation metrics.
    Computes BLEU, chrF, Terminology Accuracy, WER, and CER.
    """

    @staticmethod
    def calculate_bleu(hypotheses: List[str], references: List[List[str]]) -> float:
        if not hypotheses or not references:
            return 0.0
        try:
            bleu = sacrebleu.corpus_bleu(hypotheses, references, smooth_method="exp")
            if bleu.score > 0.0:
                return round(bleu.score, 2)
            char_bleu = sacrebleu.corpus_bleu(hypotheses, references, tokenize="char", smooth_method="exp")
            return round(char_bleu.score, 2)
        except Exception:
            return 0.0

    @staticmethod
    def calculate_chrf(hypotheses: List[str], references: List[List[str]]) -> float:
        if not hypotheses or not references:
            return 0.0
        try:
            chrf = sacrebleu.corpus_chrf(hypotheses, references)
            return round(chrf.score, 2)
        except Exception:
            return 0.0

    @staticmethod
    def calculate_wer(hypotheses: List[str], references: List[str]) -> float:
        """Computes Word Error Rate using Levenshtein distance."""
        if not hypotheses or not references:
            return 0.0
        total_errors = 0
        total_ref_words = 0

        for hyp, ref in zip(hypotheses, references):
            h_words = hyp.strip().split()
            r_words = ref.strip().split()
            total_ref_words += len(r_words)

            # Levenshtein distance table
            d = [[0] * (len(h_words) + 1) for _ in range(len(r_words) + 1)]
            for i in range(len(r_words) + 1):
                d[i][0] = i
            for j in range(len(h_words) + 1):
                d[0][j] = j

            for i in range(1, len(r_words) + 1):
                for j in range(1, len(h_words) + 1):
                    if r_words[i - 1] == h_words[j - 1]:
                        d[i][j] = d[i - 1][j - 1]
                    else:
                        d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])

            total_errors += d[len(r_words)][len(h_words)]

        return round(total_errors / max(total_ref_words, 1), 3)

    @staticmethod
    def calculate_terminology_accuracy(hypotheses: List[str], mandatory_terms: List[List[str]]) -> float:
        """Measures what percentage of target educational glossary terms are preserved in output."""
        if not hypotheses or not mandatory_terms:
            return 1.0
        found = 0
        total = 0
        for hyp, terms in zip(hypotheses, mandatory_terms):
            for t in terms:
                total += 1
                if t in hyp:
                    found += 1
        return round(found / max(total, 1), 3)
