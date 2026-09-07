import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from backend.app.core.database import Base

class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

def generate_uuid() -> str:
    return str(uuid.uuid4())
