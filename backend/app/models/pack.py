from sqlalchemy import Column, String, Integer, BigInteger, JSON, Boolean
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class LanguagePack(Base, TimestampMixin):
    """
    Downloadable offline language pack containing SQLite phrases, glossary,
    lesson packs, audio clips, and quantized edge models.
    """
    __tablename__ = "language_packs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    language_code = Column(String(10), index=True, nullable=False)
    version = Column(String(50), nullable=False)  # Semantic version e.g. 1.0.0
    min_app_version = Column(String(50), default="1.0.0", nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, default=0)
    checksum = Column(String(64), nullable=False)  # SHA-256
    manifest_json = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="READY")  # READY, BUILDING, DEPRECATED

class SyncManifest(Base, TimestampMixin):
    """
    Content-addressed delta synchronization manifest.
    Enables devices to download only changed assets (v1 -> v2 diff).
    """
    __tablename__ = "sync_manifests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    version = Column(String(50), unique=True, index=True, nullable=False)
    language_code = Column(String(10), index=True, nullable=False)
    curriculum_checksum = Column(String(64), nullable=False)
    phrases_checksum = Column(String(64), nullable=False)
    glossary_checksum = Column(String(64), nullable=False)
    audio_checksum = Column(String(64), nullable=False)
    manifest_data = Column(JSON, nullable=False)
