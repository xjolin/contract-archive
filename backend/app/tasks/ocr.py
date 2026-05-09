import os
import re
import httpx
from app.config import settings

MAX_LEN = 15000


def _clean(md: str) -> str:
    md = re.sub(r"<[^>]*>", " ", md)
    md = re.sub(r"\s+", " ", md).strip()
    return md[:MAX_LEN]


def run_mineru(pdf_path: str) -> str:
    if not settings.mineru_api_url:
        raise RuntimeError("MINERU_API_URL 未配置")

    fname = os.path.basename(pdf_path)
    with open(pdf_path, "rb") as f:
        resp = httpx.post(
            settings.mineru_api_url,
            files={"files": (fname, f, "application/pdf")},
            timeout=900,
        )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results") or {}
    if not results:
        raise RuntimeError(f"MinerU 返回为空: {data}")

    first_key = next(iter(results))
    md = results[first_key].get("md_content", "")
    if not md:
        raise RuntimeError(f"MinerU md_content 为空: key={first_key}")
    return _clean(md)
