"""Speech endpoints.

Server-side ASR and TTS were mocks and have been removed; recognition and
synthesis now run on the device (see speech_service.py and
docs/backend-modifications.md). What remains here:

  POST /speech/synthesize   unchanged response shape; now returns a real
                            speakable pronunciation form instead of sine waves.
  POST /speech/translate    RETIRED -> 501, with a machine-readable pointer to
                            the on-device path. This is the one intentional
                            contract change in this project.
  POST /speech/utterances   NEW; persists a device-produced transcript plus
                            measured stage latencies. No audio is accepted.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.services.auth_service import get_current_user
from backend.app.services.speech_service import (
    ON_DEVICE_ASR_REASON,
    SpeechService,
)

router = APIRouter(prefix="/speech", tags=["Speech"])


@router.post("/translate", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def voice_to_voice_translate_removed():
    """RETIRED. Server-side ASR was a mock that never decoded audio.

    Returns 501 with a machine-readable reason and the on-device path, so no
    caller silently receives a fabricated transcript. This is a deliberate,
    documented contract change -- the alternative is continuing to lie.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=ON_DEVICE_ASR_REASON,
    )


@router.post("/synthesize")
def synthesize_speech(
    text: str = Form(...),
    language: str = Form("sat"),
):
    """Return a speakable pronunciation form for the device TTS engine.

    Response shape is unchanged (text/language/tier/latency_ms/
    duration_seconds/format). For Santali it adds the Devanagari
    transliteration the Hindi TTS voice needs to produce any sound, flagged as
    approximate and not native-verified.
    """
    return SpeechService.synthesize_pronunciation(text, language=language)


class PersistUtteranceRequest(BaseModel):
    """Telemetry for one device-produced utterance. NO audio (§37/§38)."""

    session_id: str
    source_language: str = "hin"
    target_language: str = "sat"
    transcription: str
    translation: str
    confidence: Optional[float] = None
    tier_used: str = "neural_indictrans2"
    vad_latency_ms: float = 0.0
    asr_latency_ms: float = 0.0
    translation_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0


@router.post("/utterances")
def persist_utterance(
    req: PersistUtteranceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Persist a device-produced transcript plus its measured stage latencies.

    These timings were measured on real audio on the device, so they are the
    only real latency numbers about this pipeline. Authenticated, unlike the
    retired route, because it writes to a teacher's classroom session.
    """
    result = SpeechService.persist_utterance(
        db=db,
        session_id=req.session_id,
        source_language=req.source_language,
        target_language=req.target_language,
        transcription=req.transcription,
        translation=req.translation,
        confidence=req.confidence,
        tier_used=req.tier_used,
        vad_latency_ms=req.vad_latency_ms,
        asr_latency_ms=req.asr_latency_ms,
        translation_latency_ms=req.translation_latency_ms,
        tts_latency_ms=req.tts_latency_ms,
        total_latency_ms=req.total_latency_ms,
    )
    if not result["stored"]:
        code = (
            status.HTTP_404_NOT_FOUND
            if result.get("error") == "SESSION_NOT_FOUND"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=result["error"])
    return result
