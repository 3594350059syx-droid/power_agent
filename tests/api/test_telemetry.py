"""P0-3 实时遥测接口的设备/测点响应契约测试。"""

import os
import sys
import unittest
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.api.telemetry import get_live_telemetry


EXPECTED_METRICS = {
    "boiler_002": {"steam_temp", "steam_pressure", "furnace_temp"},
    "turbine_003": {"rpm", "bearing_temp", "vibration"},
    "generator_004": {"power", "stator_temp", "reactive_power"},
}


class TestLiveTelemetryContract(unittest.TestCase):
    """接口必须与 Mock 数据生成的 3 × 3 测点契约一致。"""

    @patch("backend.api.telemetry.random.random", return_value=0.5)
    def test_known_devices_return_only_their_three_metrics(self, _mock_random):
        for device_id, expected_keys in EXPECTED_METRICS.items():
            with self.subTest(device_id=device_id):
                response = get_live_telemetry(device_id)
                data = response["data"]

                self.assertTrue(response["success"])
                self.assertEqual(data["device_status"], {"device_id": device_id, "status": "running"})
                self.assertEqual({metric["key"] for metric in data["metrics"]}, expected_keys)
                self.assertEqual(len(data["metrics"]), 3)
                for metric in data["metrics"]:
                    self.assertEqual(metric["level"], "normal")
                    self.assertEqual(len(metric["normal_range"]), 2)
                    self.assertGreaterEqual(metric["value"], metric["normal_range"][0])
                    self.assertLessEqual(metric["value"], metric["normal_range"][1])

    def test_unknown_device_does_not_fall_back_to_boiler_data(self):
        response = get_live_telemetry("unknown_device")

        self.assertTrue(response["success"])
        self.assertEqual(
            response["data"]["device_status"],
            {"device_id": "unknown_device", "status": "unknown"},
        )
        self.assertEqual(response["data"]["metrics"], [])


if __name__ == "__main__":
    unittest.main()