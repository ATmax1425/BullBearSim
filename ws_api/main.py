import asyncio
import logging
import time
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

from kafka_consumer import ConsumerStatus, consume_ticks
from websocket import ConnectionManager


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# The producer publishes every second; no tick for this long means the stream is down.
STALE_AFTER_S = 15

manager = ConnectionManager()
status = ConsumerStatus()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    consumer_task = asyncio.create_task(consume_ticks(manager, status))
    try:
        yield
    finally:
        consumer_task.cancel()
        with suppress(asyncio.CancelledError):
            await consumer_task


app = FastAPI(lifespan=lifespan)


@app.get("/ws/health")
async def health():
    age = None
    if status.last_message_at is not None:
        age = round(time.time() - status.last_message_at, 1)
    if not status.connected:
        state = "kafka_disconnected"
    elif age is None or age > STALE_AFTER_S:
        state = "no_recent_ticks"
    else:
        state = "ok"
    body = {
        "status": state,
        "connections": manager.client_count,
        "last_message_age_s": age,
    }
    return JSONResponse(body, status_code=200 if state == "ok" else 503)


async def _wait_for_disconnect(websocket: WebSocket) -> None:
    while True:
        message = await websocket.receive()
        if message["type"] == "websocket.disconnect":
            return


@app.websocket("/ws")
async def websocket_ticks(websocket: WebSocket) -> None:
    client = await manager.connect(websocket)
    sender = asyncio.create_task(client.send_loop())
    receiver = asyncio.create_task(_wait_for_disconnect(websocket))
    try:
        await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        manager.disconnect(client)
        for task in (sender, receiver):
            task.cancel()
        # Retrieve results so errors from a closed socket are not logged as unhandled.
        await asyncio.gather(sender, receiver, return_exceptions=True)
        with suppress(Exception):
            await websocket.close()
