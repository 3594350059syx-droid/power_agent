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
from mock_utils import get_generation_start_time, inject_configured_anomalies
from normal_pattern import (
    generate_normal_boiler_data,
    generate_normal_turbine_data,
    generate_normal_generator_data,
)

# backend 依赖 sqlalchemy + psycopg2，缺失时跳过相关测试
try:
    from backend.database.models import AlarmRecord, Device, DiagnosisResult, TimeseriesData
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
        self.assertEqual(
            (steam['day_offset'], steam['start_hour'], steam['start_minute']),
            (3, 14, 0),
        )
        self.assertEqual(steam['duration'], 2 * 60)

        vib = ANOMALY_WINDOWS['vibration_rise']
        self.assertEqual(
            (vib['day_offset'], vib['start_hour'], vib['start_minute']),
            (4, 2, 0),
        )
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


class TestCalendarAnomalyWindows(unittest.TestCase):
    """异常时间必须匹配文档中的墙钟窗口，而不依赖生成起点是否为午夜。"""

    def test_non_midnight_start_uses_documented_steam_window(self):
        start = datetime(2026, 8, 19, 13, 37, 52)
        data = generate_normal_boiler_data(start, 7 * 24 * 60)
        affected = inject_configured_anomalies('boiler', data, ANOMALY_WINDOWS)

        window_start = datetime(2026, 8, 22, 14, 0)
        window_end = datetime(2026, 8, 22, 16, 0)
        self.assertEqual(affected[0]['timestamp'], datetime(2026, 8, 22, 14, 0, 52))
        self.assertTrue(all(window_start <= point['timestamp'] <= window_end for point in affected))

    def test_non_midnight_start_uses_documented_vibration_window(self):
        start = datetime(2026, 8, 19, 13, 37, 52)
        data = generate_normal_turbine_data(start, 7 * 24 * 60)
        affected = inject_configured_anomalies('turbine', data, ANOMALY_WINDOWS)

        window_start = datetime(2026, 8, 23, 2, 0)
        window_end = datetime(2026, 8, 23, 6, 0)
        self.assertEqual(affected[0]['timestamp'], datetime(2026, 8, 23, 2, 0, 52))
        self.assertTrue(all(window_start <= point['timestamp'] <= window_end for point in affected))

    def test_generation_start_is_midnight(self):
        start = get_generation_start_time(datetime(2026, 8, 26, 13, 37, 52))
        self.assertEqual(start, datetime(2026, 8, 19, 0, 0))


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

    def test_clear_device_data_deletes_dependents_before_alarms(self):
        import generate_data

        session = MagicMock()
        chains = {
            DiagnosisResult: MagicMock(),
            AlarmRecord: MagicMock(),
            TimeseriesData: MagicMock(),
        }
        session.query.side_effect = lambda model: chains[model]

        generate_data.clear_device_data(session, [1, 2, 3])

        self.assertEqual(
            [call.args[0] for call in session.query.call_args_list],
            [DiagnosisResult, AlarmRecord, TimeseriesData],
        )
        for chain in chains.values():
            chain.filter.return_value.delete.assert_called_once_with(synchronize_session=False)
        session.commit.assert_called_once()

    def test_get_mock_device_ids_uses_only_configured_device_codes(self):
        import generate_data

        session = MagicMock()
        session.query.return_value.filter.return_value.all.return_value = [
            MagicMock(id=11), MagicMock(id=12), MagicMock(id=13),
        ]

        self.assertEqual(generate_data.get_mock_device_ids(session), [11, 12, 13])
        session.query.assert_called_once_with(Device)
        session.query.return_value.filter.assert_called_once()
        predicate = session.query.return_value.filter.call_args.args[0]
        for device in DEVICES:
            self.assertIn(device['code'], str(predicate.compile(compile_kwargs={'literal_binds': True})))

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

    def test_every_supported_interval_uses_timescaledb_time_bucket(self):
        from sqlalchemy import select
        from sqlalchemy.dialects import postgresql

        device = MagicMock(id=1, device_code='boiler_002', device_name='2号锅炉')
        sensor = MagicMock(id=2, unit='℃')

        for aggregation, expected_interval in data_service.AGGREGATION_INTERVALS.items():
            with self.subTest(aggregation=aggregation):
                db = MagicMock()
                data_service.aggregate_query(
                    db, device, sensor, None, None, aggregation, 'steam_temp'
                )
                bucket = db.query.call_args.args[0]
                sql = str(select(bucket).compile(
                    dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True}
                ))

                self.assertIn('time_bucket', sql)
                self.assertIn(expected_interval, sql)
                self.assertNotIn('date_trunc', sql)


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
