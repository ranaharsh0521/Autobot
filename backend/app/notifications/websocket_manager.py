import logging
import json
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketConnectionManager:
    """
    WebSocket Connection Registry and Event Broadcaster for React Frontend Clients.
    Supports standard events: MARKET_UPDATE, SCAN_STARTED, SCAN_COMPLETED, AGENT_UPDATE,
    DEBATE_UPDATE, TRADE_SIGNAL, RISK_REJECTION, PAPER_TRADE, ERROR.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🟢 [WebSocket] Client connected. Total active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"🔴 [WebSocket] Client disconnected. Remaining active clients: {len(self.active_connections)}")

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Generic structured event broadcaster for any event type."""
        if not self.active_connections:
            return

        payload = {
            "type": event_type,
            "timestamp": data.get("timestamp"),
            "data": data
        }

        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.warning(f"[WebSocket] Failed to send {event_type} event: {str(e)}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    async def broadcast_signal(self, signal_data: Dict[str, Any]):
        """Broadcast TRADE_SIGNAL to connected clients."""
        await self.broadcast_event("TRADE_SIGNAL", signal_data)

    async def broadcast_status(self, status_data: Dict[str, Any]):
        """Broadcast MARKET_UPDATE / SYSTEM_STATUS updates."""
        await self.broadcast_event("MARKET_UPDATE", status_data)

    async def broadcast_risk_rejection(self, rejection_data: Dict[str, Any]):
        """Broadcast RISK_REJECTION events."""
        await self.broadcast_event("RISK_REJECTION", rejection_data)

    async def broadcast_paper_trade(self, trade_data: Dict[str, Any]):
        """Broadcast PAPER_TRADE execution events."""
        await self.broadcast_event("PAPER_TRADE", trade_data)

    async def broadcast_error(self, error_message: str, details: Dict[str, Any] = None):
        """Broadcast ERROR events."""
        await self.broadcast_event("ERROR", {"message": error_message, "details": details or {}})

ws_manager = WebSocketConnectionManager()
