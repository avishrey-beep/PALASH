"""Ol Chiki (U+1C50-U+1C7F) -> Devanagari transliteration.

WHY THIS EXISTS
---------------
The product decision is that Santali text is spoken aloud using the Android
Hindi TTS voice, because no Android TTS voice exists for Santali, Ho or
Mundari. An Android Hindi TTS engine silently skips codepoints outside the
scripts it knows: handed Ol Chiki, it produces *no audio at all*, with no
error. So a script bridge is required before any sound can be produced.

No installed library can do this (MEASURED):
  * ``indic_transliteration`` (sanscript) is not installed.
  * ``indic-nlp-library`` has no Ol Chiki script range. Worse,
    ``IndicProcessor``'s ``_flores_codes["sat_Olck"] == "or"``, so its
    Ol Chiki path resolves to Odia; calling
    ``UnicodeIndicTransliterator.transliterate("ᱫᱩᱲᱩᱵ ᱢᱮ", "or", "hi")``
    returns the input unchanged. See ``indictrans2_processor.py``'s
    ``OLCK_POSTPROCESS_IS_LOSSY``.

Hence a hand-written table. Ol Chiki is a true alphabet: exactly 30 letters
plus a small set of diacritics, every vowel an independent letter. That makes a
deterministic table tractable and fully unit-testable, unlike a script with
contextual conjuncts.

WHAT THIS IS NOT (read before using the output for anything else)
----------------------------------------------------------------
This is a **pronunciation aid for a speech synthesiser**, not a transliteration
standard and not a translation. It is not reviewed by a Santali speaker. The
resulting audio is *approximate Santali spoken with Hindi phonetics* and will
be wrong in ways a native speaker would notice:

  * Ol Chiki ``ᱚ`` is /ɔ/; Devanagari inherent /ə/ is the nearest Hindi vowel.
  * ``ᱹ`` GAAHLAA TTUDDAAG changes vowel quality with no Hindi equivalent, so
    it is dropped (see ``_DROPPED``).
  * ``ᱶ`` OV is a nasalised /w/; rendered as plain व, losing nasality.
  * ``ᱽ`` PHAARKAA is a glottal stop, which Hindi lacks phonemically.
  * Santali is a tonal-register-free but checked-consonant language; final
    checked stops are not distinguished here.

Any UI surfacing audio derived from this MUST label it as approximate and
machine-transliterated rather than presenting it as correct Santali. See
``PRONUNCIATION_DISCLAIMER``.

Verified against the 25 human-verified phrases seeded in the database, e.g.
``ᱫᱩᱲᱩᱵ ᱢᱮ`` -> ``दुड़ुब मे`` ("duṛub me", sit down).
"""

from __future__ import annotations

import unicodedata


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# Unicode Ol Chiki block bounds, for detection.
OLCK_START = 0x1C50
OLCK_END = 0x1C7F

PRONUNCIATION_DISCLAIMER = (
    "Approximate pronunciation: machine-transliterated from Ol Chiki to "
    "Devanagari and spoken with a Hindi voice. Not verified by a Santali "
    "speaker."
)

# ---------------------------------------------------------------------------
# Vowels. Ol Chiki writes vowels as independent letters, Devanagari needs both
# an independent form (word-initial / after another vowel) and a matra form
# (attached to a preceding consonant).
# ---------------------------------------------------------------------------
_VOWELS: dict[str, tuple[str, str]] = {
    # olck: (independent, matra).  "" matra == Devanagari inherent vowel.
    "ᱚ": ("अ", ""),          # ᱚ LA   /ɔ/ -> अ  (inherent)
    "ᱟ": ("आ", "ा"),    # ᱟ LAA  /a/ -> आ / ा
    "ᱤ": ("इ", "ि"),    # ᱤ LI   /i/ -> इ / ि
    "ᱩ": ("उ", "ु"),    # ᱩ LU   /u/ -> उ / ु
    "ᱮ": ("ए", "े"),    # ᱮ LE   /e/ -> ए / े
    "ᱳ": ("ओ", "ो"),    # ᱳ LO   /o/ -> ओ / ो
}

# ---------------------------------------------------------------------------
# Consonants. Bare Devanagari letter; the inherent vowel is handled by the
# syllable assembler, not here.
# ---------------------------------------------------------------------------
_CONSONANTS: dict[str, str] = {
    "ᱛ": "त",  # ᱛ AT   /t/  -> त
    "ᱜ": "ग",  # ᱜ AG   /g/  -> ग
    "ᱝ": "ङ",  # ᱝ ANG  /ŋ/  -> ङ
    "ᱞ": "ल",  # ᱞ AL   /l/  -> ल
    "ᱠ": "क",  # ᱠ AAK  /k/  -> क
    "ᱡ": "ज",  # ᱡ AAJ  /dʒ/ -> ज
    "ᱢ": "म",  # ᱢ AAM  /m/  -> म
    "ᱣ": "व",  # ᱣ AAW  /w/  -> व
    "ᱥ": "स",  # ᱥ IS   /s/  -> स
    "ᱦ": "ह",  # ᱦ IH   /h/  -> ह
    "ᱧ": "ञ",  # ᱧ INY  /ɲ/  -> ञ
    "ᱨ": "र",  # ᱨ IR   /r/  -> र
    "ᱪ": "च",  # ᱪ UCH  /tʃ/ -> च
    "ᱫ": "द",  # ᱫ UD   /d/  -> द
    "ᱬ": "ण",  # ᱬ UNN  /ɳ/  -> ण
    "ᱭ": "य",  # ᱭ UY   /j/  -> य
    "ᱯ": "प",  # ᱯ EP   /p/  -> प
    "ᱰ": "ड",  # ᱰ EDD  /ɖ/  -> ड
    "ᱱ": "न",  # ᱱ EN   /n/  -> न
    "ᱲ": "ड़",  # ᱲ ERR  /ɽ/  -> ड़
    "ᱴ": "ट",  # ᱴ OTT  /ʈ/  -> ट
    "ᱵ": "ब",  # ᱵ OB   /b/  -> ब
    "ᱶ": "व",  # ᱶ OV   /w̃/  -> व   (nasality lost; documented)
}

# ---------------------------------------------------------------------------
# Modifiers.
# ---------------------------------------------------------------------------
# ᱷ OH aspirates the PRECEDING consonant rather than standing alone.
_ASPIRATION = "ᱷ"
_ASPIRATED: dict[str, str] = {
    "क": "ख",  # क -> ख
    "ग": "घ",  # ग -> घ
    "च": "छ",  # च -> छ
    "ज": "झ",  # ज -> झ
    "ट": "ठ",  # ट -> ठ
    "ड": "ढ",  # ड -> ढ
    "त": "थ",  # त -> थ
    "द": "ध",  # द -> ध
    "प": "फ",  # प -> फ
    "ब": "भ",  # ब -> भ
    "ड़": "ढ़",  # ड़ -> ढ़
}

# Nasalisation -> anusvara. Meaningful for Hindi TTS, so it is preserved.
_NASALS = {
    "ᱸ",  # ᱸ MU TTUDDAG
    "ᱺ",  # ᱺ MU-GAAHLAA TTUDDAAG (nasal kept, vowel shift dropped)
}
_ANUSVARA = "ं"

# Diacritics with no Hindi phonetic equivalent. Dropped deliberately: emitting
# an unmappable combining mark would make the TTS engine skip the word, which
# is the exact failure this module exists to prevent.
_DROPPED = {
    "ᱹ",  # ᱹ GAAHLAA TTUDDAAG  - vowel quality shift
    "ᱻ",  # ᱻ TTUDDAAG
    "ᱼ",  # ᱼ RELAA            - lengthener
    "ᱽ",  # ᱽ PHAARKAA         - glottal stop
}

_PUNCTUATION = {
    "᱾": "।",  # ᱾ MUCAAD        -> ।
    "᱿": "॥",  # ᱿ DOUBLE MUCAAD -> ॥
}

# ᱐-᱙ -> ASCII. IndicProcessor already folds these on the way in; handled here
# too so this function is correct standalone.
_DIGITS = {chr(0x1C50 + n): str(n) for n in range(10)}

_VIRAMA = "्"

# Devanagari nukta letters (U+0958-U+095F) are Unicode composition exclusions:
# NFC yields the DECOMPOSED form (base + U+093C NUKTA), never the precomposed
# codepoint. The tables above are normalised here, and output is normalised on
# the way out, so a precomposed U+095C typed into the table cannot silently
# disagree with NFC-normalised text arriving from the model or the database.
_VOWELS = {
    k: (_nfc(ind), _nfc(mat)) for k, (ind, mat) in _VOWELS.items()
}
_CONSONANTS = {k: _nfc(v) for k, v in _CONSONANTS.items()}
_ASPIRATED = {_nfc(k): _nfc(v) for k, v in _ASPIRATED.items()}


def contains_ol_chiki(text: str) -> bool:
    """True if any character lies in the Ol Chiki block.

    Used to decide whether a string needs the bridge before being handed to a
    Hindi TTS voice.
    """
    return any(OLCK_START <= ord(ch) <= OLCK_END for ch in text)


def ol_chiki_to_devanagari(text: str) -> str:
    """Transliterate Ol Chiki to Devanagari for speech synthesis.

    Deterministic and idempotent on non-Ol-Chiki input: characters outside the
    block pass through untouched, so mixed-script strings are safe.

    Syllable assembly, since Devanagari is an abugida and Ol Chiki is not:
      * consonant + vowel      -> consonant + matra
      * consonant + consonant  -> first consonant + virama (cluster)
      * consonant at word end   -> bare consonant, no virama, relying on Hindi
        word-final schwa deletion. A trailing virama is orthographically
        defensible but makes some TTS engines clip the syllable.
      * vowel with no preceding consonant -> independent vowel form
    """
    out: list[str] = []
    pending: str | None = None  # a Devanagari consonant awaiting its vowel

    def flush(final: bool) -> None:
        """Emit a consonant that never received a vowel."""
        nonlocal pending
        if pending is None:
            return
        out.append(pending if final else pending + _VIRAMA)
        pending = None

    for ch in text:
        if ch in _VOWELS:
            independent, matra = _VOWELS[ch]
            if pending is not None:
                out.append(pending + matra)
                pending = None
            else:
                out.append(independent)
        elif ch in _CONSONANTS:
            flush(final=False)  # consonant cluster: previous one takes virama
            pending = _CONSONANTS[ch]
        elif ch == _ASPIRATION:
            if pending is not None:
                # Aspirate in place; unaspirable letters keep their base form.
                pending = _ASPIRATED.get(pending, pending)
            else:
                # Stray aspiration -> ह, left pending so a following vowel
                # attaches as a matra rather than surfacing independently.
                pending = "ह"
        elif ch in _NASALS:
            # Anusvara attaches to the syllable already emitted. If a bare
            # consonant is pending it must surface first, carrying its
            # inherent vowel, or the mark would have nothing to sit on.
            if pending is not None:
                out.append(pending)
                pending = None
            out.append(_ANUSVARA)
        elif ch in _DROPPED:
            continue
        elif ch in _DIGITS:
            flush(final=True)
            out.append(_DIGITS[ch])
        elif ch in _PUNCTUATION:
            flush(final=True)
            out.append(_PUNCTUATION[ch])
        else:
            # Whitespace, Latin, Devanagari, ASCII punctuation: a word boundary.
            flush(final=True)
            out.append(ch)

    flush(final=True)
    return _nfc("".join(out))


def pronunciation_form(text: str) -> dict[str, object]:
    """Devanagari pronunciation payload for a TTS client.

    Returns the text to speak plus enough metadata for the UI to label it
    honestly. ``transliterated`` is False when nothing was Ol Chiki, in which
    case ``speech_text`` is the input and no disclaimer is warranted.
    """
    needs = contains_ol_chiki(text)
    return {
        "source_text": text,
        "speech_text": ol_chiki_to_devanagari(text) if needs else text,
        "transliterated": needs,
        "script_from": "Olck" if needs else None,
        "script_to": "Deva" if needs else None,
        "disclaimer": PRONUNCIATION_DISCLAIMER if needs else None,
        "verified_by_native_speaker": False,
    }
