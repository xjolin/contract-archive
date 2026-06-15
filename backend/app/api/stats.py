from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Batch, Document

router = APIRouter(prefix="/api/stats", tags=["stats"])

# 忽略名字包含 test 的批次（不区分大小写）
NOT_TEST = ~Batch.name.ilike("%test%")


def _week_start(dt: datetime) -> datetime:
    """返回所在自然周的周一 00:00。"""
    d = dt.date()
    monday = d - timedelta(days=d.weekday())
    return datetime(monday.year, monday.month, monday.day)


@router.get("")
def stats(weeks: int = 12, db: Session = Depends(get_db)):
    cur_week = _week_start(datetime.now())

    # 每个文档对应的批次创建时间与文档状态（已排除 test 批次）
    rows = (
        db.query(Batch.created_at, Document.status)
        .join(Document, Document.batch_id == Batch.id)
        .filter(NOT_TEST)
        .all()
    )

    # 按周统计「已处理（done）」文件数
    weekly_docs: dict[datetime, int] = defaultdict(int)
    for created_at, status in rows:
        if status == "done":
            weekly_docs[_week_start(created_at)] += 1

    # 使用次数 = 本周创建的批次数（已排除 test 批次）
    batch_weeks = [
        _week_start(c) for (c,) in db.query(Batch.created_at).filter(NOT_TEST).all()
    ]
    this_week_usage = sum(1 for w in batch_weeks if w == cur_week)
    this_week_docs = weekly_docs.get(cur_week, 0)

    # 最近 N 周的处理量序列（含 0 值的空周）
    series = []
    for i in range(weeks - 1, -1, -1):
        wk = cur_week - timedelta(weeks=i)
        series.append({"week": wk.strftime("%Y-%m-%d"), "count": weekly_docs.get(wk, 0)})

    return {
        "this_week_usage": this_week_usage,
        "this_week_docs": this_week_docs,
        "weekly": series,
    }
