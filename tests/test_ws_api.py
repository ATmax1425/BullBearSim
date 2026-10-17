import asyncio

from websocket import CLIENT_QUEUE_SIZE, ConnectionManager


class FakeSocket:
    def __init__(self):
        self.sent = []

    async def accept(self):
        pass

    async def send_text(self, text):
        self.sent.append(text)


def test_broadcast_reaches_every_client():
    async def scenario():
        manager = ConnectionManager()
        a, b = FakeSocket(), FakeSocket()
        clients = [await manager.connect(a), await manager.connect(b)]
        manager.broadcast("tick")
        for client in clients:
            client.queue.put_nowait(None)
            await client.send_loop()
        return a.sent, b.sent

    assert asyncio.run(scenario()) == (["tick"], ["tick"])


def test_slow_client_is_dropped_without_blocking_others():
    async def scenario():
        manager = ConnectionManager()
        slow = await manager.connect(FakeSocket())
        fast_socket = FakeSocket()
        fast = await manager.connect(fast_socket)

        for i in range(CLIENT_QUEUE_SIZE + 1):
            manager.broadcast(str(i))
            if fast.queue.qsize() > 1:
                fast.queue.get_nowait()  # the fast client keeps up

        assert manager.client_count == 1
        await slow.send_loop()  # returns immediately: told to stop
        return slow.websocket.sent

    assert asyncio.run(scenario()) == []
