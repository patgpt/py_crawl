from sse_starlette.sse import EventSourceResponse
from fastapi import Request
import asyncio
from typing import AsyncGenerator

class EventBroadcaster:
    def __init__(self):
        self.connections = set()
        self.message_queue = asyncio.Queue()

    async def subscribe(self, request: Request) -> AsyncGenerator:
        """Subscribe a client to receive events"""
        try:
            while True:
                message = await self.message_queue.get()
                yield message
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            self.connections.remove(request)

    async def broadcast(self, message: str, event_type: str = "message"):
        """Broadcast a message to all connected clients"""
        await self.message_queue.put({
            "event": event_type,
            "data": message
        })

# Global broadcaster instance
broadcaster = EventBroadcaster()