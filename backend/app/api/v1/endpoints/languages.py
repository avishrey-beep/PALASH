from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.curriculum import Language

router = APIRouter(prefix="/languages", tags=["Languages"])

@router.get("")
def list_languages(db: Session = Depends(get_db)):
    """Lists all configured source and indigenous target languages (Hindi, Santhali, Mundari, Ho)."""
    langs = db.query(Language).filter_by(is_active=True).all()
    return [
        {
            "code": l.code,
            "name": l.name,
            "native_name": l.native_name,
            "default_script": l.default_script
        }
        for l in langs
    ]
