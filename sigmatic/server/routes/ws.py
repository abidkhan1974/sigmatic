"""WebSocket endpoints for real-time signal streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from sigmatic.server.websocket.manager import manager

ws_router = APIRouter()


@ws_router.websocket("/ws/signals")
async def signals_stream(websocket: WebSocket) -> None:
    """Stream new signals in real time.

    Connect with any WebSocket client:
        wscat -c ws://localhost:8000/v1/ws/signals

    Each message is a JSON object matching the WebhookIngestResponse schema.
    The connection stays open until the client disconnects.
    No auth is required — signals contain no credentials and the endpoint
    is read-only.  Add auth at the CORS / reverse-proxy layer if needed.
    """
    await manager.connect(websocket)
    try:
        # Keep the connection alive; we don't expect incoming messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
