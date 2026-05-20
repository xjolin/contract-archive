import pathlib
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Batch, Document
from app.schemas import BatchOut
from app.config import settings
from app.tasks.pipeline import process_document

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.post("")
async def create_batch(
    name: str = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if len(files) > 20:
        raise HTTPException(400, detail=f"一次最多上传 20 份，收到 {len(files)} 份")

    batch = Batch(name=name, status="running")
    db.add(batch)
    db.flush()

    folder = pathlib.Path(settings.storage_dir) / str(batch.id)
    folder.mkdir(parents=True, exist_ok=True)

    docs: list[Document] = []
    for idx, f in enumerate(files):
        safe_name = f"{uuid.uuid4().hex}_{f.filename}"
        path = folder / safe_name
        path.write_bytes(await f.read())
        d = Document(batch_id=batch.id, filename=f.filename, path=str(path), sort_order=idx)
        db.add(d)
        docs.append(d)
    db.commit()

    for d in docs:
        process_document.delay(d.id)

    return {"batch_id": batch.id, "count": len(docs)}


@router.get("", response_model=list[BatchOut])
def list_batches(db: Session = Depends(get_db)):
    return db.query(Batch).order_by(Batch.id.desc()).all()


@router.get("/{bid}", response_model=BatchOut)
def get_batch(bid: int, db: Session = Depends(get_db)):
    b = db.get(Batch, bid)
    if not b:
        raise HTTPException(404)
    return b


@router.delete("/{bid}")
def delete_batch(bid: int, db: Session = Depends(get_db)):
    b = db.get(Batch, bid)
    if not b:
        raise HTTPException(404)
    # 删除磁盘上的 PDF 目录
    folder = pathlib.Path(settings.storage_dir) / str(b.id)
    if folder.exists():
        for f in folder.iterdir():
            try:
                f.unlink()
            except Exception:
                pass
        try:
            folder.rmdir()
        except Exception:
            pass
    db.delete(b)  # cascade 删除 documents
    db.commit()
    return {"ok": True}
