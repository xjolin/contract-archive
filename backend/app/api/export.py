import pathlib
import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Batch
from app.exporters.xlsx import export_batch

router = APIRouter(prefix="/api/batches", tags=["export"])

FIELDS = yaml.safe_load(
    pathlib.Path("app/config_files/fields.yaml").read_text(encoding="utf-8")
)


@router.get("/{bid}/export.xlsx")
def export(bid: int, db: Session = Depends(get_db)):
    b = db.get(Batch, bid)
    if not b:
        raise HTTPException(404)
    buf = export_batch(b, FIELDS)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="batch_{bid}.xlsx"'
        },
    )
