from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import websocket_manager

router = APIRouter()

@router.websocket("/ws/vessels/positions")
async def vessel_positions_websocket(websocket: WebSocket):
    connection_id = await websocket_manager.connect(websocket)
    websocket_manager.position_subscribers.add(connection_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(connection_id)
