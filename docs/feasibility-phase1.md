# Phase 1 — Feasibility, Resources, and Model Selection

**Date:** 2026-09-04
**Status:** Phase 1 partially complete. Blocking item identified (§8).
**Evidence discipline:** every row is tagged `MEASURED`, `VERIFIED` (from an
authoritative machine-readable source), `ESTIMATED`, or `NOT MEASURED`. Nothing
here is asserted from recollection.

Measurement host (all `MEASURED` latency/RAM figures):
Windows 11, x86-64, 16 logical CPUs, 24 GB RAM, Python 3.14.6, torch 2.14.0+cpu,
**CPU inference only** (the RTX 4060 is unusable — the installed torch is a CPU
build). This host is **much faster than the 2 GB Android target**. Desktop numbers
are therefore a *lower bound* on device latency.

---

## 1. The finding that reframes the project

The three candidate languages do **not** have symmetric resource coverage, and no
single one has all three modalities available under a permissive licence.

| Modality | Santali (`sat`) | Ho (`hoc`) | Mundari (`unr`) |
|---|---|---|---|
| **Machine translation** | ✅ IndicTrans2 (MIT, Ol Chiki) · ✅ NLLB-200 (CC-BY-NC) | ❌ none pretrained | ⚠️ IndicTrans2 `unr_Deva` — undocumented, `MEASURED` working |
| **ASR** | ✅ **3× Apache-2.0 ungated** + MMS adapter | ✅ MMS adapter (CC-BY-NC) | ✅ MMS adapter (CC-BY-NC) |
| **TTS** | ❌ **nothing exists** | ✅ MMS-TTS-hoc (CC-BY-NC) | ✅ MMS-TTS-unr (CC-BY-NC) |
| Scheduled language (8th Sch.) | ✅ yes | ❌ no | ❌ no |
| Official script | Ol Chiki | Warang Citi / Latin / Deva | Devanagari |

`VERIFIED` — evidence for each cell:

* **MT.** `facebook/nllb-200-distilled-600M` tokenizer exposes 202 language tags;
  Santali appears as `sat_Beng`; **no `hoc_*` or `unr_*` tag exists**. FLORES-200's
  table lists only `sat_Olck` among the three.
* **MT — Mundari, correction.** An earlier draft of this table said Mundari had
  "none pretrained", inferred from IndicTrans2's *documented* language set (the 22
  scheduled languages + English, which excludes Mundari). That inference was wrong.
  Reading the shipped artefacts directly: `unr_Deva` is present in
  `tokenization_indictrans.py`'s `LANGUAGE_TAGS`, and in `dict.SRC.json` at id
  121515 — a real, non-`<unk>` embedding row. `MEASURED`: `hin_Deva → unr_Deva`
  produced fluent Devanagari output on 6/6 control sentences (e.g. `अपनी किताब खोलो।`
  → `अपनी पुस्तक खोलिए।`). **`NOT MEASURED`:** whether that output is *Mundari* or
  merely Hindi — the outputs are close to Hindi and no Mundari speaker has reviewed
  them; the tag is undocumented and may be undertrained. Treat as a lead, not a
  capability. `hoc_*` (Ho) is genuinely absent from both the tag set and the dict.
* **ASR.** `facebook/mms-1b-all` ships **1,125** language adapters; `sat`, `hoc`,
  and `unr` are all present (verified from the repo file listing).
  `openai/whisper` covers 100 languages — **none** of the three.
* **TTS.** `facebook/mms-tts-hoc` and `facebook/mms-tts-unr` exist (291 MB each,
  CC-BY-NC-4.0). **`facebook/mms-tts-sat` returns 404** — verified, as does
  `facebook/mms-tts-sat-Olck`. A Hub-wide search over five spellings
  (`santali`, `santhali`, `ol-chiki`, `olchiki`, `sat_Olck`) returned **60 distinct
  models and not one TTS/VITS model for Santali**. No permissively licensed Indic
  TTS covers any of the three:
  `ai4bharat/indic-parler-tts` (Apache-2.0) = 18 languages, `ai4bharat/IndicF5`
  (MIT) = 11, `ai4bharat/indic-seamless` (CC-BY-NC) = 13 — all exclude
  `sat`/`hoc`/`unr`.

### Consequence

The two translation directions have **very different** feasibility:

```
Hindi speech -> Santali speech          Santali speech -> Hindi speech
  Hindi ASR      easy, MIT                Santali ASR    available (NC / Apache FT)
  hin->sat MT    available                sat->hin MT    available
  Santali TTS    DOES NOT EXIST  <-- ✗    Hindi TTS      easy, Apache-2.0/MIT
```

For a **primary** classroom this is severe. Class 1–2 children are pre-literate,
and the Hindi-medium teacher cannot read Ol Chiki. Rendering Santali as *text* is
therefore of low pedagogical value — **spoken output is the product**. The single
hardest blocker in this project is Santali speech synthesis, and it is not a
tuning problem: no model exists.

---

## 2. `MEASURED` — Hindi → Santali with NLLB-200-distilled-600M

Reproduce: `python -m ml.research.probe_nllb_santali --tgt-lang sat_Beng`
Raw output: `benchmarks/results/phase1_nllb_hin_satBeng.json`

Corpus: 22 real Hindi primary-classroom utterances across 8 categories
(commands, instructions, numeric questions, wh-questions, praise, named
entities, long sentences, assessment prompts).

### 2.1 Script — a mislabelled tag, resolved

`MEASURED`. The tag is named `sat_Beng` (Bengali script), but the model emits
**Ol Chiki**:

| Script of output | mean letter ratio | outputs ≥0.9 |
|---|---|---|
| Ol Chiki (`Olck`) | **1.000** | **22/22** |
| Bengali (`Beng`) | 0.000 | 0/22 |
| Devanagari (source) | 0.000 | 0/22 |

So NLLB-200's Santali tag is misnamed in the released checkpoint; the underlying
training data was Ol Chiki. **NLLB-200 is a usable Ol Chiki Santali MT model**,
which contradicts what the tag name implies. Anything built on this must pin the
tag `sat_Beng` and document that it yields `sat_Olck` content.

### 2.2 Latency — the <3 s target is already missed on desktop

`MEASURED`, fp32, CPU, beam=4, warm-up excluded:

| | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| **Translation only (ms)** | **3376** | 6399 | 7545 | 9707 | 9707 |

By category:

| Category | n | p50 (ms) | max (ms) |
|---|---|---|---|
| praise (2–3 words) | 2 | 1789 | 1814 |
| command_short | 4 | 1826 | 2976 |
| question_wh | 2 | 2385 | 3376 |
| instruction | 3 | 3391 | 3576 |
| question_number | 3 | 3394 | 5574 |
| named_entity | 2 | 3792 | 4150 |
| assessment | 3 | 3780 | 4221 |
| **longer** | 3 | **7545** | **9707** |

**The <3 s end-to-end budget is exceeded by the translation stage alone, at p50,
on a 16-thread desktop CPU** — before any ASR, TTS, or audio I/O. ASR and TTS
still have to fit in the same 3 s.

### 2.3 Memory

`MEASURED`: RSS 1,587 MB after load; **peak 3,528 MB** during beam search.
`COMPUTED`: fp32 weights = 2,460 MB for 615,073,792 parameters (measured count).

Peak RSS alone is **~1.7× the entire 2 GB device RAM**, and ~7× the 512 MB
`largeHeap` Android ceiling. This model cannot run on target hardware in fp32,
by a wide margin. `NOT MEASURED`: int8-quantised footprint (see §6).

*Load time is reported as 368 s in the JSON but that figure is **contaminated** by
the tail of the 2.46 GB first-run download and must not be cited. Warm-cache load
time is `NOT MEASURED`.*

### 2.4 Quality — not classroom-safe

Two objective, speaker-independent checks (no Santali knowledge required):

* **Structural sanity — passes.** 0/22 degenerate or empty; 0/22 copied the
  Devanagari source through.
* **Semantic collapse — fails.** 22 distinct inputs produced only 21 distinct
  outputs. `बैठ जाओ।` ("sit down") and `खड़े हो जाओ।` ("stand up") produce
  **byte-identical** Santali: `ᱡᱟᱱᱟᱢ ᱢᱮ ᱾`. Two opposite, extremely
  high-frequency classroom commands are indistinguishable in the output.

Round-trip Hindi→Santali→Hindi, chrF (sacrebleu) vs the original Hindi —
a **weak** signal only, since it cannot separate a bad forward hop from a bad
back hop:

| | mean | median | min | max |
|---|---|---|---|---|
| round-trip chrF | **28.6** | — | 12.9 | 57.3 |

Illustrative round-trips (these motivate, but do not prove, a quality problem):

| Hindi source | round-tripped Hindi | issue |
|---|---|---|
| बहुत अच्छा। ("very good") | बहुत बुरा। ("very bad") | **polarity inverted** |
| राजू ने दो रोटी खाईं। | राजा ने दो रोटियां खाईं। | named entity Rajū → Rājā |
| सही उत्तर पर गोला लगाओ। | सही उदाहरण के लिए उदाहरण के लिए | degenerate |
| मिलान करो और जोड़े बनाओ। | मुफ़्त रहें और जुड़ें। | instruction lost |
| यह कौन सा रंग है? | यह किनारा क्या है? | content word wrong |
| तुम्हारा नाम क्या है? | आपका नाम क्या है? | ✅ preserved |

`NOT MEASURED` — true forward adequacy of the Santali. Establishing it requires
(a) BLEU/chrF against the **CC-BY-4.0 IN22 / FLORES+ Santali references** (§4),
and (b) native-speaker review (§7). Apparent verb confusions in the raw output
are noted in the JSON but are **explicitly not claimed as findings** here, because
the auditor is not a Santali speaker.

**Interim conclusion (NLLB-200-600M):** correct script, but too slow (p50 3.4 s
desktop), far too large (3.5 GB peak), licensed CC-BY-NC-4.0 (non-commercial —
unsuitable for a government deployment), and demonstrably collapsing on core
classroom commands. **Not the production model.** It remains useful as a
research baseline and as a server-side teacher-aid under its NC terms.

---

## 2A. `MEASURED` — Hindi → Santali with IndicTrans2-320M (production candidate)

Token obtained; `ai4bharat/indictrans2-indic-indic-dist-320M` (MIT) downloaded
and measured. Instrument: `ml/research/probe_indictrans2_santali.py`, reusing the
NLLB probe's corpus, generation settings and analysis functions so the two are
directly comparable. Report: `benchmarks/results/phase1_indictrans2_hin_sat.json`.

Host: x86-64 dev machine, CPU, fp32, torch 2.14.0+cpu, `num_beams=4`,
`max_new_tokens=96`, warm-up excluded, `use_cache=False`. **This is not the
Android target; no on-device number is claimed.**

| Metric | NLLB-600M | IndicTrans2-320M |
|---|---|---|
| Licence | CC-BY-NC-4.0 (non-commercial) | **MIT** |
| Params (measured) | 615 M | **320,861,184** |
| Latency p50 / p90 / p95 | 3376 / — / — ms | **1158 / 2214 / 2666 ms** |
| Slowest single sentence | — | 3335 ms (1 of 22 over 3 s) |
| RSS after load / peak | 1587 / 3528 MB | **474 / 1398 MB** |
| Dominant output script | Ol Chiki (tag mislabelled `sat_Beng`) | Ol Chiki (tag `sat_Olck`, correct) |
| Mean Ol Chiki char ratio | — | **0.986** |
| Outputs ≥0.9 target script | — | 20 / 22 |
| Degenerate | — | **0 / 22** |
| Source copied | — | 0 / 22 |
| Output collapse | sit-down/stand-up byte-identical | **none** — 22 inputs → 22 distinct outputs |
| Round-trip chrF (weak signal) | — | mean 40.02 |

IndicTrans2 is **~2.9× faster at p50, ~2.5× smaller in peak RSS, and permissively
licensed**. It clears the <3 s target at p95 on this host and does not collapse.
It is the production candidate.

### 2A.1 Two real defects, both `MEASURED`

**(a) Short classroom commands are the weakest category — and they matter most.**
Round-trip chrF by category (weak signal, but the pattern is consistent):

| Category | n | chrF mean | chrF min | p50 ms |
|---|---|---|---|---|
| `command_short` | 4 | **17.6** | **4.0** | 809 |
| `assessment` | 3 | 25.3 | 6.6 | 1568 |
| `question_number` | 3 | 39.8 | 34.4 | 1188 |
| `longer` | 3 | 39.4 | 20.1 | 2666 |
| `named_entity` | 2 | 40.6 | 28.4 | 1323 |
| `instruction` | 3 | 46.1 | 43.0 | 1458 |
| `praise` | 2 | 59.9 | 36.7 | 783 |
| `question_wh` | 2 | **78.6** | 57.2 | 727 |

Worst cases round-trip to unrelated meanings: `बैठ जाओ।` ("sit down") → back
`इसका उपयोग करें।` ("use it"); `खड़े हो जाओ।` ("stand up") → back `स्थापित करें।`
("establish/install"); `मिलान करो और जोड़े बनाओ।` ("match and make pairs") → back
`संपर्क करें और संपर्क करें।` ("contact and contact").

`HYPOTHESIS — NOT MEASURED`: the model card states this checkpoint was "adapted
after stitching Indic-En Distilled 200M and En-Indic Distilled 200M", i.e. it
pivots through English. "stand up" → "establish" and "match" → "contact" are
textbook English polysemy errors, which is consistent with a pivot losing the
imperative register on inputs too short to disambiguate. The pivot itself has
not been instrumented, so this remains a hypothesis.

**Architectural consequence:** this is precisely the register a teacher uses most,
and it is the register the model is worst at. It directly justifies §62 Tier 1
(precomputed, native-speaker-verified phrases) rather than treating it as an
optimisation. Classroom commands must not be model-generated at runtime.

**(b) Cross-language contamination into Meitei Mayek — 2 / 22 outputs.**
The model substituted Manipuri words for Santali ones, on the content word
in both cases:

- `यह कौन सा रंग है?` → `ᱱᱚᱶᱟ ᱫᱚ ᱪᱮᱫ ꯃꯆꯨ?` — `ꯃꯆꯨ` (*machu*) is Manipuri for
  "colour" (Mtei ratio 0.182)
- `इस पेड़ पर तीन चिड़ियाँ बैठी हैं।` → `… ᱯᱮᱭᱟ ꯎꯆꯦꯛ ᱠᱚ …` — `ꯎꯆꯦꯛ` (*uchek*) is
  Manipuri for "bird" (Mtei ratio 0.122)

These pass a naive "is it Ol Chiki?" check at 82–88%. Any output validator must
reject **foreign-script contamination**, not merely confirm majority target
script. The probe now measures the ratio for every registered script, so this
was caught automatically.

### 2A.2 `sat_Olck` postprocessing — hazard downgraded, not eliminated

`IndicProcessor` maps `sat_Olck` → ISO `"or"` (Odia) for its output
transliteration step, and `indic-nlp-library` 0.92 has **no Ol Chiki script
range at all** (`langinfo.SCRIPT_RANGES` covers 16 scripts, Ol Chiki not among
them). Initially assessed as fatal under §61.

`MEASURED` correction: for `sat_Olck` the model emits **Ol Chiki directly**
(raw decoder output was already correct in 6/6 control sentences), and
transliterating Ol Chiki text with a Devanagari→Odia map is a no-op because no
character is in the Devanagari range. So the pipeline does produce Ol Chiki.

It remains a **latent hazard**: any Devanagari fragment leaking into a Santali
output is silently converted to Odia rather than left visible. This was observed
directly while the harness was broken. Mitigation: `olck_mode="raw"` in
`ml/translation/indictrans2_processor.py` skips the step, and the output
validator must flag Orya characters in `sat_Olck` output.

---

## 3. Model candidates — `VERIFIED` metadata

All rows read from the Hugging Face API (licence, gating, byte size), not from
memory. "Gated `auto`" = instant approval after accepting terms, but **a token is
still required**.

### Translation

| Model | Langs incl. | Params | Repo size | Licence | Gated | Android viability |
|---|---|---|---|---|---|---|
| `ai4bharat/indictrans2-indic-indic-dist-320M` | hin↔sat (Ol Chiki), direct | 0.32 B | 2,581 MB (1,284 MB safetensors) | **MIT** | auto | int8 ≈ 320 MB — plausible, `NOT MEASURED` |
| `ai4bharat/indictrans2-en-indic-dist-200M` | eng→sat | 0.2 B | 2,205 MB (1,098 MB) | **MIT** | auto | int8 ≈ 200 MB |
| `ai4bharat/indictrans2-indic-en-dist-200M` | sat→eng | 0.2 B | 1,835 MB (913 MB) | **MIT** | auto | int8 ≈ 200 MB |
| `facebook/nllb-200-distilled-600M` | hin→sat via `sat_Beng` | 0.615 B `MEASURED` | 2,460 MB | CC-BY-NC-4.0 | no | ✗ 3.5 GB peak `MEASURED` |
| `facebook/nllb-200-distilled-1.3B` | same | 1.3 B | 5,483 MB | CC-BY-NC-4.0 | no | ✗ |

**`ai4bharat/indictrans2-indic-indic-dist-320M` is the production candidate**:
MIT-licensed, native Ol Chiki, and the *only* option offering direct Hindi↔Santali
without an English pivot (a pivot doubles latency and compounds error).

### ASR

`VERIFIED`. **Methodological note:** licences below were read via
`HfApi.model_info()`, not from search-result listings. `list_models()` does not
reliably populate `card_data`, so a search listing reports `license=None` even for
Apache-2.0 repos. An earlier pass over search listings alone would have wrongly
excluded three usable models under §60.

| Model | Langs | Size | Licence | Gated | Notes |
|---|---|---|---|---|---|
| `ai4bharat/indic-conformer-600m-multilingual` | 22 Indic | 2,557 MB | **MIT** | auto | Santali coverage `NOT VERIFIED` — card lists no languages |
| `facebook/mms-1b-all` | **1,125** adapters incl. `sat`,`hoc`,`unr` | 29,186 MB | CC-BY-NC-4.0 | no | covers all three; NC licence |
| `thunderboltc/whisper-small-santali-ol-chiki` | `sat` | 967 MB | **Apache-2.0** | no | outputs **Ol Chiki**; quality `NOT MEASURED` |
| `DipsankarSinha/Santali_ASR-Model_KIIT2024_v1` | `sat` | 1,262 MB | **Apache-2.0** | no | quality `NOT MEASURED` |
| `shoibo/whisper_small_santali_ipa` | `sat` | 967 MB | **Apache-2.0** | no | outputs **IPA** — needs IPA→Ol Chiki mapping |
| `ai4bharat/indicwav2vec-hindi` | `hin` | 1,262 MB | **Apache-2.0** | auto | Hindi side |
| `Tejxl/IndicConformer-Santali` | `sat` | 939 MB | **none** | no | unusable under §60 |
| `Piranav/whisper-large-v2-santali` | `sat` | 0 MB | **none** | no | no licence *and* no weights |
| Whisper (all sizes) | 100 | — | MIT | no | **excludes all three** |

Three independent Apache-2.0 Santali ASR checkpoints exist and are ungated. This
makes the **Santali→Hindi direction measurable immediately, with no token**.

### Supporting models (not ASR/MT/TTS, but directly useful)

| Model | Purpose | Size | Licence |
|---|---|---|---|
| `goldfish-models/sat_olck_full` | Santali monolingual LM — fluency scoring of MT output, and a pretrained text frontend for a future Santali TTS | 508 MB | **Apache-2.0** |
| `goldfish-models/sat_olck_5mb` | smaller variant | 163 MB | **Apache-2.0** |
| `prachuryyaIITG/SampurNER_Santali_IndicBERTv2` | Santali NER — entity preservation | 1,118 MB | **MIT** |

The NER model addresses a **measured** defect: NLLB corrupted the name राजू → राजा
(§2.4). Named-entity masking before translation and restoration after is the
standard fix, and a permissively licensed Santali NER model makes it available.

### TTS

| Model | Langs | Size | Licence | Covers target? |
|---|---|---|---|---|
| `ai4bharat/indic-parler-tts` | 18 | 3,763 MB | Apache-2.0 | ❌ no sat/hoc/unr |
| `ai4bharat/IndicF5` | 11 | 1,406 MB | MIT | ❌ |
| `ai4bharat/indic-seamless` | 13 | 6,023 MB | CC-BY-NC-4.0 | ❌ |
| `facebook/mms-tts-hoc` | Ho | 291 MB | CC-BY-NC-4.0 | ✅ Ho only |
| `facebook/mms-tts-unr` | Mundari | 291 MB | CC-BY-NC-4.0 | ✅ Mundari only |
| **Santali TTS** | — | — | — | ❌ **none exists, any licence** |

---

## 4. Dataset inventory — `VERIFIED` licences

Read from the Hub API. `S`/`H`/`M` = declared coverage of Santali / Ho / Mundari.

### Usable, permissive (commercial-safe)

| Dataset | Licence | Cover | Content | Use |
|---|---|---|---|---|
| **`google/smol`** | **CC-BY-4.0**, ungated | **S H M** | professionally translated | see §4.1 — best single asset |
| `ai4bharat/IN22-Gen` | CC-BY-4.0, **gated `auto`** | S – – | 23-lang eval benchmark | **held-out test set** |
| `ai4bharat/IN22-Conv` | CC-BY-4.0, **gated `auto`** | S – – | conversational eval | **held-out test set** |
| `openlanguagedata/flores_plus` | CC-BY-SA-4.0 | S – – | 205-lang eval | **held-out test set** |
| `facebook/flores` | CC-BY-SA-4.0 | S – – | FLORES-200 | eval |
| `sil-ai/bloom-lm` | ⚠ **mixed, see below** | S – M | **children's storybooks**, 424 langs | on-domain for primary FLN |
| `lbourdois/panlex` | **CC0** | S H M | lexicon, 6,152 langs | glossary seed |
| `ai4bharat/Bhasha-Abhijnaanam` | **CC0** | S – – | language ID | LID guard |
| `HPLT/HPLT2.0_cleaned` | **CC0** | S – – | monolingual, 186 langs | LM / back-translation |
| `HuggingFaceFW/fineweb-2` | ODC-BY | S – – | monolingual, 1,813 langs | back-translation |
| `coild-aikosh/Education_v2` | CC-BY-4.0 | S – – | **education domain** | on-domain (gating: manual) |
| `wikimedia/wikipedia` | CC-BY-SA-3.0 | S – – | sat Wikipedia | monolingual |

⚠ **`sil-ai/bloom-lm` is not uniformly CC-BY-4.0.** `dataset_info` reports a
**list** of six licences: `cc-by-4.0`, `cc-by-nc-4.0`, `cc-by-nd-4.0`,
`cc-by-sa-4.0`, `cc-by-nc-nd-4.0`, `cc-by-nc-sa-4.0`. Licensing is therefore
**per-book**, and the corpus includes **NoDerivatives (ND)** material, which
cannot lawfully be used to train a model. It must be filtered per record before
any use, not consumed wholesale. It is also `gated: auto`.

**The Santali evaluation sets are gated.** `IN22-Gen` and `IN22-Conv` both require
an accepted licence and a token. Without one, **no BLEU/chrF against real Santali
references can be computed at all** — only FLORES+ remains, and the §6 quality
items stay open. This makes the token blocker (§8) an evaluation blocker, not just
a model-download blocker.

### Restricted — non-commercial

`ltrciiith/bhashik-parallel-corpora-generic` (CC-BY-NC-4.0, S H),
`project-boli/ho` (CC-BY-NC-SA-4.0, Ho), `sil-ai/bloom-captioning` (CC-BY-NC-4.0).

### Excluded — **no licence declared**, unusable under §60

Confirmed via `dataset_info` / `model_info` (not search listings):
`XKaab/ASR-santali_100hrs`, `XKaab/ASR-Santali_4hrs` (a nominal 100 h of Santali
speech — the most tantalising asset found, and **not usable** without a licence),
`Tejxl/IndicConformer-Santali`, `Piranav/whisper-large-v2-santali`,
`thunderboltc/nllb-200-santali-ipa`, `riyakumari77/santali-english-translator`,
`AD2206/santali-nllb-adapter`, `aiswarya9302/*` (a family of
`indictrans2-eng-sat-olchiki` fine-tunes), `Murmu722/*`,
`anandohm/Ol-chiki_Santhali` (declares literally `unknown`).

This is a real cost: the largest apparent Santali speech corpus cannot be used, and
neither can the several existing Santali IndicTrans2 fine-tunes.
Action: contact the uploaders for terms; do not use meanwhile.

### 4.1 What is actually inside `google/smol` — `VERIFIED` by file listing

| Path | Size | Meaning |
|---|---|---|
| `gatitos/en_sat.jsonl` | 473 KB | En↔Santali **lexicon**, Ol Chiki |
| `gatitos/en_sat-Latn.jsonl` | 399 KB | same, romanised |
| `smolsent/en_sat.jsonl` | 549 KB | En↔Santali **sentences**, Ol Chiki |
| `smoldoc/en_hoc-Wara.jsonl` | 5,324 KB | En↔Ho **documents**, **Warang Citi script** |
| `smoldoc/en_unr-Deva.jsonl` | 2,979 KB | En↔Mundari **documents**, Devanagari |

Two consequences:

1. **Everything is English-paired, not Hindi-paired.** Hindi↔Santali supervision
   must be built by pivoting through English or by aligning against abundant
   En↔Hindi data. This is a genuine data-engineering task, not a download.
2. **Ho appears in Warang Citi**, while `facebook/mms-tts-hoc`'s expected input
   orthography is `NOT VERIFIED`. If they disagree, the Ho text data and the Ho
   TTS model cannot be combined without a transliteration layer.

---

## 5. Recommended first target language: **Santali**

Justification from the evidence above, not from convenience:

1. Only language of the three with a **pretrained MT model** — and under **MIT**
   (IndicTrans2), with **native Ol Chiki**.
2. Only one with **CC-BY-4.0 held-out evaluation sets** (IN22-Gen, IN22-Conv,
   FLORES+). Without these, §48's metrics cannot be computed honestly at all.
3. Largest permissive data pool (§4) and an official, standardised orthography
   (Ol Chiki) that matches Jharkhand Santali textbooks.
4. A Scheduled Language, so future government resourcing is plausible.

**Accepted cost:** Santali is the one language of the three with **no TTS at all**.
This is the deliberate trade — MT+ASR+evaluation are the parts that cannot be
bootstrapped locally, whereas a small single-speaker TTS *can* be, and a verified
pre-recorded phrase bank delivers classroom value from day one (§62 Tier 1).

Choosing **Ho** instead would invert the problem: TTS exists (CC-BY-NC), but MT
would have to be trained from ~5 MB of English-paired document data with no
held-out benchmark — an unmeasurable system. That is the worse engineering bet.

The architecture must keep language a **configuration value**, never a code path,
so Ho and Mundari can be added when their MT gap closes.

---

## 6. Open, must-measure items — currently `NOT MEASURED`

| # | Item | Why it decides the project |
|---|---|---|
| 1 | IndicTrans2 320M int8 latency + RAM, CPU | Whether *any* on-device dynamic MT is viable |
| 2 | IndicTrans2 hin→sat chrF/BLEU vs IN22 + FLORES+ | The only honest quality number available |
| 3 | Same, on a real Android 9 / 2 GB device | §43/§44 acceptance; desktop ≠ device |
| 4 | Santali ASR WER — 3 Apache-2.0 candidates | Whether the Santali→Hindi direction works. **Unblocked, no token needed** |
| 5 | Hindi ASR WER + latency (IndicConformer MIT) | The teacher's input path |
| 6 | Does `ai4bharat/indic-conformer-600m` include `sat`? | MIT ASR vs falling back to CC-BY-NC MMS |
| 7 | MMS-TTS-hoc expected orthography | Whether Ho text and Ho TTS can be combined. **Unblocked** |
| 8 | Feasibility of a small Santali VITS from a recorded phrase bank | The only route to Santali speech output |
| 9 | Whether `goldfish-models/sat_olck_full` can score Santali fluency | A speaker-independent quality proxy that is better than round-trip chrF |

Extrapolating the `MEASURED` desktop latency to Android is **deliberately not
done**. A 2 GB Cortex-A53-class device is far slower than this 16-thread host, but
int8 quantisation moves the other way; multiplying two guesses produces a fake
number. §43 requires a device measurement, and until then the answer is
`NOT MEASURED`.

---

## 7. Consequences for the architecture (§62 tiering, now evidence-driven)

The measurements force the tiered design — it is not a stylistic preference:

```
Tier 1  Verified pre-translated phrase bank + PRE-RECORDED HUMAN AUDIO
        The ONLY route to spoken Santali today. Must carry the classroom.
        Latency ~ disk read. Quality = human. Coverage = finite.

Tier 2  Translation memory / fuzzy match over reviewer-approved pairs
        Extends Tier 1 without a model. Text only, unless audio pre-generated.

Tier 3  On-device int8 IndicTrans2-320M          [viability: item 1, NOT MEASURED]
        Novel sentences -> Ol Chiki TEXT. No spoken output (no TTS).
        Confidence-gated; low confidence must ask the teacher to rephrase.

Tier 4  Larger local model where hardware permits [NOT MEASURED]

Tier 5  Server-side, ONLINE ONLY — during preparation/sync, never in class.
        Also where server-side TTS audio is pre-generated into packs.
```

The critical architectural inversion: because Santali TTS does not exist, **audio
is an asset to be synchronised, not a runtime computation.** The pack pipeline
(§28) and the phrase cache (§12) therefore carry the product, and the neural model
is a text-only fallback. This is the opposite of the usual ASR→MT→TTS assumption
in the original brief, and it is what the evidence supports.

---

## 8. Blocking item — **RESOLVED**

**Hugging Face access token — obtained.** `ai4bharat/indictrans2-*` are
`gated: auto`; access granted, checkpoint downloaded (1.28 GB), and §6 items 1–3
are now measured in §2A.

**`IndicTransToolkit` — reimplemented, not installed.** It is Cython and requires
MSVC ≥14.0 (absent; README states Linux/macOS only). Reimplemented in pure Python
as `ml/translation/indictrans2_processor.py`, ported from `processor.pyx`:
`_flores_codes`, the digit translation table, `_PUNC_REPLACEMENTS`, the four
entity patterns, `_INDIC_FAILURE_CASES`, `_punc_norm`, `_wrap_with_placeholders`,
`_normalize`, `_do_indic_tokenize_and_transliterate`, `_preprocess`,
`_postprocess`. Only `indic-nlp-library` (pure Python) is needed. Deviations are
documented in the module docstring (`regex`→`re`; lazy `sacremoses`; placeholder
maps returned rather than pushed to a module-level `Queue`, which is not
thread-safe under concurrent requests).

**A claim in this document's earlier draft was wrong and is corrected here:**
the preprocessing subset needed for `hin_Deva → sat_Olck` is *not* sufficient.
Post-processing is **mandatory**, because IndicTrans2 emits a unified Devanagari
representation that must be transliterated into the target script. Omitting it
was the cause of correction 3 below.

---

## 9. Status

**Done:** existing implementation audited and found to be a mockup
(`audit-existing-implementation.md`); ML stack verified installable on Python
3.14; language coverage for MT/ASR/TTS verified against authoritative sources;
dataset and model inventory with licences read via `model_info`/`dataset_info`;
NLLB-200 Hindi→Santali measured end-to-end; **IndicTrans2-320M Hindi→Santali
measured end-to-end (§2A) and selected as the production model**; `IndicProcessor`
reimplemented in pure Python; tiering derived from measurement.

**Implemented and tested:**
- `ml/research/probe_nllb_santali.py` — the repository's first honest measurement
  instrument. Its analysis functions (`score_output`, `analyse_outputs`,
  `is_degenerate`, `has_char_repetition_loop`, `char_ratio_in_range`) are pure and
  covered by tests in `ml/tests/test_output_checks.py`.
- `ml/research/probe_indictrans2_santali.py` — same corpus, settings and analysis
  functions, so NLLB and IndicTrans2 are directly comparable. Asserts at runtime
  that the sinusoidal position table is non-degenerate (see correction 4).
- `ml/research/control_indictrans2_targets.py` — the control that caught both
  harness defects, by routing the same sentences to well-resourced targets whose
  scripts are unambiguous.
- `ml/translation/indictrans2_processor.py` — pure-Python `IndicProcessor`.

**Blocked:** Santali BLEU/chrF against IN22 (gated eval sets); all Android
measurement.

**Not started:** Phases 2–7.

**Explicitly not claimed:** any Android measurement; any adequacy score for
Santali output (round-trip chrF is a weak signal, not adequacy — no native
speaker has reviewed any output); any WER; any TTS quality; usability of the
100 h Santali speech corpus; the English-pivot hypothesis in §2A.1.

### Corrections made to this document during Phase 1

Recorded because all five were errors of method, and the method is the deliverable:

1. **Only the tag-declared script was being measured.** The probe reported
   `pct_output_in_target_script: 0.0` for `sat_Beng` and this was briefly read as
   "the model produces no valid target output". The model in fact produces 100%
   Ol Chiki; the *tag* is mislabelled. Now all registered scripts are measured and
   a mismatch is reported explicitly, with a regression test.
2. **Licences were initially read from search listings.** `list_models()` does not
   populate `card_data`, so Apache-2.0 repos appear as `license=None`. This would
   have wrongly excluded three usable Santali ASR models and two Santali LMs under
   §60. All licences here are now read via `model_info`/`dataset_info`.
3. **The mandatory `IndicProcessor` wrapper was not applied.** The first
   IndicTrans2 probe run reported Ol Chiki ratio 0.089 and "TAG MISLABELLED",
   and was nearly written up as "IndicTrans2 has weak Santali support". A control
   run to well-resourced targets returned **ben 0/6, tam 0/6, guj 0/6** — an
   impossible result for IndicTrans2, which proved the harness was at fault, not
   the model. Root cause: IndicTrans2 emits unified Devanagari and requires
   `postprocess_batch` to transliterate into the target script.
4. **`transformers` v5 silently zero-filled the sinusoidal position table.**
   Even after fix 3, the model card's *own* documented example returned scrambled
   word-salad ("small daily go was when I every go was") and one sentence in
   Meitei Mayek. `from_pretrained` reported **0 missing, 0 unexpected, 0
   mismatched keys** — the failure was completely silent. Cause:
   `IndicTransSinusoidalPositionalEmbedding` registers its table with
   `persistent=False` (correctly — it is computed, not stored), but v5 materializes
   the module on the meta device and zero-fills every tensor the checkpoint does
   not supply, discarding `__init__`'s `make_weights()` result. A zero table gives
   every position the same vector, making the encoder a bag of words. Confirmed by
   two direct probes: `PE[0] == PE[1]` exactly, and swapping two input tokens
   changed *only* those two positions' encoder outputs, leaving all others
   bit-identical. Fixed by `_restore_sinusoidal_positions()` in
   `ml/research/load_indictrans2.py`; the probe now asserts the table is
   non-degenerate before measuring. **The NLLB baseline was checked for the same
   defect and is clean** (its buffer is populated, `absmax=1.0`), so §2 stands.
   All pre-fix IndicTrans2 numbers are void and have been discarded.
5. **The degeneracy detector missed intra-word character loops.** `'एम्मोआउआउआउआउआउ'`
   is a single whitespace-delimited token, so both the unigram and n-gram checks
   scored it as ordinary output — while it also took 20,348 ms to generate, so the
   omission understated both the failure rate and the latency tail. Added
   `has_char_repetition_loop()`.

**Method note.** Corrections 3 and 4 were each caught by a control experiment, not
by inspection — in both cases the model's output looked plausible enough to report.
Fix 3 alone would have produced a *worse* outcome than no fix: the pipeline scored
**100% target-script hit rate on ben/tam/guj while emitting scrambled Hindi
transliterated into those scripts**. A script-validity check cannot detect a
word-order failure. Running the upstream model card's own example verbatim is what
exposed it, and is now the first check applied to any new checkpoint.
