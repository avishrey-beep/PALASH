import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.pack_service import LanguagePackService
from backend.app.services.auth_service import require_roles
from backend.app.models.pack import LanguagePack
from backend.app.models.user import User

router = APIRouter(prefix="/language-packs", tags=["Language Packs"])

class BuildPackRequest(BaseModel):
    language_code: str = "sat"
    version: str = "1.0.0"
    min_app_version: str = "1.0.0"

@router.post("/build")
def build_pack(
    req: BuildPackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ML_OPERATOR", "CURRICULUM_MANAGER"]))
):
    """Packages phrases, glossary, lessons, audio, and manifests into downloadable offline pack."""
    return LanguagePackService.build_pack(
        db=db,
        language_code=req.language_code,
        version=req.version,
        min_app_version=req.min_app_version
    )

@router.get("")
def list_packs(language_code: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists available offline language packs and checksums."""
    q = db.query(LanguagePack).filter_by(is_active=True)
    if language_code:
        q = q.filter_by(language_code=language_code)
    packs = q.all()
    return [
        {
            "id": p.id,
            "language_code": p.language_code,
            "version": p.version,
            "file_size_bytes": p.file_size_bytes,
            "checksum": p.checksum,
            "status": p.status,
            "created_at": p.created_at.isoformat()
        }
        for p in packs
    ]

@router.get("/download")
def download_pack(lang: str = "sat", version: Optional[str] = None, db: Session = Depends(get_db)):
    """Downloads language pack zip archive."""
    q = db.query(LanguagePack).filter_by(language_code=lang, is_active=True)
    if version:
        pack = q.filter_by(version=version).first()
    else:
        pack = q.order_by(LanguagePack.created_at.desc()).first()

    if not pack or not os.path.exists(pack.file_path):
        raise HTTPException(status_code=404, detail="Language pack file not found on disk")

    return FileResponse(
        pack.file_path,
        media_type="application/zip",
        filename=os.path.basename(pack.file_path)
    )
