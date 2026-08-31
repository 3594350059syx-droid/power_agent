"""趋势分析和告警中心 API 契约测试，无需外部 PostgreSQL。"""

import os
import sys
import unittest
from unittest.mock import patch


project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.api.alarm import acknowledge_alarm_record, get_alarm_list
from backend.api.telemetry import get_history_trend


class TestHistoryTrendContract(unittest.TestCase):
    @patch("backend.api.telemetry.get_database_history_trend", return_value=None)
    def test_mock_history_has_aligned_series_and_anomaly_ranges(self, mock_database_history):
        response = get_history_trend("boiler_002", "steam_temp", 24)
        data = response["data"]

        self.assertTrue(response["success"])
        self.assertEqual(data["device_id"], "boiler_002")
        self.assertEqual(data["parameter"], "steam_temp")
        self.assertEqual(data["unit"], "℃")
        self.assertEqual(len(data["timestamps"]), len(data["values"]))
        self.assertGreater(len(data["timestamps"]), 0)
        self.assertEqual(len(data["anomaly_ranges"]), 1)
        self.assertLessEqual(
            data["anomaly_ranges"][0]["start"],
            data["anomaly_ranges"][0]["end"],
        )
        mock_database_history.assert_called_once_with("boiler_002", "steam_temp", 24)

    def test_parameter_not_belonging_to_device_returns_empty_series(self):
        response = get_history_trend("turbine_003", "steam_temp", 24)

        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["timestamps"], [])
        self.assertEqual(response["data"]["values"], [])
        self.assertEqual(response["data"]["anomaly_ranges"], [])


class TestAlarmContract(unittest.TestCase):
    def test_database_unavailable_uses_sorted_and_filtered_contract_mock(self):
        with patch("backend.api.alarm.list_alarm_records", return_value=None):
            response = get_alarm_list(
                severity="high",
                sort="time_asc",
                device_id=None,
                hours=None,
            )

        self.assertTrue(response["success"])
        data = response["data"]
        self.assertEqual(data["total"], len(data["alarms"]))
        self.assertGreaterEqual(data["total"], 1)
        self.assertTrue(all(alarm["severity"] == "high" for alarm in data["alarms"]))
        self.assertEqual(
            [alarm["triggered_at"] for alarm in data["alarms"]],
            sorted(alarm["triggered_at"] for alarm in data["alarms"]),
        )
        required_fields = {
            "id", "device_id", "device_name", "parameter", "parameter_name",
            "alarm_type", "severity", "current_value", "threshold_value",
            "status", "triggered_at",
        }
        self.assertTrue(required_fields.issubset(data["alarms"][0]))
        self.assertIn(data["alarms"][0]["status"], {"pending", "acknowledged"})

    def test_acknowledge_updates_contract_mock_when_database_is_unavailable(self):
        with patch("backend.api.alarm.acknowledge_alarm", return_value=None):
            response = acknowledge_alarm_record(1)

        self.assertTrue(response["success"])
        self.assertEqual(response["data"], {"id": 1, "status": "acknowledged"})

    def test_acknowledging_unknown_alarm_returns_unified_error_response(self):
        with patch("backend.api.alarm.acknowledge_alarm", return_value=False):
            response = acknowledge_alarm_record(99999)

        self.assertFalse(response["success"])
        self.assertEqual(response["data"], {"id": 99999})


if __name__ == "__main__":
    unittest.main()