"""
consumer_to_db.py
Consumes messages from Kafka and stores them in TimescaleDB
"""

import asyncio
import json
import os
from helper import get_psql_conn, safe_batch_insert
from aiokafka import AIOKafkaConsumer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = "ticks"
BATCH_SIZE = 50

async def consume():
    # Connect to Postgres
    print("Connecting to Postgres...")
    conn = get_psql_conn()
    cur = conn.cursor()

    # Kafka consumer
    print("Connecting to Kafka...")
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="db-writer",
        auto_offset_reset="earliest"
    )
    # Wait until Kafka is ready
    for attempt in range(5):
        print("Waiting for Kafka to be ready...")
        try:
            await consumer.start()
            break
        except Exception as e:
            print(f"Kafka not ready ({attempt+1}/5): {e}")
            await asyncio.sleep(5)
    else:
        print("Failed to connect to Kafka after several attempts.")
        return
    print("Consumer connected to Kafka, writing to DB...")

    batch = []
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))
            batch.append((data["ts"], data["symbol"], data["price"], data["volume"]))
            if len(batch) >= BATCH_SIZE:
                conn, cur = await asyncio.to_thread(safe_batch_insert, conn, cur, batch)
                batch.clear()
                # print("commit done")
    finally:
        if batch:
            conn, cur = await asyncio.to_thread(safe_batch_insert, conn, cur, batch)
        await consumer.stop()
        cur.close()
        conn.close()

if __name__ == "__main__":
    asyncio.run(consume())
