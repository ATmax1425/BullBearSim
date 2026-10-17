"""
app.py
Market tick producer: steps the market simulation once per second and
publishes one tick per symbol to Kafka.
"""

import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from simulation import MarketSimulator


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC_TICKS = "ticks"
TICK_INTERVAL = 1.0  # seconds

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("producer")


async def start_producer() -> AIOKafkaProducer:
    delay = 1
    while True:
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
        try:
            await producer.start()
            return producer
        except KafkaError as exc:
            log.warning("Kafka not ready (%s), retrying in %ss", exc, delay)
            await producer.stop()
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)


async def tick_producer(stop: asyncio.Event) -> None:
    log.info("Starting tick producer...")
    producer = await start_producer()
    log.info("Producer started")

    sim = MarketSimulator()
    loop = asyncio.get_running_loop()
    next_tick = loop.time()

    try:
        while not stop.is_set():
            ts = datetime.now(timezone.utc)
            ticks = sim.step(ts, dt=TICK_INTERVAL)

            try:
                # Queue every symbol first, then wait for all acks together.
                futures = [
                    await producer.send(
                        TOPIC_TICKS,
                        key=symbol.encode(),
                        value=json.dumps({
                            "ts": ts.isoformat(timespec="milliseconds"),
                            "symbol": symbol,
                            "price": price,
                            "volume": volume,
                        }).encode(),
                    )
                    for symbol, price, volume in ticks
                ]
                await asyncio.gather(*futures)
            except KafkaError as exc:
                # The client reconnects on its own; drop this tick and carry on.
                log.warning("Failed to publish tick: %s", exc)

            # Fixed cadence: schedule from the previous tick, not from "now".
            next_tick += TICK_INTERVAL
            delay = next_tick - loop.time()
            if delay < 0:
                next_tick = loop.time()
                delay = 0
            try:
                await asyncio.wait_for(stop.wait(), timeout=delay)
            except asyncio.TimeoutError:
                pass
    finally:
        log.info("Stopping producer...")
        await producer.stop()


async def main() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await tick_producer(stop)


if __name__ == "__main__":
    asyncio.run(main())
