from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    installation_id = Column(String(100), index=True, nullable=False)
    school_id = Column(String(100), index=True, nullable=True)
    device_model = Column(String(100), nullable=True)
    android_version = Column(String(50), nullable=True)
    app_version = Column(String(50), nullable=False, default="1.0.0")
    total_ram_mb = Column(Integer, default=2048)
    available_storage_mb = Column(Integer, default=4096)
    
    # Supported language codes e.g. ["hin", "sat", "unr"]
    supported_languages = Column(JSON, default=lambda: ["hin", "sat"])
    
    # Installed model versions e.g. {"nmt": "1.0.0", "asr": "1.0.0"}
    installed_models = Column(JSON, default=dict)
    
    # Remote configuration dictionary
    remote_config = Column(JSON, default=dict)

    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    last_ip_address = Column(String(50), nullable=True)

    sync_logs = relationship("DeviceSyncLog", back_populates="device", cascade="all, delete-orphan")

class DeviceSyncLog(Base, TimestampMixin):
    __tablename__ = "device_sync_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    sync_type = Column(String(50), nullable=False)  # full, delta, telemetry
    status = Column(String(50), nullable=False)  # started, completed, failed
    bytes_transferred = Column(Integer, default=0)
    client_manifest_version = Column(String(50), nullable=True)
    server_manifest_version = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    device = relationship("Device", back_populates="sync_logs")
