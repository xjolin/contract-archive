import json
import redis
from loguru import logger
from app.tasks.celery_app import celery
from app.tasks.ocr import run_mineru
from app.tasks.llm import extract_fields
from app.db import SessionLocal
from app.models import Document
from app.config import settings

r = redis.from_url(settings.redis_url)


def _publish(batch_id: int, doc_id: int, status: str):
    r.publish(
        f"batch:{batch_id}",
        json.dumps({"doc_id": doc_id, "status": status}),
    )


def _update(doc_id: int, status: str, **fields):
    with SessionLocal() as s:
        d = s.get(Document, doc_id)
        d.status = status
        for k, v in fields.items():
            setattr(d, k, v)
        s.commit()
        _publish(d.batch_id, d.id, status)


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def process_document(self, doc_id: int):
    logger.info(f"[doc {doc_id}] start, retry={self.request.retries}")
    try:
        with SessionLocal() as s:
            d = s.get(Document, doc_id)
            path = d.path
            d.error = None
            s.commit()

        _update(doc_id, "ocr_running")
        text = run_mineru(path)

        _update(doc_id, "llm_running", ocr_text=text)
        data = extract_fields(text)

        _update(doc_id, "done", extracted_json=data)
        logger.info(f"[doc {doc_id}] done")
    except Exception as e:
        logger.exception(f"[doc {doc_id}] error: {e}")
        with SessionLocal() as s:
            d = s.get(Document, doc_id)
            d.retry_count += 1
            d.error = str(e)[:1900]
            s.commit()
        if self.request.retries >= self.max_retries:
            _update(doc_id, "failed")
        raise
