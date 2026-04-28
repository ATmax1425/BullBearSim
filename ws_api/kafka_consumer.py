import json
import os
import asyncio

from aiokafka import AIOKafkaConsumer

from websocket import ConnectionManager


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
CONSUMER_GROUP = os.getenv("WS_API_CONSUMER_GROUP", "ws-broadcast")
TOPIC = "ticks"


async def consume_ticks(manager: ConnectionManager) -> None:
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="latest",
    )

    delay_seconds = 1
    while True:
        try:
            await consumer.start()
            break
        except Exception as exc:
            print(f"Kafka not ready for ws_api consumer: {exc}")
            await asyncio.sleep(delay_seconds)
            delay_seconds = min(delay_seconds * 2, 10)

    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                print(f"Skipping invalid Kafka message: {exc}")
                continue
            await manager.broadcast(data)
            print(data)
    finally:
        await consumer.stop()
