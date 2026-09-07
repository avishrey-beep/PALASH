import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.worksheet_service import WorksheetService
from backend.app.models.content import Worksheet

router = APIRouter(prefix="/worksheets", tags=["Worksheets"])

class GenerateWorksheetRequest(BaseModel):
    class_grade: int = 2
    subject: str = "Mathematics"
    topic: str = "Addition up to 20"
    target_language: str = "sat"
    lesson_id: Optional[str] = None
    question_count: int = 5
    difficulty: str = "EASY"

@router.post("/generate")
def generate_worksheet(req: GenerateWorksheetRequest, db: Session = Depends(get_db)):
    """
    Generates a bilingual classroom worksheet constrained by curriculum topic.
    Outputs structured JSON, HTML representation, and printable PDF.
    """
    return WorksheetService.generate_bilingual_worksheet(
        db=db,
        class_grade=req.class_grade,
        subject=req.subject,
        topic=req.topic,
        target_language=req.target_language,
        lesson_id=req.lesson_id,
        question_count=req.question_count,
        difficulty=req.difficulty
    )

@router.get("/{worksheet_id}/html", response_class=HTMLResponse)
def get_worksheet_html(worksheet_id: str, db: Session = Depends(get_db)):
    """Renders printable HTML worksheet."""
    ws = db.query(Worksheet).filter_by(id=worksheet_id).first()
    if not ws or not ws.html_content:
        raise HTTPException(status_code=404, detail="Worksheet HTML not found")
    return HTMLResponse(content=ws.html_content)

@router.get("/{worksheet_id}/pdf")
def get_worksheet_pdf(worksheet_id: str, db: Session = Depends(get_db)):
    """Downloads printable PDF worksheet."""
    ws = db.query(Worksheet).filter_by(id=worksheet_id).first()
    if not ws or not ws.pdf_path or not os.path.exists(ws.pdf_path):
        raise HTTPException(status_code=404, detail="Worksheet PDF not found on disk")
    return FileResponse(ws.pdf_path, media_type="application/pdf", filename=os.path.basename(ws.pdf_path))
