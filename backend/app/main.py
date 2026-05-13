import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db import engine
from app.models import Base
from app.api import batches, documents, stream, export

app = FastAPI(title="Contract Archive")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(batches.router)
app.include_router(documents.router)
app.include_router(stream.router)
app.include_router(export.router)

@app.on_event("startup")
def _startup():
    last_err: Exception | None = None
    for _ in range(120):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(engine)
            return
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise last_err or RuntimeError("DB 连接失败")


@app.get("/health")
def health():
    return {"ok": True}
