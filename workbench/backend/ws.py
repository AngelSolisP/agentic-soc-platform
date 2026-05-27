"""WebSocket handlers for real-time pipeline progress and notifications."""
import asyncio
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from workbench.backend.security import authenticate_websocket, validate_client_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class NotificationHub:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    def add(self, queue: asyncio.Queue) -> None:
        self._subscribers.append(queue)

    def remove(self, queue: asyncio.Queue) -> None:
        self._subscribers = [q for q in self._subscribers if q is not queue]

    async def broadcast(self, message: dict[str, Any]) -> None:
        for queue in self._subscribers:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.debug("Dropping notification for full subscriber queue")


notification_hub = NotificationHub()


@router.websocket("/ws/pipeline/{case_id}")
async def ws_pipeline(websocket: WebSocket, case_id: str):
    # OWASP A01: Authenticate before accepting WebSocket connection
    analyst = await authenticate_websocket(websocket)
    if not analyst:
        await websocket.accept()
        await websocket.close(code=4001, reason="Authentication required")
        return

    # OWASP A01: Require client_id for tenant isolation
    client_id = websocket.query_params.get("client_id", "")
    try:
        validate_client_id(client_id)
    except Exception:
        await websocket.accept()
        await websocket.close(code=4002, reason="Invalid client_id")
        return

    # Verify analyst is authorized for this client
    allowed = analyst.get("allowed_clients", [])
    if analyst.get("role") != "admin" and client_id not in allowed:
        await websocket.accept()
        await websocket.close(code=4003, reason="Not authorized for client")
        return

    await websocket.accept()
    logger.info("Pipeline WebSocket connected", extra={"case_id": case_id, "client_id": client_id})

    known_stages: dict[str, dict] = {}
    consecutive_errors = 0
    poll_interval = 2.0
    max_consecutive_errors = 10
    max_poll_interval = 60.0

    try:
        while True:
            try:
                db = websocket.app.state.db
                # Tenant isolation: filter by BOTH case_id AND client_id
                stages = (
                    db.collection("workflow_stages")
                    .where("case_id", "==", case_id)
                    .where("client_id", "==", client_id)
                    .order_by("stage_order")
                    .stream()
                )

                for stage_doc in stages:
                    stage = stage_doc.to_dict()
                    stage_id = stage.get("stage_id", stage_doc.id)
                    old = known_stages.get(stage_id)

                    if old is None or old.get("status") != stage.get("status"):
                        known_stages[stage_id] = stage
                        await websocket.send_json({
                            "type": "stage_update",
                            "case_id": case_id,
                            "stage": _serialize_stage(stage),
                        })

                # Success: reset backoff
                consecutive_errors = 0
                poll_interval = 2.0

            except Exception as e:
                consecutive_errors += 1
                poll_interval = min(2.0 * (2 ** consecutive_errors), max_poll_interval)
                logger.warning(
                    "Pipeline poll error (%d/%d), next in %.0fs: %s",
                    consecutive_errors, max_consecutive_errors, poll_interval, e,
                )
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Max poll errors reached, closing WebSocket for case %s", case_id)
                    if websocket.application_state == WebSocketState.CONNECTED:
                        await websocket.send_json({"type": "error", "message": "Data source unavailable"})
                        await websocket.close(code=1011, reason="Data source unavailable")
                    return

            await asyncio.sleep(poll_interval)
    except WebSocketDisconnect:
        logger.info("Pipeline WebSocket disconnected", extra={"case_id": case_id})


@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    # OWASP A01: Authenticate before accepting WebSocket connection
    analyst = await authenticate_websocket(websocket)
    if not analyst:
        # Must accept() before close() so client sees the 4001 code
        # instead of a raw HTTP 403 (which maps to code 1006 in browsers
        # and bypasses the frontend's "don't reconnect" logic).
        await websocket.accept()
        await websocket.close(code=4001, reason="Authentication required")
        return

    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    notification_hub.add(queue)
    logger.info("Notifications WebSocket connected", extra={"analyst": analyst.get("email")})

    try:
        while True:
            message = await queue.get()
            # Tenant isolation: only send notifications for analyst's allowed clients
            allowed = analyst.get("allowed_clients", [])
            msg_client = message.get("client_id", "")
            if analyst.get("role") == "admin" or not msg_client or msg_client in allowed:
                await websocket.send_json(message)
    except WebSocketDisconnect:
        pass
    finally:
        notification_hub.remove(queue)
        logger.info("Notifications WebSocket disconnected")


def _serialize_stage(stage: dict) -> dict:
    return {
        "stage_id": stage.get("stage_id"),
        "stage_name": stage.get("stage_name"),
        "stage_order": stage.get("stage_order"),
        "status": stage.get("status"),
        "duration_seconds": stage.get("duration_seconds"),
        "output_structured": stage.get("output_structured"),
        "error": stage.get("error"),
        "started_at": stage.get("started_at"),
        "completed_at": stage.get("completed_at"),
    }
