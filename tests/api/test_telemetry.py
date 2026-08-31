"""P0-3 实时遥测接口的设备/测点响应契约测试。"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.api.telemetry import get_live_telemetry
from backend.services.telemetry_service import get_database_live_telemetry


EXPECTED_METRICS = {
    "boiler_002": {"steam_temp", "steam_pressure", "furnace_temp"},
    "turbine_003": {"rpm", "bearing_temp", "vibration"},
    "generator_004": {"power", "stator_temp", "reactive_power"},
}


# 项目 TimeseriesData 的 PostgreSQL 模型使用复合主键（其中 BIGSERIAL id 自增）。
# SQLite 不支持该组合，因此为服务逻辑提供字段等价的测试映射，验证查询、最新值
# 选择和状态映射，而不更改生产表结构。
TelemetryTestBase = declarative_base()


class TelemetryTestDevice(TelemetryTestBase):
    __tablename__ = "test_device"

    id = Column(Integer, primary_key=True)
    device_code = Column(String(50), unique=True, nullable=False)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50), nullable=False)
    status = Column(String(20), default="running")


class TelemetryTestSensorPoint(TelemetryTestBase):
    __tablename__ = "test_sensor_point"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, nullable=False)
    point_name = Column(String(100), nullable=False)
    unit = Column(String(20))
    normal_min = Column(Float)
    normal_max = Column(Float)
    threshold_high = Column(Float)
    threshold_low = Column(Float)


class TelemetryTestTimeseriesData(TelemetryTestBase):
    __tablename__ = "test_timeseries_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, nullable=False)
    sensor_id = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False)


class TestLiveTelemetryContract(unittest.TestCase):
    """接口必须与 Mock 数据生成的 3 × 3 测点契约一致。"""

    @patch("backend.api.telemetry.get_database_live_telemetry", return_value=None)
    @patch("backend.api.telemetry.random.random", return_value=0.5)
    def test_known_devices_return_only_their_three_metrics(self, _mock_random, _mock_database):
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

    @patch("backend.api.telemetry.get_database_live_telemetry")
    def test_known_device_prioritizes_complete_database_snapshot(self, mock_database):
        database_snapshot = {
            "device_status": {"device_id": "boiler_002", "status": "warning"},
            "metrics": [{"key": "steam_temp", "value": 558.1, "level": "warn"}],
        }
        mock_database.return_value = database_snapshot

        response = get_live_telemetry("boiler_002")

        mock_database.assert_called_once_with("boiler_002")
        self.assertEqual(response["data"], database_snapshot)

    @patch("backend.api.telemetry.get_database_live_telemetry")
    def test_unknown_device_does_not_fall_back_to_boiler_data(self, mock_database):
        response = get_live_telemetry("unknown_device")

        self.assertTrue(response["success"])
        self.assertEqual(
            response["data"]["device_status"],
            {"device_id": "unknown_device", "status": "unknown"},
        )
        self.assertEqual(response["data"]["metrics"], [])
        mock_database.assert_not_called()


class TestDatabaseLiveTelemetry(unittest.TestCase):
    """使用内存 SQLite 验证最新值查询和状态映射，无需外部 TimescaleDB。"""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        TelemetryTestBase.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.model_patch = patch.multiple(
            "backend.services.telemetry_service",
            Device=TelemetryTestDevice,
            SensorPoint=TelemetryTestSensorPoint,
            TimeseriesData=TelemetryTestTimeseriesData,
        )
        self.model_patch.start()

    def tearDown(self):
        self.model_patch.stop()
        self.session.close()
        self.engine.dispose()

    def test_returns_latest_complete_snapshot_with_metric_levels(self):
        device = TelemetryTestDevice(device_code="boiler_002", device_name="2号锅炉", device_type="boiler", status="warning")
        self.session.add(device)
        self.session.flush()

        sensors = {
            "steam_temp": TelemetryTestSensorPoint(device_id=device.id, point_name="steam_temp", unit="℃", normal_min=525, normal_max=555, threshold_low=510, threshold_high=570),
            "steam_pressure": TelemetryTestSensorPoint(device_id=device.id, point_name="steam_pressure", unit="MPa", normal_min=16.2, normal_max=17.2, threshold_low=15.5, threshold_high=18),
            "furnace_temp": TelemetryTestSensorPoint(device_id=device.id, point_name="furnace_temp", unit="℃", normal_min=1150, normal_max=1250, threshold_low=1100, threshold_high=1300),
        }
        self.session.add_all(sensors.values())
        self.session.flush()

        now = datetime(2026, 8, 26, 12, 0)
        self.session.add_all([
            TelemetryTestTimeseriesData(device_id=device.id, sensor_id=sensors["steam_temp"].id, value=540, recorded_at=now - timedelta(minutes=1)),
            TelemetryTestTimeseriesData(device_id=device.id, sensor_id=sensors["steam_temp"].id, value=572.26, recorded_at=now),
            TelemetryTestTimeseriesData(device_id=device.id, sensor_id=sensors["steam_pressure"].id, value=16.0, recorded_at=now),
            TelemetryTestTimeseriesData(device_id=device.id, sensor_id=sensors["furnace_temp"].id, value=1200, recorded_at=now),
        ])
        self.session.commit()

        snapshot = get_database_live_telemetry("boiler_002", self.session)

        self.assertEqual(snapshot["device_status"], {"device_id": "boiler_002", "status": "warning"})
        self.assertEqual([metric["key"] for metric in snapshot["metrics"]], ["steam_temp", "steam_pressure", "furnace_temp"])
        self.assertEqual([metric["value"] for metric in snapshot["metrics"]], [572.3, 16.0, 1200.0])
        self.assertEqual([metric["level"] for metric in snapshot["metrics"]], ["danger", "warn", "normal"])

    def test_requires_all_configured_metrics_to_have_latest_data(self):
        device = TelemetryTestDevice(device_code="boiler_002", device_name="2号锅炉", device_type="boiler")
        self.session.add(device)
        self.session.flush()
        sensor = TelemetryTestSensorPoint(device_id=device.id, point_name="steam_temp", unit="℃", normal_min=525, normal_max=555)
        self.session.add(sensor)
        self.session.flush()
        self.session.add(TelemetryTestTimeseriesData(device_id=device.id, sensor_id=sensor.id, value=540, recorded_at=datetime(2026, 8, 26, 12, 0)))
        self.session.commit()

        self.assertIsNone(get_database_live_telemetry("boiler_002", self.session))


if __name__ == "__main__":
    unittest.main()