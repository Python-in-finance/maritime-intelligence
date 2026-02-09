import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.position_subscribers: Set[str] = set()
        
    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        conn_id = f"conn_{id(websocket)}"
        self.active_connections[conn_id] = websocket
        return conn_id
        
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        self.position_subscribers.discard(connection_id)
        
    async def broadcast_position_update(self, positions: list):
        message = {
            "type": "position_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": positions
        }
        for conn_id in list(self.position_subscribers):
            if conn_id in self.active_connections:
                try:
                    await self.active_connections[conn_id].send_json(message)
                except:
                    self.disconnect(conn_id)

websocket_manager = WebSocketManager()
