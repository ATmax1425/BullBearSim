"""
app.py (FastAPI + Kafka + WebSocket)
Using Lifespan instead of deprecated on_event
"""

import asyncio
import json
import random
from datetime import datetime, timezone, time, timedelta
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from aiokafka import AIOKafkaProducer
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

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

def is_market_open(ts: datetime) -> bool:
    ist_offset = timedelta(hours=5, minutes=30)
    ist_ts = ts + ist_offset

    if ist_ts.weekday() >= 5:
        return False
    return MARKET_OPEN <= ist_ts.time() <= MARKET_CLOSE


async def tick_producer_task():
    """
    Simulates stock ticks and produces them to Kafka.
    Added more realism
    """
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await producer.start()
    print("producer.start()")
    try:
        prices = {s: 100.0 + random.uniform(-10, 10) for s in SYMBOLS}
        vols = {s: 0.01 for s in SYMBOLS}

        while True:
            ts = datetime.now(timezone.utc)

            if not is_market_open(ts):
                # Market closed → sleep until next minute
                await asyncio.sleep(60)
                continue

            market_factor = random.gauss(0, 0.001)

            for s in SYMBOLS:
                if random.random() < 0.05:
                    vols[s] = max(0.001, vols[s] * random.uniform(0.5, 1.5))

                drift = 0.0002
                indiv_move = random.gauss(drift, vols[s])
                delta = market_factor + indiv_move

                old_price = prices[s]
                prices[s] = max(1, prices[s] * (1 + delta))

                base_vol = 100
                vol_spike = int(abs(prices[s] - old_price) * 5000)
                volume = max(1, int(random.gauss(base_vol + vol_spike, 30)))

                msg = {
                    "ts": ts.isoformat(),
                    "symbol": s,
                    "price": round(prices[s], 2),
                    "volume": volume,
                }
                # print(msg)
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
