"""WebSocket connection manager for real-time signal streaming."""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Thread-safe manager for active WebSocket connections.

    Maintains a set of connected clients and broadcasts JSON messages
    to all of them concurrently, silently dropping dead connections.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket client."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.debug("WS client connected — total: %d", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected client."""
        async with self._lock:
            self._connections.discard(websocket)
        logger.debug("WS client disconnected — total: %d", len(self._connections))

    async def broadcast(self, data: dict[str, Any]) -> None:
        """Send a JSON message to all connected clients.

        Failed sends (dead sockets) are silently removed so they don't
        block the broadcast for healthy clients.
        """
        message = json.dumps(data)
        async with self._lock:
            connections = set(self._connections)

        dead: set[WebSocket] = set()
        await asyncio.gather(
            *[self._send(ws, message, dead) for ws in connections],
            return_exceptions=True,
        )

        if dead:
            async with self._lock:
                self._connections -= dead

    @staticmethod
    async def _send(ws: WebSocket, message: str, dead: set[WebSocket]) -> None:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Module-level singleton shared across the app
manager: ConnectionManager = ConnectionManager()
