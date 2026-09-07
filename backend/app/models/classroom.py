from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class ClassroomSession(Base, TimestampMixin):
    """
    Temporary classroom context session created by teacher.
    Preserves privacy with automatic expiration (e.g. 8 hours max).
    """
    __tablename__ = "classroom_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(String(100), nullable=True)
    class_grade = Column(Integer, nullable=False, default=2)
    subject = Column(String(100), nullable=False, default="Mathematics")
    topic = Column(String(200), nullable=False)
    learning_outcome = Column(Text, nullable=True)
    target_language = Column(String(10), default="sat", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(hours=8), nullable=False)

    context_items = relationship("ContextItem", back_populates="session", cascade="all, delete-orphan")
    utterances = relationship("AudioUtterance", back_populates="session", cascade="all, delete-orphan")

class ContextItem(Base, TimestampMixin):
    __tablename__ = "context_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("classroom_sessions.id", ondelete="CASCADE"), nullable=False)
    item_type = Column(String(50), nullable=False)  # dialogue, vocabulary, command, instruction, summary
    content = Column(JSON, nullable=False)

    session = relationship("ClassroomSession", back_populates="context_items")

class AudioUtterance(Base, TimestampMixin):
    """
    Classroom telemetry and latency measurement entity.
    Child privacy principle: Raw audio is discarded; only performance metrics & sanitized transcripts are logged.
    """
    __tablename__ = "audio_utterances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("classroom_sessions.id", ondelete="CASCADE"), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    transcription = Column(Text, nullable=False)
    translation = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    tier_used = Column(String(50), default="cache")  # cache, tm, model
    
    # Latency tracking in milliseconds
    vad_latency_ms = Column(Float, default=0.0)
    asr_latency_ms = Column(Float, default=0.0)
    translation_latency_ms = Column(Float, default=0.0)
    tts_latency_ms = Column(Float, default=0.0)
    total_latency_ms = Column(Float, default=0.0)

    session = relationship("ClassroomSession", back_populates="utterances")
