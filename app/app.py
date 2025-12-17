
import asyncio
import json
import random
import os
from datetime import datetime, timezone, time, timedelta

from aiokafka import AIOKafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC_TICKS = "ticks"

SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY"]

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

def is_market_open(ts: datetime) -> bool:
    ist_ts = ts + timedelta(hours=5, minutes=30)
    if ist_ts.weekday() >= 5:
        return False
    return MARKET_OPEN <= ist_ts.time() <= MARKET_CLOSE


async def tick_producer():
    print("Starting tick producer...")
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await producer.start()
    print("Producer started")

    prices = {s: 1000.0 + random.uniform(-10, 10) for s in SYMBOLS}
    vols = {s: 0.01 for s in SYMBOLS}

    try:
        while True:
            ts = datetime.now(timezone.utc)
            # todo test
            # if not is_market_open(ts):
            if is_market_open(ts):
                print("Market closed, sleeping...")
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

                await producer.send_and_wait(
                    TOPIC_TICKS, json.dumps(msg).encode()
                )

            await asyncio.sleep(1)

    finally:
        await producer.stop()

async def main():
    await asyncio.gather(
        tick_producer()
    )

if __name__ == "__main__":
    asyncio.run(main())
