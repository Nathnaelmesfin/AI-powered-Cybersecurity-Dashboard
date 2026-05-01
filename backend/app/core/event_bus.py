import asyncio
import json
import os
from typing import Any, Awaitable, Callable

from nats.aio.client import Client as NATS

EVENT_SUBJECT = "sentinelops.events"

_nc: NATS | None = None


def _enabled() -> bool:
    return os.getenv("SENTINELOPS_EVENT_BUS_ENABLED", "0") == "1"


def _nats_url() -> str:
    return os.getenv("SENTINELOPS_NATS_URL", "nats://127.0.0.1:4222")


async def _get_nc() -> NATS:
    global _nc
    if _nc and _nc.is_connected:
        return _nc
    _nc = NATS()
    await _nc.connect(servers=[_nats_url()], connect_timeout=1)
    return _nc


def publish_event(event_type: str, data: dict[str, Any]) -> None:
    if not _enabled():
        return

    async def _pub() -> None:
        try:
            nc = await _get_nc()
            payload = json.dumps({"type": event_type, "data": data}).encode()
            await nc.publish(EVENT_SUBJECT, payload)
        except Exception:
            return

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_pub())
    except RuntimeError:
        asyncio.run(_pub())


async def subscribe_events(handler: Callable[[dict], Awaitable[None]]) -> bool:
    if not _enabled():
        return False
    try:
        nc = await _get_nc()
    except Exception:
        return False

    async def _cb(msg):
        payload = json.loads(msg.data.decode())
        await handler(payload)

    await nc.subscribe(EVENT_SUBJECT, cb=_cb)
    return True
