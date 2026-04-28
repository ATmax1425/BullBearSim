import asyncio
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)
        try:
            await websocket.close()
        except Exception:
            pass

    async def broadcast(self, message: dict) -> None:
        async with self._lock:
            clients = list(self._clients)

        stale_clients = []

        async def send(client: WebSocket):
            try:
                await client.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                stale_clients.append(client)

        await asyncio.gather(*(send(c) for c in clients))

        for client in stale_clients:
            await self.disconnect(client)