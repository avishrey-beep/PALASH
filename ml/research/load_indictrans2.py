"""Load the local IndicTrans2-320M checkpoint under installed libs.

Environment: torch 2.14.0+cpu, transformers 5.16.1. The repo's custom code
was written for transformers 4.34.0.dev0 and hits v5 API changes. We shim only
what inference needs (ONNX stub, tokenizer base seeding, tie_weights kwarg);
no model math is touched.

Public: load_model_and_tokenizer() -> (model, tokenizer, config)
"""
import os
import sys
import types
import importlib.util

_REPO = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "storage", "models", "indictrans2-320m")
)
_PKG = "indtrans2c"


def _install_onnx_stub():
    if "transformers.onnx" in sys.modules:
        return
    onnx = types.ModuleType("transformers.onnx")

    class OnnxConfig:
        pass

    class OnnxSeq2SeqConfigWithPast:
        pass

    onnx.OnnxConfig = OnnxConfig
    onnx.OnnxSeq2SeqConfigWithPast = OnnxSeq2SeqConfigWithPast
    utils = types.ModuleType("transformers.onnx.utils")

    def compute_effective_axis_dimension(*args, **kwargs):
        return args[0] if args else 1

    utils.compute_effective_axis_dimension = compute_effective_axis_dimension
    sys.modules["transformers.onnx"] = onnx
    sys.modules["transformers.onnx.utils"] = utils


def _load_package():
    """Load config/tokenizer/modeling_ as one package (relative imports)."""
    if _PKG in sys.modules:
        return sys.modules[_PKG]
    pkg = types.ModuleType(_PKG)
    pkg.__path__ = [_REPO]
    sys.modules[_PKG] = pkg
    for name in ("configuration_indictrans", "tokenization_indictrans", "modeling_indictrans"):
        spec = importlib.util.spec_from_file_location(
            f"{_PKG}.{name}", os.path.join(_REPO, f"{name}.py")
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[f"{_PKG}.{name}"] = mod
        spec.loader.exec_module(mod)
    return pkg


def _patch_model():
    from indtrans2c.modeling_indictrans import IndicTransForConditionalGeneration

    orig_tie = IndicTransForConditionalGeneration.tie_weights

    def tie_weights(self, *args, **kwargs):
        # v5 calls tie_weights(recompute_mapping=False); upstream is 0-arg and
        # ties only if share_decoder_input_output_embed (False for this ckpt).
        if self.config.share_decoder_input_output_embed:
            return orig_tie(self)
        return None

    IndicTransForConditionalGeneration.tie_weights = tie_weights


def _restore_sinusoidal_positions(model) -> int:
    """Recompute the sinusoidal position tables zeroed out by v5 loading.

    IndicTransSinusoidalPositionalEmbedding builds its table in __init__ and
    registers it with persistent=False, so it is deliberately absent from the
    checkpoint. transformers v5 materializes the module on the meta device and
    then zero-fills every tensor that the checkpoint does not supply -- which
    includes this non-persistent buffer. __init__'s make_weights() result is
    discarded, leaving an all-zero table.

    A zero table means every position gets the same vector: the encoder becomes
    permutation-equivariant (a bag of words) and the decoder loses word order.
    Symptom is fluent-but-scrambled output ("small daily go was when I every go
    was") that still passes script/vocabulary checks, so it is easy to mistake
    for weak translation quality rather than a loading bug.

    VERIFIED: with no missing/unexpected/mismatched keys reported by
    from_pretrained, model.model.encoder.embed_positions.weights was
    (258, 512) all-zero, and PE[pos0] == PE[pos1] exactly.

    Returns the number of position tables rebuilt (expected: 2, enc + dec).
    """
    import torch
    from indtrans2c.modeling_indictrans import IndicTransSinusoidalPositionalEmbedding

    rebuilt = 0
    for module in model.modules():
        if not isinstance(module, IndicTransSinusoidalPositionalEmbedding):
            continue
        w = getattr(module, "weights", None)
        if w is None:
            continue
        # weights was sized num_positions + offset at construction; keep it.
        module.make_weights(w.size(0), module.embedding_dim, module.padding_idx)
        new = module.weights
        if bool(torch.isnan(new).any()) or bool((new == 0).all()):
            raise RuntimeError(
                "sinusoidal position table still degenerate after rebuild"
            )
        rebuilt += 1
    if rebuilt == 0:
        raise RuntimeError("no IndicTransSinusoidalPositionalEmbedding modules found")
    return rebuilt


def load_model_and_tokenizer():
    from transformers.tokenization_utils_base import PreTrainedTokenizerBase

    _install_onnx_stub()
    _load_package()
    _patch_model()

    from indtrans2c.configuration_indictrans import IndicTransConfig
    from indtrans2c.modeling_indictrans import IndicTransForConditionalGeneration
    from indtrans2c.tokenization_indictrans import IndicTransTokenizer

    cfg = IndicTransConfig.from_pretrained(_REPO)

    # Tokenizer: seed v5 base component (creates _special_tokens_map) BEFORE
    # upstream __init__ assigns special tokens.
    class CompatTokenizer(IndicTransTokenizer):
        def __init__(self, *a, **kw):
            PreTrainedTokenizerBase.__init__(self)
            super().__init__(*a, **kw)

    tokenizer = CompatTokenizer(
        src_vocab_fp=os.path.join(_REPO, "dict.SRC.json"),
        tgt_vocab_fp=os.path.join(_REPO, "dict.TGT.json"),
        src_spm_fp=os.path.join(_REPO, "model.SRC"),
        tgt_spm_fp=os.path.join(_REPO, "model.TGT"),
        bos_token="<s>",
        eos_token="</s>",
        pad_token="<pad>",
        unk_token="<unk>",
    )

    model = IndicTransForConditionalGeneration.from_pretrained(_REPO, config=cfg)
    _restore_sinusoidal_positions(model)
    model.eval()
    return model, tokenizer, cfg


if __name__ == "__main__":
    import time

    import torch

    t0 = time.time()
    model, tok, cfg = load_model_and_tokenizer()
    print(f"[load] model+tokenizer in {time.time()-t0:.1f}s; "
          f"params(M)={sum(p.numel() for p in model.parameters())/1e6:.1f}")
    print(f"[cfg] enc_vocab={cfg.encoder_vocab_size} dec_vocab={cfg.decoder_vocab_size} "
          f"share_out_emb={cfg.share_decoder_input_output_embed}")
    pe = model.model.encoder.embed_positions.weights
    print(f"[pos] enc table {tuple(pe.shape)} all_zero={bool((pe == 0).all())} "
          f"PE[0]vs[1] mean|d|={ (pe[0]-pe[1]).abs().mean().item():.6f}")
