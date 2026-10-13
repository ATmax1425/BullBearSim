"""
consumer_to_db.py
Consumes messages from Kafka and stores them in TimescaleDB.

Offsets are committed only after a batch is written, so a crash or restart
re-delivers unwritten ticks instead of losing them (duplicates are ignored
by the ON CONFLICT clause).
"""

import asyncio
import logging
import os
import signal

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from helper import TickWriter, parse_tick

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = "ticks"
BATCH_SIZE = 50
FLUSH_INTERVAL = 2.0  # seconds; flush a partial batch at least this often

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consumer")


async def start_consumer() -> AIOKafkaConsumer:
    delay = 1
    while True:
        consumer = AIOKafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id="db-writer",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        try:
            await consumer.start()
            return consumer
        except KafkaError as exc:
            log.warning("Kafka not ready (%s), retrying in %ss", exc, delay)
            await consumer.stop()
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)


async def consume(stop: asyncio.Event) -> None:
    writer = TickWriter()
    log.info("Connecting to Kafka...")
    consumer = await start_consumer()
    log.info("Consumer connected to Kafka, writing to DB...")

    loop = asyncio.get_running_loop()
    batch = []
    uncommitted = False
    last_flush = loop.time()

    async def flush() -> None:
        nonlocal uncommitted, last_flush
        if batch:
            await asyncio.to_thread(writer.write, list(batch))
            batch.clear()
        if uncommitted:
            await consumer.commit()
            uncommitted = False
        last_flush = loop.time()

    try:
        while not stop.is_set():
            records = await consumer.getmany(timeout_ms=500, max_records=500)
            for messages in records.values():
                for msg in messages:
                    uncommitted = True
                    row = parse_tick(msg.value)
                    if row is None:
                        log.warning("Skipping invalid message at offset %s", msg.offset)
                        continue
                    batch.append(row)

            if len(batch) >= BATCH_SIZE or loop.time() - last_flush >= FLUSH_INTERVAL:
                await flush()
        await flush()
    finally:
        log.info("Shutting down consumer...")
        await consumer.stop()
        writer.close()


async def main() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await consume(stop)


if __name__ == "__main__":
    asyncio.run(main())
