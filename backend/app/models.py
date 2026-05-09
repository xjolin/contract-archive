from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, Text, func


class Base(DeclarativeBase):
    pass


class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="running")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    documents: Mapped[list["Document"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    filename: Mapped[str] = mapped_column(String(300))
    path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    batch: Mapped["Batch"] = relationship(back_populates="documents")
