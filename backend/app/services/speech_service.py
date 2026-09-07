"""Speech services, rewritten to stop fabricating audio.

WHAT CHANGED AND WHY (§2, §37, §38, §72)
----------------------------------------
The previous implementation chained ``ml.asr.engine`` and ``ml.tts.engine``,
both of which were mocks:
  * ASR returned the caller's own ``expected_text`` (or a hardcoded Hindi
    string) and never decoded the audio bytes at all.
  * TTS returned three summed sine waves whose only text-derived property was
    ``len(text)``.
So ``POST /speech/translate`` reported a fake transcript, a translation of that
fake transcript, and a fake audio duration -- while claiming to measure the
end-to-end latency of a real pipeline.

The honest architecture is on-device (see docs/backend-modifications.md):
  * ASR  -> Android SpeechRecognizer (hi-IN), on the device.
  * TTS  -> Android TextToSpeech, on the device.
This also strengthens child-privacy compliance: raw audio never leaves the
tablet (§37/§38). The server's role shrinks to (a) translating the transcript
the device produced and (b) storing measured telemetry -- never audio.

``ml.asr.engine`` and ``ml.tts.engine`` are deleted. This module no longer
imports them.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.models.classroom import AudioUtterance, ClassroomSession
from ml.translation.engine import LayeredTranslationEngine
from ml.transliteration.olchiki import contains_ol_chiki, pronunciation_form

# Machine-readable reason returned by the retired server-side audio route, so a
# client receives an honest refusal instead of fabricated audio.
ON_DEVICE_ASR_REASON = {
    "error": "SERVER_SIDE_ASR_REMOVED",
    "detail": (
        "Server-side speech recognition was a mock that echoed the caller's "
        "expected_text and never decoded audio. It has been removed. Speech "
        "recognition now runs on the device (Android SpeechRecognizer) so "
        "child audio never leaves the tablet (privacy requirements §37/§38)."
    ),
    "on_device_path": (
        "Use the device ASR service to produce a transcript, then call "
        "POST /api/v1/translation/translate for text, and "
        "POST /api/v1/speech/utterances to persist measured telemetry."
    ),
}


class SpeechService:
    """Server-side speech operations that remain after ASR/TTS moved on-device."""

    @staticmethod
    def synthesize_pronunciation(
        text: str, language: str = "sat"
    ) -> Dict[str, Any]:
        """Return a speakable form of ``text`` for the device TTS engine.

        This replaces the sine-wave TTS mock while KEEPING the exact response
        shape ``POST /speech/synthesize`` already advertised
        (``text/language/tier/latency_ms/duration_seconds/format``), so no
        client contract breaks. It never returned audio bytes, so nothing that
        depended on bytes is lost.

        The useful work it now does: Android's Hindi TTS voice silently skips
        Ol Chiki codepoints and produces no audio, so for Santali we return a
        Devanagari transliteration the engine can actually voice -- explicitly
        labelled approximate and not native-verified. Duration is estimated
        and labelled as such, never measured here (there is no audio to
        measure server-side).
        """
        t0 = time.perf_counter()
        form = pronunciation_form(text)
        speech_text = form["speech_text"]
        latency_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "text": text,
            "language": language,
            "tier": "on_device_tts",
            "latency_ms": round(latency_ms, 3),
            # Rough reading-time estimate for UI progress only. Labelled
            # ESTIMATED per §72; the real duration is known only on the device.
            "duration_seconds": None,
            "duration_basis": "NOT_MEASURED_SERVER_SIDE",
            "format": "text/pronunciation-deva",
            # Everything the device and UI need to speak this honestly:
            "speech_text": speech_text,
            "speech_script": form["script_to"] or (
                "Olck" if contains_ol_chiki(text) else None
            ),
            "transliterated": form["transliterated"],
            "pronunciation_is_approximate": form["transliterated"],
            "verified_by_native_speaker": False,
            "disclaimer": form["disclaimer"],
        }

    @staticmethod
    def persist_utterance(
        db: Session,
        session_id: str,
        source_language: str,
        target_language: str,
        transcription: str,
        translation: str,
        confidence: Optional[float],
        tier_used: str,
        vad_latency_ms: float = 0.0,
        asr_latency_ms: float = 0.0,
        translation_latency_ms: float = 0.0,
        tts_latency_ms: float = 0.0,
        total_latency_ms: float = 0.0,
    ) -> Dict[str, Any]:
        """Persist a device-produced utterance: transcript + measured latencies.

        NO AUDIO is accepted or stored (§37/§38); the device measured these
        stage timings on real audio and hardware, so they are the only latency
        numbers about this pipeline that are real. ``confidence`` is nullable:
        None is stored as SQL NULL, meaning "unknown", never coerced to a
        fabricated score (§52).
        """
        session = (
            db.query(ClassroomSession)
            .filter(ClassroomSession.id == session_id)
            .first()
        )
        if session is None:
            return {"stored": False, "error": "SESSION_NOT_FOUND"}

        utterance = AudioUtterance(
            session_id=session_id,
            source_language=source_language,
            target_language=target_language,
            transcription=transcription,
            translation=translation,
            confidence=confidence,
            tier_used=tier_used,
            vad_latency_ms=round(vad_latency_ms, 2),
            asr_latency_ms=round(asr_latency_ms, 2),
            translation_latency_ms=round(translation_latency_ms, 2),
            tts_latency_ms=round(tts_latency_ms, 2),
            total_latency_ms=round(total_latency_ms, 2),
        )
        try:
            db.add(utterance)
            db.commit()
            db.refresh(utterance)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            return {"stored": False, "error": f"{type(exc).__name__}: {exc}"}

        return {"stored": True, "utterance_id": utterance.id}
