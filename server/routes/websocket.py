# server/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.embeddings import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive by waiting for messages
            # The client doesn't need to send anything, this just maintains the connection
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket client disconnected") 