import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Jharkhand Primary Multilingual Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "dev_secret_key_change_in_production_89472389472938472938479238"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/app.db"
    
    # Storage Paths
    STORAGE_ROOT: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_ROOT / "uploads"
    PACKS_DIR: Path = STORAGE_ROOT / "packs"
    AUDIO_DIR: Path = STORAGE_ROOT / "audio"
    EXPORT_DIR: Path = STORAGE_ROOT / "exports"
    MODEL_DIR: Path = STORAGE_ROOT / "models"
    
    # Seed and Data Paths
    DATA_ROOT: Path = BASE_DIR / "data"
    SEED_DIR: Path = DATA_ROOT / "seed"
    MANIFEST_DIR: Path = DATA_ROOT / "manifests"

    # Rate Limiting & File Size
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".json", ".zip"]

    # Supported Target Languages
    SUPPORTED_LANGUAGES: List[str] = ["hin", "sat", "unr", "hoc"]
    DEFAULT_SOURCE_LANGUAGE: str = "hin"
    DEFAULT_TARGET_LANGUAGE: str = "sat"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
for d in [settings.STORAGE_ROOT, settings.UPLOAD_DIR, settings.PACKS_DIR, 
          settings.AUDIO_DIR, settings.EXPORT_DIR, settings.MODEL_DIR,
          settings.DATA_ROOT, settings.SEED_DIR, settings.MANIFEST_DIR]:
    d.mkdir(parents=True, exist_ok=True)
