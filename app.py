"""
app.py (FastAPI + Kafka + WebSocket)
Using Lifespan instead of deprecated on_event
"""

import asyncio
import json
import random
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_TICKS = "ticks"
SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY"]

# --------------------------
# WebSocket Connection Manager
# --------------------------
class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self.lock:
            self.active.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self.lock:
            self.active.discard(ws)

    async def broadcast(self, message: str):
        async with self.lock:
            to_drop = []
            for ws in list(self.active):
                try:
                    await ws.send_text(message)
                except Exception:
                    to_drop.append(ws)
            for ws in to_drop:
                self.active.discard(ws)

manager = ConnectionManager()

# --------------------------
# Producer + Consumer Tasks
# --------------------------
async def tick_producer_task():
    """Simulates stock ticks and produces them to Kafka."""
    from aiokafka import AIOKafkaProducer
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await producer.start()
    try:
        prices = {s: 1000.0 for s in SYMBOLS}
        while True:
            for s in SYMBOLS:
                prices[s] += random.uniform(-50.0, 50.0)
                msg = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "symbol": s,
                    "price": round(prices[s], 2),
                    "volume": random.randint(10, 500),
                }
                await producer.send_and_wait(TOPIC_TICKS, json.dumps(msg).encode())
            await asyncio.sleep(1)
    finally:
        await producer.stop()

async def kafka_consumer_task():
    """Consumes from Kafka and forwards messages to WebSocket clients."""
    consumer = AIOKafkaConsumer(
        TOPIC_TICKS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="latest",
        group_id="fastapi-consumer",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            raw = msg.value.decode("utf-8")
            await manager.broadcast(raw)
    finally:
        await consumer.stop()

# --------------------------
# Lifespan Context Manager
# --------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    producer_task = asyncio.create_task(tick_producer_task())
    consumer_task = asyncio.create_task(kafka_consumer_task())
    app.state.tasks = [producer_task, consumer_task]
    print("Kafka producer and consumer started.")
    yield
    # Shutdown
    for t in app.state.tasks:
        t.cancel()
    await asyncio.gather(*app.state.tasks, return_exceptions=True)
    print("Kafka producer and consumer stopped.")

# --------------------------
# FastAPI Application
# --------------------------
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"msg": "Real-time Kafka → FastAPI → WebSocket demo", "ws": "/ws"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        await manager.disconnect(ws)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
