from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as aioredis
from app.config import settings

router = APIRouter(tags=["stream"])


@router.get("/api/batches/{bid}/stream")
async def stream(bid: int):
    r = aioredis.from_url(settings.redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe(f"batch:{bid}")

    async def gen():
        try:
            while True:
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=15
                )
                if msg:
                    yield {"data": msg["data"].decode()}
                else:
                    yield {"event": "ping", "data": "1"}
        finally:
            await pubsub.unsubscribe()
            await r.close()

    return EventSourceResponse(gen())
