import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from kafka_consumer import consume_ticks
from websocket import ConnectionManager


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    consumer_task = asyncio.create_task(consume_ticks(manager))
    try:
        yield
    finally:
        consumer_task.cancel()
        with suppress(asyncio.CancelledError):
            await consumer_task


app = FastAPI(lifespan=lifespan)

@app.websocket("/ws")
async def websocket_ticks(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
