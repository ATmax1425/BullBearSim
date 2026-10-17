import asyncio
import json
import logging
import os
import time

from aiokafka import AIOKafkaConsumer

from websocket import ConnectionManager


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = "ticks"

log = logging.getLogger("ws_api")


class ConsumerStatus:
    def __init__(self) -> None:
        self.connected = False
        self.last_message_at: float | None = None


async def consume_ticks(manager: ConnectionManager, status: ConsumerStatus) -> None:
    """Relay ticks from Kafka to WebSocket clients, reconnecting on any failure."""
    delay = 1
    while True:
        # No consumer group: this is a live relay, so every (re)start begins at
        # the latest offset instead of replaying ticks missed while it was down.
        consumer = AIOKafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id=None,
            auto_offset_reset="latest",
        )
        try:
            await consumer.start()
            status.connected = True
            delay = 1
            log.info("Connected to Kafka, relaying ticks")

            async for msg in consumer:
                try:
                    text = msg.value.decode("utf-8")
                    json.loads(text)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    log.warning("Skipping invalid Kafka message: %s", exc)
                    continue
                status.last_message_at = time.time()
                manager.broadcast(text)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.warning("Kafka consumer error (%s), restarting in %ss", exc, delay)
        finally:
            status.connected = False
            await consumer.stop()

        await asyncio.sleep(delay)
        delay = min(delay * 2, 30)
