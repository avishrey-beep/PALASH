from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.job import BackgroundJob

class JobService:
    @staticmethod
    def create_job(db: Session, job_type: str, payload: Dict[str, Any]) -> BackgroundJob:
        job = BackgroundJob(
            job_type=job_type,
            status="QUEUED",
            progress_pct=0.0,
            payload=payload
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> BackgroundJob:
        job = db.query(BackgroundJob).filter_by(id=job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    @staticmethod
    def update_job_progress(
        db: Session,
        job_id: str,
        progress_pct: float,
        status: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> BackgroundJob:
        job = db.query(BackgroundJob).filter_by(id=job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job.progress_pct = progress_pct
        if status:
            job.status = status
            if status == "RUNNING" and not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            elif status in ["COMPLETED", "FAILED", "CANCELLED"]:
                job.completed_at = datetime.now(timezone.utc)

        if result:
            job.result = result
        if error_message:
            job.error_message = error_message

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def cancel_job(db: Session, job_id: str) -> BackgroundJob:
        job = db.query(BackgroundJob).filter_by(id=job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status in ["COMPLETED", "FAILED"]:
            raise HTTPException(status_code=400, detail="Cannot cancel completed or failed job")
        
        job.status = "CANCELLED"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return job
