import asyncio
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket

from app.api.auth import router as auth_router
from app.api.routes import router
from app.core.db import SessionLocal, init_db
from app.core.event_bus import subscribe_events
from app.services import store

app = FastAPI(title="SentinelOps AI API", version="0.5.0")
app.include_router(auth_router)
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    with SessionLocal() as db:
        store.seed_defaults(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sentinelops-api"}


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        with SessionLocal() as db:
            summary = store.summary(db).model_dump()
        await websocket.send_json({"timestamp": datetime.now(timezone.utc).isoformat(), "summary": summary, "message": "Live SentinelOps dashboard feed"})
        await asyncio.sleep(2)


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    async def handler(evt: dict):
        await queue.put(evt)

    subscribed = await subscribe_events(handler)
    if not subscribed:
        await websocket.send_json({"type": "info", "data": {"message": "event bus disabled"}})
    while True:
        evt = await queue.get() if subscribed else {"type": "heartbeat", "data": {"ts": datetime.now(timezone.utc).isoformat()}}
        await websocket.send_json(evt)
        if not subscribed:
            await asyncio.sleep(5)
