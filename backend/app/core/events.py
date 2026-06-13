"""Redis pub/sub bridge between Celery workers and FastAPI WebSocket clients.

Workers run in separate processes and cannot reach a browser socket directly.
They publish JSON progress events to a Redis channel; FastAPI WebSocket
handlers subscribe to that channel and forward messages to the client.
"""

import json
from collections.abc import AsyncIterator
from typing import Any

import redis
import redis.asyncio as aioredis

from app.core.config import settings

_sync_client: redis.Redis | None = None


def _get_sync_client() -> redis.Redis:
    global _sync_client
    if _sync_client is None:
        _sync_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _sync_client


def experiment_channel(experiment_id: int) -> str:
    return f"experiment:{experiment_id}"


def cleaning_channel(dataset_id: int) -> str:
    return f"dataset:{dataset_id}:clean"


def publish(channel: str, payload: dict[str, Any]) -> None:
    """Publish a JSON event to a channel. Called from synchronous Celery workers."""
    _get_sync_client().publish(channel, json.dumps(payload))


async def subscribe(channel: str) -> AsyncIterator[dict[str, Any]]:
    """Yield JSON events from a channel. Used by async FastAPI WebSocket handlers."""
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                yield json.loads(message["data"])
            except (ValueError, TypeError):
                continue
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await client.aclose()
