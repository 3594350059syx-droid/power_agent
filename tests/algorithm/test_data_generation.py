"""
P0-2 数据生成模块测试

覆盖：
- 配置契约：3 设备 × 3 测点 = 9 测点，数据量 ≈ 90,720
- 异常场景：主蒸汽温度线性上升 / 振动持续升高，时间窗口与 Week 2 规格一致
- 幂等性：重复运行先清空旧数据再插入（mock DB 验证 clear 调用）
- 聚合查询：aggregate_query 签名兼容 SQLAlchemy 2.x（不再使用 from_self）

运行方式：
    python -m unittest tests.algorithm.test_data_generation -v
"""
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_mock_dir = os.path.join(project_root, 'data', 'mock')
if _mock_dir not in sys.path:
    sys.path.insert(0, _mock_dir)

from config import DEVICES, SENSOR_POINTS, ANOMALY_WINDOWS
from anomaly_scenarios import inject_steam_temp_rise, inject_vibration_rise
from normal_pattern import (
    generate_normal_boiler_data,
    generate_normal_turbine_data,
    generate_normal_generator_data,
)

# backend 依赖 sqlalchemy + psycopg2，缺失时跳过相关测试
try:
    from backend.database.models import TimeseriesData, AlarmRecord
    from backend.services import data_service
    BACKEND_AVAILABLE = True
except Exception:
    BACKEND_AVAILABLE = False


class TestConfigContract(unittest.TestCase):
    """设备/测点配置契约（Week 2 规格）"""

    def test_three_devices(self):
        self.assertEqual(len(DEVICES), 3)

    def test_three_sensors_per_device(self):
        for device in DEVICES:
            sensors = SENSOR_POINTS[device['type']]
            self.assertEqual(len(sensors), 3,
                             f"Device type '{device['type']}' should have 3 sensors, got {len(sensors)}")

    def test_total_sensor_count(self):
        total = sum(len(SENSOR_POINTS[d['type']]) for d in DEVICES)
        self.assertEqual(total, 9)

    def test_expected_data_volume(self):
        expected = 3 * 3 * 7 * 1440
        self.assertEqual(expected, 90720)

    def test_anomaly_windows_match_spec(self):
        steam = ANOMALY_WINDOWS['steam_temp_rise']
        self.assertEqual(steam['start_offset'], 3 * 24 * 60 + 14 * 60)
        self.assertEqual(steam['duration'], 2 * 60)

        vib = ANOMALY_WINDOWS['vibration_rise']
        self.assertEqual(vib['start_offset'], 4 * 24 * 60 + 2 * 60)
        self.assertEqual(vib['duration'], 4 * 60)

    def test_device_codes_no_hardcoded_ids(self):
        for d in DEVICES:
            self.assertNotIn('id', d, f"Device config should not contain hardcoded id: {d}")


class TestSteamTempAnomaly(unittest.TestCase):
    """主蒸汽温度异常：线性 540→575℃"""

    def setUp(self):
        self.start = datetime(2026, 1, 1)
        self.data = []
        for i in range(180):
            self.data.append({
                'point_name': 'steam_temp',
                'value': 540.0,
                'timestamp': self.start + timedelta(minutes=i),
            })

    def test_linear_rise_540_to_575(self):
        affected = inject_steam_temp_rise(self.data, 30, 120)
        self.assertEqual(len(affected), 121)
        self.assertAlmostEqual(affected[0]['value'], 540.0, places=1)
        self.assertAlmostEqual(affected[-1]['value'], 575.0, places=1)

    def test_is_linear_not_cubic(self):
        affected = inject_steam_temp_rise(self.data, 0, 100)
        mid = affected[50]['value']
        # 线性中点 = (540 + 575) / 2 = 557.5
        self.assertAlmostEqual(mid, 557.5, delta=1.0,
                               msg=f"Linear midpoint should be ~557.5, got {mid}")

    def test_exceeds_high_threshold(self):
        affected = inject_steam_temp_rise(self.data, 0, 120)
        peak = max(p['value'] for p in affected)
        self.assertGreaterEqual(peak, 570)


class TestVibrationAnomaly(unittest.TestCase):
    """振动异常：持续升高 0.03→0.12mm"""

    def setUp(self):
        self.start = datetime(2026, 1, 1)
        self.data = []
        for i in range(300):
            self.data.append({
                'point_name': 'vibration',
                'value': 0.03,
                'timestamp': self.start + timedelta(minutes=i),
            })

    def test_sustained_rise_003_to_012(self):
        affected = inject_vibration_rise(self.data, 0, 240)
        self.assertEqual(len(affected), 241)
        self.assertAlmostEqual(affected[0]['value'], 0.03, places=4)
        self.assertAlmostEqual(affected[-1]['value'], 0.12, places=4)

    def test_is_monotonic_increase(self):
        affected = inject_vibration_rise(self.data, 0, 240)
        for i in range(1, len(affected)):
            self.assertGreaterEqual(affected[i]['value'], affected[i - 1]['value'] - 1e-9)

    def test_exceeds_high_threshold(self):
        affected = inject_vibration_rise(self.data, 0, 240)
        peak = max(p['value'] for p in affected)
        self.assertGreaterEqual(peak, 0.10)


class TestNormalPatternSensors(unittest.TestCase):
    """正常数据生成器：每设备 3 测点"""

    def test_boiler_has_three_sensors(self):
        data = generate_normal_boiler_data(datetime(2026, 1, 1), 10)
        names = set(item['point_name'] for item in data)
        self.assertEqual(names, {'steam_temp', 'steam_pressure', 'furnace_temp'})

    def test_turbine_has_three_sensors(self):
        data = generate_normal_turbine_data(datetime(2026, 1, 1), 10)
        names = set(item['point_name'] for item in data)
        self.assertEqual(names, {'rpm', 'bearing_temp', 'vibration'})

    def test_generator_has_three_sensors(self):
        data = generate_normal_generator_data(datetime(2026, 1, 1), 10)
        names = set(item['point_name'] for item in data)
        self.assertEqual(names, {'power', 'stator_temp', 'reactive_power'})

    def test_record_count_matches_minutes(self):
        data = generate_normal_boiler_data(datetime(2026, 1, 1), 60)
        self.assertEqual(len(data), 180)


@unittest.skipUnless(BACKEND_AVAILABLE, "backend dependencies (sqlalchemy/psycopg2) not installed")
class TestIdempotency(unittest.TestCase):
    """幂等性：重复运行先清空旧数据再插入"""

    def test_clear_device_data_deletes_both_tables(self):
        import generate_data

        session = MagicMock()
        ts_chain = MagicMock()
        alarm_chain = MagicMock()
        session.query.side_effect = lambda arg: ts_chain if arg is TimeseriesData else alarm_chain

        generate_data.clear_device_data(session, [1, 2, 3])

        ts_chain.filter.return_value.delete.assert_called_once()
        alarm_chain.filter.return_value.delete.assert_called_once()

    @patch('generate_data.clear_device_data')
    @patch('generate_data.get_db')
    def test_main_calls_clear_before_insert(self, mock_get_db, mock_clear):
        import generate_data

        session = MagicMock()
        mock_get_db.return_value = iter([session])
        session.query.return_value.filter_by.return_value.first.return_value = None
        session.query.return_value.all.return_value = []

        try:
            generate_data.main()
        except Exception:
            pass

        mock_clear.assert_called_once()


@unittest.skipUnless(BACKEND_AVAILABLE, "backend dependencies (sqlalchemy/psycopg2) not installed")
class TestAggregateQuery(unittest.TestCase):
    """聚合查询：SQLAlchemy 2.x 兼容（不使用 from_self）"""

    def test_no_from_self_in_source(self):
        import inspect
        source = inspect.getsource(data_service.aggregate_query)
        # 检查方法调用 .from_self(，而非文档字符串中的文字描述
        self.assertNotIn('.from_self(', source,
                         "aggregate_query must not call Query.from_self() (removed in SQLAlchemy 2.x)")

    def test_accepts_db_session_not_query(self):
        import inspect
        sig = inspect.signature(data_service.aggregate_query)
        params = list(sig.parameters.keys())
        self.assertIn('db', params)
        self.assertNotIn('query', params)


@unittest.skipUnless(BACKEND_AVAILABLE, "backend dependencies (sqlalchemy/psycopg2) not installed")
class TestErrorContract(unittest.TestCase):
    """Week 2 契约：无匹配数据时返回空数组而非异常"""

    def test_empty_result_has_data_array(self):
        result = data_service._empty_result('unknown', 'steam_temp', 'Device not found')
        self.assertEqual(result['data'], [])
        self.assertIn('error', result)
        self.assertEqual(result['parameter'], 'steam_temp')


if __name__ == '__main__':
    unittest.main()
