# Audit — Pre-existing Implementation in This Repository

**Audit date:** 2026-09-04
**Auditor scope:** all 5,904 lines of Python found in this working tree prior to any changes.
**Verdict: the pre-existing ML/AI layer is a mockup. It must be replaced, not extended.**

The backend/API/database layer is largely genuine and salvageable. The ML layer —
translation, ASR, TTS, training, and the benchmark reports built on top of them —
does not do the work it claims to do. Every finding below was verified by execution,
not by reading alone.

---

## 1. Summary table

| Component | File | Claim made by the code | Reality | Salvageable |
|---|---|---|---|---|
| ASR | `ml/asr/engine.py` | "Streaming ASR … measuring time to first partial result" | Returns the ground-truth text handed to it via `expected_text`; never decodes audio | **No — delete** |
| TTS | `ml/tts/engine.py` | "Text-to-Speech Engine for Indigenous Indian Languages" | Emits a 3-harmonic sine tone whose only input is `len(text)` | **No — delete** |
| Translation (neural path) | `ml/translation/model_wrapper.py:48-55` | ONNX neural inference | Returns the literal string `"[ONNX Translated] " + input` | **No — delete** |
| Translation (fallback) | `ml/translation/model_wrapper.py:57-108` | "Syntactic & Glossary-Augmented Rule Generation" | Word-by-word dictionary substitution — the exact mechanism §46 forbids | **No — delete** |
| Training | `ml/training/train_translation.py` | "Reproducible ML Training Pipeline" | Trains a GRU to autoencode character ordinals of the *first word* only | **No — delete** |
| Android RAM benchmark | `benchmarks/benchmark_android_memory.py` | 4 components labelled `"type": "MEASURED"` | Hardcoded literals; no measurement occurs anywhere in the file | **No — delete** |
| Cache experiment | `benchmarks/run_cache_experiment.py` | Latency + RAM comparison of 3 pipelines | Times the fake components; RAM values hardcoded as `simulated_ram_mb` | **No — rewrite** |
| Auth / RBAC | `backend/app/services/auth_service.py` | JWT + hashing + roles | Appears genuine — pending security review | **Likely yes** |
| DB schema / models | `backend/app/models/*` | Relational schema | Appears genuine — pending schema review | **Likely yes** |
| API surface | `backend/app/api/v1/**` | Versioned REST API | Appears genuine — pending review | **Likely yes** |

The 20 tests in `backend/tests/` all pass. **They pass because they assert the
mock's behaviour.** A green suite here is not evidence of function.

---

## 2. Evidence

### 2.1 ASR does not read the audio (`ml/asr/engine.py`)

`transcribe_chunked()` accepts an `expected_text` parameter and emits it token by
token as "partial results" (`engine.py:63-74`). The audio is touched only for a
frame-energy check that is bypassed for every chunk after the first
(`if energy >= 0.005 or chunk_idx > 0`, `engine.py:72`).

Three acoustically unrelated inputs, same `expected_text`:

```
digital silence  -> 'तीन और दो मिलाकर कितने होते हैं'  conf=0.91
440Hz tone       -> 'तीन और दो मिलाकर कितने होते हैं'  conf=0.91
white noise      -> 'तीन और दो मिलाकर कितने होते हैं'  conf=0.91
```

With no `expected_text`, white noise transcribes to a hardcoded default
(`engine.py:63`, `engine.py:88`):

```
white noise      -> 'गिनो और बताओ कितने'
```

`confidence` is the literal `0.91` (`engine.py:94`). It is not derived from
anything. Consequently every "ASR latency", "time to first partial", and WER
number this component could produce is meaningless.

### 2.2 TTS emits a tone, and depends only on text *length* (`ml/tts/engine.py`)

`generate_synthetic_speech_wav()` sums three sine waves (`engine.py:48-52`). The
only text-derived quantity is duration: `len(text) * 0.08` (`engine.py:102`).

Two unrelated strings of equal length produce **byte-identical audio**:

```
sha256(Santali "ᱫᱩᱲᱩᱵ ᱢᱮ") : 94296b804847c978b55f303259c69f26
sha256(literal "XXXXXXXX")  : 94296b804847c978b55f303259c69f26
IDENTICAL BYTES: True
```

Spectral analysis of a committed artifact, `storage/audio/sat_1366820360.wav`:

```
16 kHz mono, 0.80 s; zero-crossing rate => ~110 Hz dominant
perfectly periodic (fixed 220 Hz fundamental + harmonics)
```

This is a musical tone. It carries no phonetic content and is not intelligible as
speech in any language. The seven `storage/audio/sat_*.wav` files are all instances
of this generator.

### 2.3 The "neural" translation branch returns a placeholder string

`model_wrapper.py:48-55` — when a model *is* loaded, the function never invokes
`self.session`. It returns an f-string:

```
output: '[ONNX Translated] कितने आम हैं'
confidence: 0.82
```

### 2.4 The fallback is word-by-word substitution — explicitly forbidden by §46

`model_wrapper.py:64-95` maps individual Hindi tokens to Santali morphemes and
joins them. Untranslated tokens pass through verbatim, producing mixed-script
output:

```
'कितने आम हैं'         -> 'ᱛᱤᱱᱟᱹᱜ आम ᱠᱟᱱᱟ ᱠᱚ'      conf=0.80
'यह किताब मेज पर है'   -> 'ᱱᱚᱣᱟ किताब मेज ᱨᱮ ᱠᱟᱱᱟ'  conf=0.77
```

Beyond violating §46, note the `confidence` values: 0.80 and 0.77 are produced by
`0.50 + 0.45 * (translated_tokens / total_tokens)` (`model_wrapper.py:101`). This
is a coverage ratio being presented as a confidence score. §52 explicitly warns
against exactly this.

The correctness of the Santali glossary entries themselves is **NOT MEASURED** —
no verified reference exists in the repository, and no native-speaker review is
recorded.

### 2.5 Training trains nothing related to translation

`train_translation.py:76-77`:

```python
indices = torch.tensor([[min(ord(c), 1999) for c in src_tokens[0]]], ...)
target  = torch.tensor([[min(ord(c), 1999) for c in src_tokens[0]]], ...)
```

Input and target are the same tensor, built from the characters of `src_tokens[0]`
— the **first word of the source sentence only**. The target side of every
training pair is discarded entirely. The model is a character autoencoder over one
word. Its decreasing loss is real and completely uninformative.

### 2.6 Benchmarks label hardcoded constants as `MEASURED`

`benchmark_android_memory.py:34-70` declares four components with
`"type": "MEASURED"` and fixed numbers (e.g. `"ram_usage_mb": 14.8`,
`"load_time_ms": 12.0`). The file performs no measurement of any kind — it
contains no timing calls, no memory introspection, and imports nothing that
could measure. It then prints
`"FEASIBLE AND SAFE FOR PRODUCTION"`.

`run_cache_experiment.py:124,130,136` hardcodes `simulated_ram_mb` at 580 / 15 / 25
and concludes the cache is `"indispensable for production classroom feasibility"`.
The latency it compares is the latency of the fake components in §2.1–2.4.

This directly violates §72. It is the most serious class of finding here, because
the numbers are downstream-consumable and read as validation.

### 2.7 Functional defect: cache identifiers are not deterministic

`ml/tts/engine.py:87` derives the audio cache filename from `abs(hash(text))`.
Python randomises `str` hashing per process (PEP 456). Same input, two processes:

```
process 1: 8251928901
process 2: 7284017241
```

§12 requires "Cache keys should be deterministic" and §27 "deterministic
identifiers so assets can be reused". This breaks both: the audio cache can never
hit after a restart, and re-synthesises + writes a new file each run. This is the
origin of the accumulated stray `sat_*.wav` files.

**Fix for the replacement:** SHA-256 over NFC-normalised text plus explicit
language-pair and model-version fields.

---

## 3. Disposition

**Delete outright** — cannot be repaired, and their presence is actively
misleading:

```
ml/asr/engine.py
ml/tts/engine.py
ml/translation/model_wrapper.py
ml/training/train_translation.py
benchmarks/benchmark_android_memory.py
storage/audio/sat_*.wav                     (tone artifacts)
storage/exports/*.json                      (reports derived from the above)
```

**Rewrite against real models:** `benchmarks/run_cache_experiment.py`,
`benchmarks/run_latency_benchmark.py`, `ml/evaluation/*`.

**Review then keep:** `backend/app/**` (auth, models, API, services),
`backend/tests/**` — but every ML-touching assertion must be re-grounded, and the
security review in §36 has not yet been performed.

**Retain as a genuine asset:** the glossary/phrase *structure* and the Hindi
source-side classroom corpus are useful. The Santali target side must be treated
as `unverified` per §23 until a bilingual reviewer approves it — never as ground
truth.

---

## 4. Why this matters beyond tidiness

A mockup that reports `MEASURED`, prints `FEASIBLE AND SAFE FOR PRODUCTION`, and
ships a passing test suite is more dangerous than no implementation, because it
answers the project's central question — *is this feasible on a 2 GB device?* —
with fabricated evidence. The real answer requires real models, and is developed
in `feasibility-phase1.md`.
