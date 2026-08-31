"""Week 6-A WebSocket 遥测协议测试。"""
import os
import sys
import unittest
from unittest.mock import patch

from fastapi import WebSocketDisconnect

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.api.websocket import telemetry_websocket
from backend.services.realtime_service import manager


class FakeWebSocket:
    def __init__(self, messages=None):
        self.messages = list(messages or [])
        self.sent = []
        self.accepted = False
        self.closed_with = None

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        self.sent.append(payload)

    async def receive_text(self):
        if self.messages:
            message = self.messages.pop(0)
            if isinstance(message, BaseException):
                raise message
            return message
        raise WebSocketDisconnect()

    async def close(self, code=None):
        self.closed_with = code


class TestTelemetryWebSocket(unittest.IsolatedAsyncioTestCase):
    def tearDown(self):
        manager._connections.clear()

    async def test_sends_snapshot_responds_to_ping_and_cleans_connection(self):
        websocket = FakeWebSocket(["ping", WebSocketDisconnect()])
        snapshot = {
            "success": True,
            "data": {
                "device_status": {"device_id": "boiler_002", "status": "running"},
                "metrics": [],
            },
        }

        with patch("backend.api.websocket.get_live_telemetry", return_value=snapshot):
            await telemetry_websocket(websocket, "boiler_002")

        self.assertTrue(websocket.accepted)
        self.assertEqual(websocket.sent[0]["event"], "telemetry_snapshot")
        self.assertEqual(websocket.sent[0]["data"], snapshot["data"])
        self.assertEqual(websocket.sent[1]["type"], "pong")
        self.assertEqual(manager.count("boiler_002"), 0)

    async def test_unknown_device_is_rejected_with_error_event(self):
        websocket = FakeWebSocket()

        await telemetry_websocket(websocket, "unknown_device")

        self.assertTrue(websocket.accepted)
        self.assertEqual(websocket.sent[0]["type"], "error")
        self.assertEqual(websocket.closed_with, 1008)
        self.assertEqual(manager.count("unknown_device"), 0)


class TestConnectionManager(unittest.IsolatedAsyncioTestCase):
    def tearDown(self):
        manager._connections.clear()

    async def test_broadcast_removes_failed_connections(self):
        good = FakeWebSocket()
        failed = FakeWebSocket()

        async def fail_send(_payload):
            raise RuntimeError("closed")

        failed.send_json = fail_send
        manager._connections["boiler_002"].update({good, failed})

        sent = await manager.broadcast("boiler_002", {"type": "telemetry"})

        self.assertEqual(sent, 1)
        self.assertEqual(manager.count("boiler_002"), 1)
        self.assertEqual(good.sent, [{"type": "telemetry"}])


if __name__ == "__main__":
    unittest.main()