"""P1-1 predict_tool 接口契约测试，不依赖 PostgreSQL 或 Prophet。"""
import os
import sys
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.tools.predict_tool import predict_tool
from backend.services.predict_service import predict_parameter


class TestPredictTool(unittest.TestCase):
    def test_forwards_the_declared_signature(self):
        expected = {
            'predictions': [
                {'time': '2026-01-01T01:00:00', 'value': 1.0,
                 'lower': 0.9, 'upper': 1.1},
            ],
            'trend': 'rising',
            'confidence': 0.9,
        }
        with patch('agent.tools.predict_tool.predict_parameter', return_value=expected) as mocked:
            result = predict_tool('boiler_002', 'steam_temp', hours=1)

        self.assertEqual(result, expected)
        mocked.assert_called_once_with('boiler_002', 'steam_temp', 1)


    @patch('backend.services.predict_service.get_db')
    @patch('backend.services.predict_service.get_device_by_code_or_name')
    @patch('backend.services.predict_service.fetch_history_data')
    @patch('backend.services.predict_service.TimeSeriesPredictor')
    def test_service_returns_one_point_per_hour(
        self, mock_predictor_cls, mock_fetch_history, mock_get_device, mock_get_db
    ):
        device = SimpleNamespace(id=1, device_code='boiler_002', device_name='2号锅炉')
        sensor = SimpleNamespace(id=2, unit='℃')
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sensor
        mock_get_db.return_value = iter([db])
        mock_get_device.return_value = device

        start = datetime(2026, 1, 1)
        mock_fetch_history.return_value = pd.DataFrame({
            'ds': [start + timedelta(minutes=i) for i in range(40)],
            'y': [540.0 + i * 0.1 for i in range(40)],
        })

        predictor = MagicMock()
        predictor.model_type = 'sklearn'
        predictor.predict.return_value = pd.DataFrame({
            'ds': [start + timedelta(hours=i + 1) for i in range(6)],
            'yhat': [545.0 + i for i in range(6)],
            'yhat_lower': [544.0 + i for i in range(6)],
            'yhat_upper': [546.0 + i for i in range(6)],
        })
        mock_predictor_cls.return_value = predictor

        result = predict_parameter(
            'boiler_002', 'steam_temp', hours=6, use_cache=False
        )

        self.assertNotIn('error', result)
        self.assertEqual(len(result['predictions']), 6)
        self.assertEqual(result['prediction_hours'], 6)
        self.assertIn(result['trend'], {'rising', 'falling', 'stable'})
        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)
        self.assertEqual(
            [point['time'] for point in result['predictions']],
            [
                (start + timedelta(hours=i + 1)).isoformat()
                for i in range(6)
            ],
        )
        predictor.predict.assert_called_once()
        self.assertEqual(
            predictor.predict.call_args.kwargs,
            {'periods': 6, 'freq': '1h'},
        )


if __name__ == '__main__':
    unittest.main()
