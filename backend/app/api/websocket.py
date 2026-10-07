"""WebSocket Real-Time Telemetry Streaming

Broadcasts live network telemetry, AI predictions, confidence, stability scores,
and degradation alerts to connected frontend dashboards.
"""

import json
import logging
import asyncio
from typing import Set, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.collector.telemetry import telemetry_service
from app.ml.service import prediction_engine
from app.schemas.network import NetworkTelemetry

logger = logging.getLogger(__name__)

ws_router = APIRouter()


class TelemetryConnectionManager:
    """Manages active WebSocket dashboard clients and broadcasts live telemetry packets."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._subscriber_registered: bool = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Dashboard client connected. Active connections: {len(self.active_connections)}")

        if not self._subscriber_registered:
            telemetry_service.add_subscriber(self._on_telemetry_event)
            self._subscriber_registered = True

        # Send initial immediate snapshot if available
        latest = telemetry_service.get_latest_telemetry()
        if latest is not None:
            await self._send_payload(websocket, self._build_payload(latest))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Dashboard client disconnected. Active connections: {len(self.active_connections)}")

    def _on_telemetry_event(self, telemetry: NetworkTelemetry):
        """Callback invoked whenever telemetry service produces a new measurement."""
        if not self.active_connections:
            return

        payload = self._build_payload(telemetry)
        # Broadcast asynchronously to all connected clients
        asyncio.create_task(self.broadcast(payload))

    def _build_payload(self, telemetry: NetworkTelemetry) -> Dict[str, Any]:
        """Synthesizes unified live dashboard packet."""
        telem_dict = telemetry.model_dump()
        history = telemetry_service.get_telemetry_history(6)

        # Generate ML prediction and stability score
        pred_res = prediction_engine.predict_telemetry(telem_dict, recent_history=history)

        # Detect degradation trends
        alerts = prediction_engine.degradation_detector.analyze_trend(
            history=history,
            current_prediction=pred_res.predicted_class
        )

        return {
            "type": "telemetry_update",
            "telemetry": telem_dict,
            "prediction": {
                "predicted_class": pred_res.predicted_class,
                "confidence": pred_res.confidence,
                "confidence_percentage": pred_res.confidence_percentage,
                "class_probabilities": pred_res.class_probabilities,
                "stability_score": pred_res.stability_score,
                "stability_grade": pred_res.stability_grade,
                "explanation": pred_res.explanation.model_dump(),
                "future_forecast": pred_res.future_forecast.model_dump() if pred_res.future_forecast else None,
                "model_name": pred_res.model_name
            },
            "alerts": [a.to_dict() for a in alerts]
        }

    async def _send_payload(self, websocket: WebSocket, payload: Dict[str, Any]):
        try:
            # Serializing datetimes to ISO strings
            await websocket.send_text(json.dumps(payload, default=str))
        except Exception as exc:
            logger.debug(f"Error sending to WebSocket client: {exc}")

    async def broadcast(self, payload: Dict[str, Any]):
        dead_connections = set()
        msg_text = json.dumps(payload, default=str)

        for connection in list(self.active_connections):
            try:
                await connection.send_text(msg_text)
            except Exception:
                dead_connections.add(connection)

        for dead in dead_connections:
            self.disconnect(dead)


ws_manager = TelemetryConnectionManager()


@ws_router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Listen for client-side events / pings
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "collect_now":
                    telemetry_service.collect_now()
                elif msg.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.debug(f"WebSocket session terminated: {exc}")
        ws_manager.disconnect(websocket)
