import asyncio
import logging

from fastapi import WebSocket

log = logging.getLogger("ws_api")

# Messages buffered per client before it is considered too slow and dropped.
CLIENT_QUEUE_SIZE = 200


class Client:
    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket
        self.queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=CLIENT_QUEUE_SIZE)

    async def send_loop(self) -> None:
        """Forward queued messages to the socket; a None message ends the loop."""
        while True:
            message = await self.queue.get()
            if message is None:
                return
            await self.websocket.send_text(message)

    def close_soon(self) -> None:
        """Discard pending messages and tell send_loop to stop."""
        while not self.queue.empty():
            self.queue.get_nowait()
        self.queue.put_nowait(None)


class ConnectionManager:
    def __init__(self) -> None:
        self._clients: set[Client] = set()

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def connect(self, websocket: WebSocket) -> Client:
        await websocket.accept()
        client = Client(websocket)
        self._clients.add(client)
        return client

    def disconnect(self, client: Client) -> None:
        self._clients.discard(client)

    def broadcast(self, message: str) -> None:
        """Queue a message for every client without waiting on any of them."""
        for client in list(self._clients):
            try:
                client.queue.put_nowait(message)
            except asyncio.QueueFull:
                log.warning("Dropping slow WebSocket client")
                self.disconnect(client)
                client.close_soon()
