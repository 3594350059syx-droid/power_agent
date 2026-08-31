"""Week 6-A WebSocket 实时遥测接口。"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.telemetry import get_live_telemetry
from backend.services.realtime_service import manager
from backend.services.telemetry_service import DEVICE_METRICS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["realtime"])


def _telemetry_event(device_id: str, response: dict) -> dict:
    """将 HTTP 遥测响应转换为稳定的 WebSocket 事件契约。"""
    return {
        "type": "telemetry",
        "event": "telemetry_snapshot",
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": response.get("data", {}) if isinstance(response, dict) else {},
    }


async def _send_snapshot(websocket: WebSocket, device_id: str) -> bool:
    response = get_live_telemetry(device_id)
    return await manager.send_json(websocket, _telemetry_event(device_id, response))


@router.websocket("/ws/telemetry/{device_id}")
async def telemetry_websocket(websocket: WebSocket, device_id: str) -> None:
    """订阅设备实时遥测。

    连接建立后立即发送快照，随后每 3 秒推送一次。客户端发送 ``ping``
    返回 ``pong``，其它文本消息触发一次立即刷新。未知设备收到 error
    事件后以 1008 关闭，避免建立一个永远没有有效数据的订阅。
    """
    if device_id not in DEVICE_METRICS:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "event": "telemetry_error",
            "device_id": device_id,
            "message": "unknown device",
        })
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, device_id)
    receive_task = None
    try:
        if not await _send_snapshot(websocket, device_id):
            return

        # 接收与定时推送并行，避免客户端持续发送 ping 时重置 3 秒推送计时器。
        receive_task = asyncio.create_task(websocket.receive_text())
        next_snapshot_at = asyncio.get_running_loop().time() + 3.0
        while True:
            timeout = max(0.0, next_snapshot_at - asyncio.get_running_loop().time())
            done, _ = await asyncio.wait(
                {receive_task}, timeout=timeout
            )
            if not done:
                if not await _send_snapshot(websocket, device_id):
                    break
                next_snapshot_at = asyncio.get_running_loop().time() + 3.0
                continue

            try:
                message = receive_task.result()
            except WebSocketDisconnect:
                break
            receive_task = asyncio.create_task(websocket.receive_text())

            if message.strip().lower() == "ping":
                if not await manager.send_json(websocket, {
                    "type": "pong",
                    "event": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }):
                    break
            elif not await _send_snapshot(websocket, device_id):
                break
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WebSocket telemetry failed for %s: %s", device_id, exc)
    finally:
        if receive_task and not receive_task.done():
            receive_task.cancel()
        manager.disconnect(websocket, device_id)