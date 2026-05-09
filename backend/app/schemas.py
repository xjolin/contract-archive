from pydantic import BaseModel
from datetime import datetime


class DocumentOut(BaseModel):
    id: int
    filename: str
    status: str
    retry_count: int
    error: str | None
    extracted_json: dict | None

    class Config:
        from_attributes = True


class BatchOut(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    documents: list[DocumentOut]

    class Config:
        from_attributes = True
