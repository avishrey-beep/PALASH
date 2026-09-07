from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.core.security import create_device_token
from backend.app.models.device import Device, DeviceSyncLog

class DeviceService:
    @staticmethod
    def register_device(
        db: Session,
        device_id: str,
        installation_id: str,
        school_id: Optional[str] = None,
        device_model: Optional[str] = None,
        android_version: Optional[str] = None,
        app_version: str = "1.0.0",
        total_ram_mb: int = 2048,
        available_storage_mb: int = 4096,
        supported_languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        device = db.query(Device).filter_by(device_id=device_id).first()
        if not device:
            device = Device(
                device_id=device_id,
                installation_id=installation_id,
                school_id=school_id,
                device_model=device_model,
                android_version=android_version,
                app_version=app_version,
                total_ram_mb=total_ram_mb,
                available_storage_mb=available_storage_mb,
                supported_languages=supported_languages or ["hin", "sat"],
                remote_config={"offline_mode": True, "max_offline_sessions": 50},
                is_active=True,
                last_sync_at=datetime.now(timezone.utc)
            )
            db.add(device)
        else:
            device.installation_id = installation_id
            device.app_version = app_version
            device.total_ram_mb = total_ram_mb
            device.available_storage_mb = available_storage_mb
            device.last_sync_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(device)

        device_token = create_device_token(device_id=device.device_id, school_id=device.school_id)

        return {
            "device_token": device_token,
            "device": {
                "id": device.id,
                "device_id": device.device_id,
                "school_id": device.school_id,
                "supported_languages": device.supported_languages,
                "remote_config": device.remote_config
            }
        }

    @staticmethod
    def update_heartbeat(
        db: Session,
        device_id: str,
        available_storage_mb: Optional[int] = None,
        installed_models: Optional[Dict[str, str]] = None,
        ip_address: Optional[str] = None
    ) -> Device:
        device = db.query(Device).filter_by(device_id=device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device.last_sync_at = datetime.now(timezone.utc)
        if available_storage_mb is not None:
            device.available_storage_mb = available_storage_mb
        if installed_models is not None:
            device.installed_models = installed_models
        if ip_address:
            device.last_ip_address = ip_address

        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def log_sync_event(
        db: Session,
        device_id: str,
        sync_type: str,
        status: str,
        bytes_transferred: int = 0,
        error_message: Optional[str] = None
    ) -> DeviceSyncLog:
        device = db.query(Device).filter_by(device_id=device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        log = DeviceSyncLog(
            device_id=device.id,
            sync_type=sync_type,
            status=status,
            bytes_transferred=bytes_transferred,
            error_message=error_message
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
