from ml.preprocessing.normalizer import TextNormalizer
from ml.preprocessing.cleaner import DatasetCleaner
from ml.preprocessing.tokenizer import SimpleTokenizer
from ml.evaluation.metrics import EvaluationMetrics

def test_text_normalizer():
    raw_hindi = "  गिनो    और बताओ !  "
    norm = TextNormalizer.normalize(raw_hindi, lang="hin")
    assert norm == "गिनो और बताओ!"

    raw_cache = TextNormalizer.clean_for_cache(raw_hindi)
    assert raw_cache == "गिनो और बताओ"

def test_dataset_cleaner():
    # Valid pair
    pair = DatasetCleaner.clean_pair("बैठ जाओ", "ᱫᱩᱲᱩᱵ ᱢᱮ")
    assert pair is not None

    # Invalid empty pair
    empty_pair = DatasetCleaner.clean_pair("", "")
    assert empty_pair is None

    # Deduplication
    pairs = [("गिनो", "ᱞᱮᱠᱷᱟᱭ ᱢᱮ"), ("गिनो", "ᱞᱮᱠᱷᱟᱭ ᱢᱮ"), ("किताब", "ᱯᱚᱛᱚᱵ")]
    deduped = DatasetCleaner.deduplicate(pairs)
    assert len(deduped) == 2

def test_tokenizer():
    text = "गिनो, और बताओ।"
    tokens = SimpleTokenizer.tokenize(text)
    assert "गिनो" in tokens
    assert "," in tokens
    detok = SimpleTokenizer.detokenize(tokens)
    assert detok == "गिनो, और बताओ।"

def test_evaluation_metrics():
    hyps = ["ᱫᱩᱲᱩᱵ ᱢᱮ", "ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ"]
    refs = [["ᱫᱩᱲᱩᱵ ᱢᱮ", "ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ"]]
    bleu = EvaluationMetrics.calculate_bleu(hyps, refs)
    assert bleu > 90.0

    wer = EvaluationMetrics.calculate_wer(["बैठ जाओ"], ["बैठ जाओ"])
    assert wer == 0.0

    term_acc = EvaluationMetrics.calculate_terminology_accuracy(hyps, [["ᱫᱩᱲᱩᱵ"], ["ᱯᱚᱛᱚᱵ"]])
    assert term_acc == 1.0
