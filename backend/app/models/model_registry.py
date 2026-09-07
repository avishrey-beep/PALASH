from sqlalchemy import Column, String, Integer, Float, JSON
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class AIModelEntry(Base, TimestampMixin):
    """
    Model Registry tracking model metadata, quantization,
    hardware envelopes, licenses, and deployment readiness.
    """
    __tablename__ = "model_registry"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    task = Column(String(50), index=True, nullable=False)  # TRANSLATION, ASR, TTS
    language = Column(String(20), index=True, nullable=False)  # sat, hin, unr, hoc
    language_pair = Column(String(30), index=True, nullable=True)  # hin-sat, sat-hin
    framework = Column(String(50), nullable=False)  # ONNX, PYTORCH, TFLITE, CTRANSLATE2
    quantization = Column(String(50), default="INT8")  # FP32, FP16, INT8
    checksum = Column(String(64), nullable=False)
    disk_size_mb = Column(Float, nullable=False)
    ram_required_mb = Column(Integer, nullable=False)
    license = Column(String(100), nullable=False)
    accuracy_metrics = Column(JSON, default=dict)  # {"bleu": 24.5, "chrf": 48.2} or {"wer": 0.28}
    latency_p50_ms = Column(Float, default=0.0)
    status = Column(String(50), default="TESTING", index=True)  # EXPERIMENTAL, TESTING, PRODUCTION, DEPRECATED
    file_path = Column(String(500), nullable=True)
