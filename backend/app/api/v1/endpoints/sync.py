from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["Synchronization"])

class ComputeDeltaRequest(BaseModel):
    client_version: str
    language_code: str = "sat"
    client_checksums: Dict[str, str]

class UploadSyncRequest(BaseModel):
    device_id: str
    offline_sessions: List[Dict[str, Any]] = []
    offline_utterances: List[Dict[str, Any]] = []

@router.get("/manifest")
def get_manifest(lang: str = "sat", db: Session = Depends(get_db)):
    """Retrieves current server manifest for specified tribal language."""
    return SyncService.get_latest_manifest(db, language_code=lang)

@router.post("/delta")
def compute_delta(req: ComputeDeltaRequest, db: Session = Depends(get_db)):
    """
    Computes delta package requirements by comparing client section checksums
    against server manifests (Section 29).
    """
    return SyncService.compute_delta(
        db=db,
        client_version=req.client_version,
        client_checksums=req.client_checksums,
        language_code=req.language_code
    )

@router.post("/upload")
def upload_sync(req: UploadSyncRequest, db: Session = Depends(get_db)):
    """
    Uploads offline classroom sessions and telemetry upon network reconnection.
    Executes conflict resolution by non-destructive merge (Section 31).
    """
    return SyncService.upload_client_sync(
        db=db,
        device_id=req.device_id,
        offline_sessions=req.offline_sessions,
        offline_utterances=req.offline_utterances
    )
