from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine
from app.models import Base
from app.api import batches, documents, stream, export

Base.metadata.create_all(engine)

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


@app.get("/health")
def health():
    return {"ok": True}
