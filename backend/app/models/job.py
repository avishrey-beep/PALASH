from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, JSON, DateTime
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class BackgroundJob(Base, TimestampMixin):
    """
    Asynchronous job tracking entity for curriculum ingestion,
    OCR, batch translation, audio generation, and pack building.
    """
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_type = Column(String(50), index=True, nullable=False)  # curriculum_ingest, build_pack, batch_translate, generate_worksheets
    status = Column(String(50), default="QUEUED", index=True, nullable=False)  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    progress_pct = Column(Float, default=0.0)
    payload = Column(JSON, default=dict)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
