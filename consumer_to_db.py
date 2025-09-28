"""
consumer_to_db.py
Consumes messages from Kafka and stores them in TimescaleDB
"""

import asyncio
import json
from helper import get_psql_conn
from aiokafka import AIOKafkaConsumer

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC = "ticks"

async def consume():
    # Connect to Postgres
    conn = get_psql_conn()
    cur = conn.cursor()

    # Kafka consumer
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="db-writer"
    )
    await consumer.start()
    print("✅ Consumer connected to Kafka, writing to DB...")

    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))
            cur.execute(
                "INSERT INTO ticks (ts, symbol, price, volume) VALUES (%s, %s, %s, %s)",
                (data["ts"], data["symbol"], data["price"], data["volume"])
            )
            conn.commit()
            # print("commit done")
    finally:
        await consumer.stop()
        cur.close()
        conn.close()

if __name__ == "__main__":
    asyncio.run(consume())
