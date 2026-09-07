from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.device_service import DeviceService
from backend.app.services.auth_service import require_roles
from backend.app.models.user import User

router = APIRouter(prefix="/devices", tags=["Devices"])

class DeviceRegisterRequest(BaseModel):
    device_id: str
    installation_id: str
    school_id: Optional[str] = None
    device_model: Optional[str] = None
    android_version: Optional[str] = None
    app_version: str = "1.0.0"
    total_ram_mb: int = 2048
    available_storage_mb: int = 4096
    supported_languages: Optional[List[str]] = None

class HeartbeatRequest(BaseModel):
    device_id: str
    available_storage_mb: Optional[int] = None
    installed_models: Optional[Dict[str, str]] = None

@router.post("/register")
def register_device(req: DeviceRegisterRequest, db: Session = Depends(get_db)):
    """Registers an Android classroom tablet or smartphone and returns signed device credentials."""
    return DeviceService.register_device(
        db,
        device_id=req.device_id,
        installation_id=req.installation_id,
        school_id=req.school_id,
        device_model=req.device_model,
        android_version=req.android_version,
        app_version=req.app_version,
        total_ram_mb=req.total_ram_mb,
        available_storage_mb=req.available_storage_mb,
        supported_languages=req.supported_languages
    )

@router.post("/heartbeat")
def device_heartbeat(req: HeartbeatRequest, request: Request, db: Session = Depends(get_db)):
    """Updates device heartbeat, storage availability, and model tracking."""
    client_ip = request.client.host if request.client else None
    device = DeviceService.update_heartbeat(
        db,
        device_id=req.device_id,
        available_storage_mb=req.available_storage_mb,
        installed_models=req.installed_models,
        ip_address=client_ip
    )
    return {
        "status": "HEARTBEAT_ACK",
        "device_id": device.device_id,
        "last_sync_at": device.last_sync_at.isoformat() if device.last_sync_at else None,
        "remote_config": device.remote_config
    }
