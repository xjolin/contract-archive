from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import get_db
from app.models import Document
from app.tasks.pipeline import process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


class PatchExtracted(BaseModel):
    extracted_json: dict


@router.post("/{did}/retry")
def retry(did: int, db: Session = Depends(get_db)):
    d = db.get(Document, did)
    if not d:
        raise HTTPException(404)
    d.status = "pending"
    d.error = None
    db.commit()
    process_document.delay(did)
    return {"ok": True}


@router.patch("/{did}")
def patch(did: int, body: PatchExtracted, db: Session = Depends(get_db)):
    d = db.get(Document, did)
    if not d:
        raise HTTPException(404)
    d.extracted_json = body.extracted_json
    db.commit()
    return {"ok": True}
