from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.auth_service import require_roles
from backend.app.models.model_registry import AIModelEntry
from backend.app.models.user import User

router = APIRouter(prefix="/models", tags=["Model Registry"])

class UpdateModelStatusRequest(BaseModel):
    status: str  # EXPERIMENTAL, TESTING, PRODUCTION, DEPRECATED

@router.get("")
def list_models(task: Optional[str] = None, language: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists registered AI models with hardware requirements, quantization, and evaluation metrics."""
    q = db.query(AIModelEntry)
    if task:
        q = q.filter_by(task=task)
    if language:
        q = q.filter_by(language=language)
    models = q.all()
    return [
        {
            "id": m.id,
            "model_name": m.model_name,
            "version": m.version,
            "task": m.task,
            "language": m.language,
            "language_pair": m.language_pair,
            "framework": m.framework,
            "quantization": m.quantization,
            "disk_size_mb": m.disk_size_mb,
            "ram_required_mb": m.ram_required_mb,
            "license": m.license,
            "accuracy_metrics": m.accuracy_metrics,
            "latency_p50_ms": m.latency_p50_ms,
            "status": m.status
        }
        for m in models
    ]

@router.post("/{model_id}/status")
def update_model_status(
    model_id: str,
    req: UpdateModelStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ML_OPERATOR"]))
):
    """Rolls out or rolls back a model's deployment status."""
    entry = db.query(AIModelEntry).filter_by(id=model_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Model entry not found")

    entry.status = req.status
    db.commit()
    db.refresh(entry)
    return {"model_name": entry.model_name, "version": entry.version, "status": entry.status}
