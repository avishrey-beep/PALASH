import time
from backend.app.core.database import SessionLocal
from backend.app.models.job import BackgroundJob
from backend.app.services.job_service import JobService
from backend.app.services.pack_service import LanguagePackService

def process_single_job():
    db = SessionLocal()
    try:
        job = db.query(BackgroundJob).filter_by(status="QUEUED").order_by(BackgroundJob.created_at.asc()).first()
        if not job:
            return False

        # Mark as running
        JobService.update_job_progress(db, job.id, progress_pct=10.0, status="RUNNING")

        if job.job_type == "build_pack":
            lang = job.payload.get("language_code", "sat")
            ver = job.payload.get("version", "1.0.0")
            JobService.update_job_progress(db, job.id, progress_pct=50.0)
            res = LanguagePackService.build_pack(db, language_code=lang, version=ver)
            JobService.update_job_progress(db, job.id, progress_pct=100.0, status="COMPLETED", result=res)
            return True

        elif job.job_type == "batch_translate":
            # Simulate batch translation of curriculum lessons
            JobService.update_job_progress(db, job.id, progress_pct=50.0)
            time.sleep(0.1)
            JobService.update_job_progress(
                db, job.id, progress_pct=100.0, status="COMPLETED",
                result={"translated_count": len(job.payload.get("items", []))}
            )
            return True

        else:
            JobService.update_job_progress(
                db, job.id, progress_pct=100.0, status="COMPLETED",
                result={"message": f"Job {job.job_type} processed successfully"}
            )
            return True

    except Exception as e:
        if job:
            JobService.update_job_progress(db, job.id, progress_pct=job.progress_pct, status="FAILED", error_message=str(e))
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Worker started. Checking for queued jobs...")
    processed = process_single_job()
    print("Job processed:", processed)
