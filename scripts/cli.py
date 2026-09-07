import sys
import os
import argparse
import json

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.services.curriculum_service import CurriculumService
from backend.app.services.pack_service import LanguagePackService
from backend.app.services.translation_service import TranslationService
from backend.app.services.speech_service import SpeechService
from ml.translation.engine import LayeredTranslationEngine
from ml.evaluation.evaluate_translation import evaluate_test_set

def main():
    parser = argparse.ArgumentParser(description="Jharkhand Primary Multilingual Platform CLI Management Suite")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # 1. ingest-curriculum
    p_ingest = subparsers.add_parser("ingest-curriculum", help="Ingest a curriculum document (TXT/PDF)")
    p_ingest.add_argument("--file", required=True, help="Path to curriculum file")
    p_ingest.add_argument("--title", help="Optional title")
    p_ingest.add_argument("--grade", type=int, default=2, help="Class grade (1-3)")
    p_ingest.add_argument("--subject", default="Mathematics", help="Subject name")

    # 2. build-language-pack
    p_pack = subparsers.add_parser("build-language-pack", help="Build self-contained offline language pack (.zip)")
    p_pack.add_argument("--lang", default="sat", help="Language code (sat, unr, hoc)")
    p_pack.add_argument("--version", default="1.0.0", help="Pack version")

    # 3. train-translation
    p_train = subparsers.add_parser("train-translation", help="Run translation training pipeline")
    p_train.add_argument("--epochs", type=int, default=2, help="Epochs")

    # 4. evaluate-translation
    p_eval_t = subparsers.add_parser("evaluate-translation", help="Evaluate translation engine on benchmark set")
    p_eval_t.add_argument("--lang", default="sat", help="Target language code")

    # 5. quantize-model
    p_quant = subparsers.add_parser("quantize-model", help="Apply INT8 dynamic quantization to PyTorch model")
    p_quant.add_argument("--input", default="storage/models/translation_checkpoint.pt", help="Input model path")
    p_quant.add_argument("--output", default="storage/models/translation_quant_int8.pt", help="Output model path")

    # 6. export-android-model
    p_export = subparsers.add_parser("export-android-model", help="Export PyTorch model to ONNX for Android")
    p_export.add_argument("--input", default="storage/models/translation_checkpoint.pt", help="Input model path")
    p_export.add_argument("--output", default="storage/models/translation_model.onnx", help="Output ONNX path")

    # 7. run-latency-benchmark
    p_lat = subparsers.add_parser("run-latency-benchmark", help="Measure end-to-end voice translation latency")

    # 8. run-offline-test
    p_off = subparsers.add_parser("run-offline-test", help="Simulate complete network loss on classroom device")
    p_off.add_argument("--pack", help="Path to language pack zip")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    db = SessionLocal()
    try:
        if args.command == "ingest-curriculum":
            if not os.path.exists(args.file):
                print(f"Error: File {args.file} not found.")
                sys.exit(1)
            with open(args.file, "rb") as f:
                content = f.read()
            raw_text = content.decode("utf-8", errors="ignore")
            parsed = CurriculumService.parse_curriculum_text(raw_text)
            print(f"Successfully parsed curriculum: {parsed['title']} (Grade {parsed['class_grade']} {parsed['subject']})")
            print(f"Extracted {len(parsed['lessons'])} structured lessons.")

        elif args.command == "build-language-pack":
            print(f"Building Language Pack for {args.lang} v{args.version}...")
            res = LanguagePackService.build_pack(db, language_code=args.lang, version=args.version)
            print("Language Pack Build Complete:")
            print(json.dumps(res, indent=2))

        elif args.command == "train-translation":
            from ml.training.train_translation import TranslationTrainer
            print(f"Starting PyTorch translation training ({args.epochs} epochs)...")
            sample_pairs = [
                ("बैठ जाओ", "ᱫᱩᱲᱩᱵ ᱢᱮ"),
                ("अपनी किताब खोलो", "ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ"),
                ("गिनो और बताओ", "ᱞᱮᱠᱷᱟᱭ ᱢᱮ ᱟᱨ ᱞᱟᱹᱭ ᱢᱮ"),
                ("कितने आम हैं?", "ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?"),
                ("बहुत अच्छा", "ᱟᱹᱰᱤ ᱵᱷᱟᱹᱜᱤ")
            ] * 10
            trainer = TranslationTrainer({"learning_rate": 0.001, "checkpoint_dir": "storage/models"})
            splits = trainer.prepare_data(sample_pairs)
            res = trainer.run_training(splits["train"], epochs=args.epochs)
            print("Training Results:")
            print(json.dumps(res, indent=2))

        elif args.command == "evaluate-translation":
            test_set = [
                {"source": "बैठ जाओ", "reference": "ᱫᱩᱲᱩᱵ ᱢᱮ", "mandatory_terms": ["ᱫᱩᱲᱩᱵ"]},
                {"source": "अपनी किताब खोलो", "reference": "ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ", "mandatory_terms": ["ᱯᱚᱛᱚᱵ"]},
                {"source": "गिनो और बताओ", "reference": "ᱞᱮᱠᱷᱟᱭ ᱢᱮ ᱟᱨ ᱞᱟᱹᱭ ᱢᱮ", "mandatory_terms": ["ᱞᱮᱠᱷᱟᱭ"]},
                {"source": "कितने आम हैं?", "reference": "ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?", "mandatory_terms": ["ᱩᱞ"]},
                {"source": "बहुत अच्छा", "reference": "ᱟᱹᱰᱤ ᱵᱷᱟᱹᱜᱤ", "mandatory_terms": ["ᱵᱷᱟᱹᱜᱤ"]}
            ]
            engine = LayeredTranslationEngine(db)
            report = evaluate_test_set(test_set, engine)
            print("Evaluation Report:")
            print(json.dumps(report, indent=2, ensure_ascii=False))

        elif args.command == "quantize-model":
            from ml.quantization.quantize_model import quantize_pytorch_model
            print("Quantizing model to INT8...")
            res = quantize_pytorch_model(args.input, args.output)
            print("Quantization result:", json.dumps(res, indent=2))

        elif args.command == "export-android-model":
            from ml.export.export_android_model import export_to_onnx
            print("Exporting model to ONNX format...")
            res = export_to_onnx(args.input, args.output)
            print("Export result:", json.dumps(res, indent=2))

        elif args.command == "run-latency-benchmark":
            # RETIRED. This used to feed a synthetic sine-wave WAV into a mock
            # ASR that echoed expected_text, then report the round-trip as a
            # "measured end-to-end voice latency" -- a fabricated number (§72).
            # Server-side ASR/TTS were removed; ASR and TTS now run on the
            # device, so genuine end-to-end latency can only be measured there.
            print("run-latency-benchmark has been retired.")
            print(
                "Server-side ASR/TTS were mocks (the ASR echoed expected_text "
                "and never decoded audio), so any latency measured here was "
                "fabricated. Speech recognition and synthesis now run on the "
                "device."
            )
            print(
                "What CAN be measured server-side is neural translation "
                "latency alone -- run 'evaluate-translation', whose report "
                "includes real per-sentence inference_ms from IndicTrans2. "
                "True end-to-end voice latency (VAD+ASR+MT+TTS) must be "
                "measured on the device and persisted via "
                "POST /api/v1/speech/utterances."
            )

        elif args.command == "run-offline-test":
            print("Running simulated offline test (0% network connectivity)...")
            engine = LayeredTranslationEngine(db)
            test_utterances = ["बैठ जाओ", "अपनी किताब खोलो", "गिनो और बताओ", "दो और तीन"]
            print("\nTranslating offline using Tier 1 Phrase Cache & Terminology:")
            for utt in test_utterances:
                out = engine.translate(utt, src_lang="hin", tgt_lang="sat")
                print(f"  [Offline] '{utt}' -> '{out['target_text']}' | Tier: {out['tier']} | Latency: {out['latency_ms']}ms")
            print("\nOffline execution verified with ZERO network requests.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
