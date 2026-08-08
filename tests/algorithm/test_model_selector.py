"""
P1-2 模型自适应选择测试

覆盖：
- 工况划分：高负荷(power > 280MW) / 低负荷(power <= 280MW) 边界判定
- HIGH_LOAD_THRESHOLD 常量契约

运行方式：
    python -m unittest tests.algorithm.test_model_selector -v
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# 确保项目根目录在 sys.path 中
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from algorithms.evaluation.model_selector import ModelSelector, HIGH_LOAD_THRESHOLD
from backend.database.models import SensorPoint


def _build_mock_session(avg_power: float):
    """构造 mock db session：
    - SensorPoint 查询 → 返回一个 fake sensor
    - TimeseriesData.value 查询 → 返回 [(avg_power,)] * 5
    """
    session = MagicMock()
    sensor = MagicMock()
    sensor.id = 10

    sensor_query = MagicMock()
    sensor_query.filter.return_value.first.return_value = sensor

    ts_chain = MagicMock()
    ts_chain.order_by.return_value = ts_chain
    ts_chain.limit.return_value = ts_chain
    ts_chain.all.return_value = [(avg_power,)] * 5
    ts_query = MagicMock()
    ts_query.filter.return_value = ts_chain

    # get_device_by_code_or_name 已被 patch，session.query 只会被 SensorPoint / TimeseriesData.value 调用
    session.query.side_effect = lambda arg: sensor_query if arg is SensorPoint else ts_query
    return session


class TestConditionDetection(unittest.TestCase):
    """工况（高/低负荷）划分测试"""

    def test_high_load_threshold_contract(self):
        # 契约：高负荷阈值 = 280MW
        self.assertEqual(HIGH_LOAD_THRESHOLD, 280.0)

    @patch('algorithms.evaluation.model_selector.get_device_by_code_or_name')
    @patch('algorithms.evaluation.model_selector.get_db')
    def test_detect_high_load(self, mock_get_db, mock_get_device):
        device = MagicMock()
        device.id = 1
        device.device_code = 'generator_004'
        mock_get_device.return_value = device

        session = _build_mock_session(avg_power=300.0)  # 300 > 280 → 高负荷
        mock_get_db.return_value = iter([session])

        selector = ModelSelector()
        self.assertEqual(selector.detect_condition('generator_004'), 'high')

    @patch('algorithms.evaluation.model_selector.get_device_by_code_or_name')
    @patch('algorithms.evaluation.model_selector.get_db')
    def test_detect_low_load(self, mock_get_db, mock_get_device):
        device = MagicMock()
        device.id = 1
        device.device_code = 'generator_004'
        mock_get_device.return_value = device

        session = _build_mock_session(avg_power=250.0)  # 250 <= 280 → 低负荷
        mock_get_db.return_value = iter([session])

        selector = ModelSelector()
        self.assertEqual(selector.detect_condition('generator_004'), 'low')

    @patch('algorithms.evaluation.model_selector.get_device_by_code_or_name')
    @patch('algorithms.evaluation.model_selector.get_db')
    def test_detect_boundary_just_above(self, mock_get_db, mock_get_device):
        device = MagicMock()
        device.id = 1
        mock_get_device.return_value = device

        session = _build_mock_session(avg_power=280.5)
        mock_get_db.return_value = iter([session])

        selector = ModelSelector()
        self.assertEqual(selector.detect_condition('generator_004'), 'high')

    @patch('algorithms.evaluation.model_selector.get_device_by_code_or_name')
    @patch('algorithms.evaluation.model_selector.get_db')
    def test_detect_boundary_exactly_threshold(self, mock_get_db, mock_get_device):
        device = MagicMock()
        device.id = 1
        mock_get_device.return_value = device

        # 恰好等于阈值 → 不大于 → 低负荷
        session = _build_mock_session(avg_power=280.0)
        mock_get_db.return_value = iter([session])

        selector = ModelSelector()
        self.assertEqual(selector.detect_condition('generator_004'), 'low')

    @patch('algorithms.evaluation.model_selector.get_device_by_code_or_name')
    @patch('algorithms.evaluation.model_selector.get_db')
    def test_device_not_found_returns_low(self, mock_get_db, mock_get_device):
        mock_get_device.return_value = None
        session = MagicMock()
        mock_get_db.return_value = iter([session])

        selector = ModelSelector()
        self.assertEqual(selector.detect_condition('unknown_device'), 'low')


if __name__ == '__main__':
    unittest.main()
