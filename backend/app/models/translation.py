from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class Phrase(Base, TimestampMixin):
    """
    Tier 1 Instant Phrase Cache for common classroom expressions.
    Guarantees deterministic O(1) retrieval with < 30ms latency.
    """
    __tablename__ = "phrases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    cache_key = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256(source_lang:target_lang:normalized_text)
    source_lang = Column(String(10), index=True, nullable=False)
    target_lang = Column(String(10), index=True, nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    domain = Column(String(50), default="classroom", index=True)
    class_grade = Column(Integer, nullable=True)
    subject = Column(String(100), nullable=True)
    confidence = Column(Float, default=1.0)
    verification_status = Column(String(50), default="human_verified", index=True)  # human_verified, machine_generated, synthetic
    audio_asset_path = Column(String(500), nullable=True)
    usage_frequency = Column(Integer, default=0)
    version = Column(Integer, default=1)

    __table_args__ = (
        Index("ix_phrase_lookup", "source_lang", "target_lang", "domain"),
    )

class TranslationMemoryItem(Base, TimestampMixin):
    """
    Tier 2 Translation Memory for fuzzy/similarity retrieval.
    Stores bitext segments with quality scores and verified provenance.
    """
    __tablename__ = "translation_memory"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_lang = Column(String(10), index=True, nullable=False)
    target_lang = Column(String(10), index=True, nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    domain = Column(String(50), default="education", index=True)
    lesson_id = Column(String(36), nullable=True)
    subject = Column(String(100), nullable=True)
    class_grade = Column(Integer, nullable=True)
    verification_status = Column(String(50), default="human_verified", index=True)
    quality_score = Column(Float, default=1.0)
    source_type = Column(String(50), default="fln_curriculum")  # fln_curriculum, teacher_submission, flores200, bpcc
    version = Column(Integer, default=1)

class GlossaryTerm(Base, TimestampMixin):
    """
    Standardized multilingual terminology dictionary for primary schooling.
    Used for glossary constraint injection in MT and educational content.
    """
    __tablename__ = "glossary_terms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    hindi_term = Column(String(200), index=True, nullable=False)
    target_term = Column(String(200), nullable=False)
    target_lang = Column(String(10), index=True, nullable=False)
    domain = Column(String(50), default="mathematics", index=True)
    class_grade = Column(Integer, nullable=True)
    subject = Column(String(100), nullable=True)
    approved_translation = Column(String(200), nullable=False)
    alternative_translations = Column(JSON, default=list)
    pronunciation = Column(String(200), nullable=True)
    audio_asset_path = Column(String(500), nullable=True)
    verification_status = Column(String(50), default="human_verified")

class ReviewTask(Base, TimestampMixin):
    """
    Human-in-the-loop review queue for low-resource translation validation.
    """
    __tablename__ = "review_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_text = Column(Text, nullable=False)
    source_lang = Column(String(10), nullable=False)
    target_lang = Column(String(10), nullable=False)
    model_translation = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=True)
    status = Column(String(50), default="PENDING", index=True)  # PENDING, APPROVED, EDITED, REJECTED
    assigned_reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    decisions = relationship("ReviewDecision", back_populates="review_task", cascade="all, delete-orphan")

class ReviewDecision(Base, TimestampMixin):
    __tablename__ = "review_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    review_task_id = Column(String(36), ForeignKey("review_tasks.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_translation = Column(Text, nullable=False)
    corrected_translation = Column(Text, nullable=True)
    decision = Column(String(50), nullable=False)  # APPROVE, EDIT, REJECT
    reason = Column(String(255), nullable=True)

    review_task = relationship("ReviewTask", back_populates="decisions")
