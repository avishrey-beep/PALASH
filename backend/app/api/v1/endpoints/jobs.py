from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

class CreateJobRequest(BaseModel):
    job_type: str  # curriculum_ingest, build_pack, batch_translate
    payload: Dict[str, Any] = {}

@router.post("")
def create_job(req: CreateJobRequest, db: Session = Depends(get_db)):
    """Submits a long-running task to the asynchronous background job queue (Section 34)."""
    job = JobService.create_job(db, job_type=req.job_type, payload=req.payload)
    return {
        "job_id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "created_at": job.created_at.isoformat()
    }

@router.get("/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Retrieves current job status, progress, and result."""
    job = JobService.get_job(db, job_id)
    return {
        "job_id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "result": job.result,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }

@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Cancels a queued or running background job."""
    job = JobService.cancel_job(db, job_id)
    return {"job_id": job.id, "status": job.status}
