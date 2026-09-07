import os
import torch
from ml.training.train_translation import ToySeq2Seq

def export_to_onnx(model_path: str, output_onnx_path: str) -> dict:
    """
    Exports trained PyTorch model to ONNX format with dynamic axis support
    for ONNX Runtime Mobile inference on Android.
    """
    model = ToySeq2Seq()
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    dummy_input = torch.randint(0, 1000, (1, 10), dtype=torch.long)
    os.makedirs(os.path.dirname(output_onnx_path), exist_ok=True)

    torch.onnx.export(
        model,
        dummy_input,
        output_onnx_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input_tokens"],
        output_names=["logits"],
        dynamic_axes={
            "input_tokens": {0: "batch_size", 1: "sequence_length"},
            "logits": {0: "batch_size", 1: "sequence_length"}
        }
    )

    size_bytes = os.path.getsize(output_onnx_path)
    return {
        "format": "ONNX",
        "output_path": output_onnx_path,
        "size_bytes": size_bytes,
        "opset_version": 14,
        "target_runtime": "ONNX Runtime Mobile (Android 9+ / ARM64)"
    }

if __name__ == "__main__":
    res = export_to_onnx("storage/models/translation_checkpoint.pt", "storage/models/translation_model.onnx")
    print("Export Result:", res)
