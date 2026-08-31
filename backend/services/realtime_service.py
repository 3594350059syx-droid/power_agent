"""WebSocket 实时遥测连接管理。

连接管理器只负责连接生命周期和广播，快照读取由 WebSocket 路由复用
现有的 ``GET /telemetry/live`` 服务，确保 HTTP 与 WebSocket 契约一致。
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """按设备维护 WebSocket 订阅连接。"""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, device_id: str) -> None:
        await websocket.accept()
        self._connections[device_id].add(websocket)
        logger.info(
            "WebSocket connected: device=%s connections=%d",
            device_id,
            self.count(device_id),
        )

    def disconnect(self, websocket: WebSocket, device_id: str) -> None:
        connections = self._connections.get(device_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(device_id, None)
        logger.info(
            "WebSocket disconnected: device=%s connections=%d",
            device_id,
            self.count(device_id),
        )

    async def send_json(self, websocket: WebSocket, payload: dict[str, Any]) -> bool:
        """发送消息；发送失败时返回 False，由调用方负责结束连接。"""
        try:
            await websocket.send_json(payload)
            return True
        except Exception as exc:  # Starlette 会以异常表示连接已断开
            logger.debug("WebSocket send failed: %s", exc)
            return False

    async def broadcast(self, device_id: str, payload: dict[str, Any]) -> int:
        """向指定设备所有订阅者广播，返回成功发送数。"""
        connections = list(self._connections.get(device_id, ()))
        sent = 0
        stale: list[WebSocket] = []
        for websocket in connections:
            if await self.send_json(websocket, payload):
                sent += 1
            else:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket, device_id)
        return sent

    def count(self, device_id: str | None = None) -> int:
        if device_id is not None:
            return len(self._connections.get(device_id, ()))
        return sum(len(connections) for connections in self._connections.values())


manager = ConnectionManager()