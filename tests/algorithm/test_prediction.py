"""
P1-1 / P1-2 预测模块测试

覆盖：
- metrics：RMSE / MAE / MAPE / evaluate_predictions / compare_models
- 降级：Prophet 未安装时 TimeSeriesPredictor 自动降级为 scikit-learn 多项式回归
- trend 判定：rising / falling / stable

运行方式：
    python -m unittest tests.algorithm.test_prediction -v
"""
import os
import sys
import unittest

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 确保项目根目录在 sys.path 中
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from algorithms.evaluation.metrics import (
    calculate_rmse, calculate_mae, calculate_mape, evaluate_predictions, compare_models,
)
from algorithms.prediction.prophet_model import TimeSeriesPredictor, PROPHET_AVAILABLE
from algorithms.prediction.model_utils import prepare_training_data, split_train_test
from backend.services.predict_service import _calculate_trend


class TestMetrics(unittest.TestCase):
    """评估指标测试"""

    def test_rmse_perfect(self):
        self.assertAlmostEqual(calculate_rmse([1, 2, 3], [1, 2, 3]), 0.0, places=6)

    def test_rmse_known(self):
        # sqrt((1+1+1)/3) = 1.0
        self.assertAlmostEqual(calculate_rmse([1, 2, 3], [2, 3, 4]), 1.0, places=6)

    def test_mae_known(self):
        self.assertAlmostEqual(calculate_mae([1, 2, 3], [2, 3, 4]), 1.0, places=6)

    def test_mape_known(self):
        # (|100-110|/100 + |200-210|/200) / 2 * 100 = (0.1 + 0.05) / 2 * 100 = 7.5
        self.assertAlmostEqual(calculate_mape([100, 200], [110, 210]), 7.5, places=4)

    def test_mape_zero_true_returns_zero(self):
        # 真实值全为 0 时 MAPE 定义为 0，避免除零
        self.assertEqual(calculate_mape([0, 0], [1, 2]), 0.0)

    def test_evaluate_predictions_keys(self):
        result = evaluate_predictions([1, 2, 3], [1.1, 2.1, 3.1])
        for key in ('rmse', 'mae', 'mape', 'r2'):
            self.assertIn(key, result)
        # 完美预测 r2 = 1
        perfect = evaluate_predictions([1, 2, 3], [1, 2, 3])
        self.assertAlmostEqual(perfect['r2'], 1.0, places=6)

    def test_compare_models_picks_lowest_rmse(self):
        results = {'prophet': {'rmse': 1.0}, 'sklearn': {'rmse': 0.5}}
        cmp = compare_models(results)
        self.assertEqual(cmp['best_model'], 'sklearn')
        self.assertAlmostEqual(cmp['best_rmse'], 0.5)


class TestSklearnFallback(unittest.TestCase):
    """Prophet 未安装时的降级方案测试"""

    def setUp(self):
        start = datetime(2026, 1, 1)
        times = [start + timedelta(minutes=i) for i in range(200)]
        # 基线 + 线性趋势 + 分钟级周期
        y = 100 + 0.05 * np.arange(200) + np.sin(2 * np.pi * np.arange(200) / 60)
        self.df = pd.DataFrame({'ds': pd.to_datetime(times), 'y': y})

    def test_auto_falls_back_to_sklearn_without_prophet(self):
        predictor = TimeSeriesPredictor(model_type='auto')
        if not PROPHET_AVAILABLE:
            self.assertEqual(predictor.model_type, 'sklearn')

    def test_sklearn_fit_predict(self):
        predictor = TimeSeriesPredictor(model_type='sklearn')
        predictor.fit(self.df)
        self.assertEqual(predictor.model_type, 'sklearn')
        forecast = predictor.predict(self.df, periods=60, freq='1min')
        self.assertEqual(len(forecast), 60)
        for col in ('ds', 'yhat', 'yhat_lower', 'yhat_upper'):
            self.assertIn(col, forecast.columns)
        # 预测区间下界 <= 点估计 <= 上界
        self.assertTrue(((forecast['yhat_lower'] <= forecast['yhat']) &
                         (forecast['yhat'] <= forecast['yhat_upper'])).all())

    def test_sklearn_forecast_continues_linear_trend(self):
        start = datetime(2026, 1, 1)
        sample_count = 7 * 24 * 60
        history = pd.DataFrame({
            'ds': pd.to_datetime([start + timedelta(minutes=i) for i in range(sample_count)]),
            'y': 100 + 2 * np.arange(sample_count, dtype=float),
        })
        predictor = TimeSeriesPredictor(model_type='sklearn')
        predictor.fit(history)

        forecast = predictor.predict(history, periods=3, freq='1min')

        np.testing.assert_allclose(
            forecast['yhat'].values,
            100 + 2 * np.arange(sample_count, sample_count + 3),
            atol=1.0,
        )
        self.assertGreater(forecast['yhat'].iloc[0], history['y'].iloc[-1])

    def test_sklearn_evaluate(self):
        predictor = TimeSeriesPredictor(model_type='sklearn')
        predictor.fit(self.df)
        metrics = predictor.evaluate(self.df)
        self.assertIn('rmse', metrics)
        self.assertGreaterEqual(metrics['rmse'], 0.0)

    def test_sklearn_evaluate_uses_training_time_origin(self):
        start = datetime(2026, 1, 1)
        train_count = 7 * 24 * 60
        test_count = 24 * 60
        full_df = pd.DataFrame({
            'ds': pd.to_datetime([
                start + timedelta(minutes=i) for i in range(train_count + test_count)
            ]),
            'y': 100 + 2 * np.arange(train_count + test_count, dtype=float),
        })
        predictor = TimeSeriesPredictor(model_type='sklearn')
        predictor.fit(full_df.iloc[:train_count])

        metrics = predictor.evaluate(full_df.iloc[train_count:])

        self.assertLess(metrics['rmse'], 1.0)

    def test_save_load_roundtrip(self):
        import tempfile
        predictor = TimeSeriesPredictor(model_type='sklearn')
        predictor.fit(self.df)
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, 'model.pkl')
            predictor.save(fp)
            loaded = TimeSeriesPredictor.load(fp)
            self.assertEqual(loaded.model_type, 'sklearn')
            original_forecast = predictor.predict(self.df, periods=10, freq='1min')
            # 加载后仍可预测，并且必须使用训练时持久化的时间原点。
            forecast = loaded.predict(self.df, periods=10, freq='1min')
            self.assertEqual(len(forecast), 10)
            self.assertEqual(loaded._feature_time_origin, predictor._feature_time_origin)
            np.testing.assert_allclose(forecast['yhat'].values, original_forecast['yhat'].values)


class TestDataPreprocessing(unittest.TestCase):
    """训练数据预处理测试"""

    def test_prepare_training_data_fills_nan(self):
        times = [datetime(2026, 1, 1) + timedelta(minutes=i) for i in range(10)]
        y = [1.0, 2.0, None, 4.0, 5.0, 6.0, None, 8.0, 9.0, 10.0]
        df = pd.DataFrame({'ds': pd.to_datetime(times), 'y': y})
        processed = prepare_training_data(df, resample_freq='1min')
        self.assertFalse(processed['y'].isnull().any())

    def test_split_train_test_ratio(self):
        times = [datetime(2026, 1, 1) + timedelta(minutes=i) for i in range(100)]
        df = pd.DataFrame({'ds': pd.to_datetime(times), 'y': np.arange(100.0)})
        train, test = split_train_test(df, test_ratio=0.2)
        self.assertEqual(len(train), 80)
        self.assertEqual(len(test), 20)


class TestPredictionValidation(unittest.TestCase):
    """P1-1 输入和输出契约测试。"""

    def test_invalid_model_type_is_rejected(self):
        with self.assertRaises(ValueError):
            TimeSeriesPredictor(model_type='unknown')

    def test_invalid_periods_are_rejected(self):
        predictor = TimeSeriesPredictor(model_type='sklearn')
        with self.assertRaises(ValueError):
            predictor.predict(pd.DataFrame({'ds': [datetime(2026, 1, 1)]}), 0)

    def test_dirty_history_is_cleaned_before_fit(self):
        df = pd.DataFrame({
            'ds': [datetime(2026, 1, 1, 0, 2), None,
                   datetime(2026, 1, 1, 0, 1), datetime(2026, 1, 1, 0, 1)],
            'y': [2.0, 99.0, 1.0, float('nan')],
        })
        predictor = TimeSeriesPredictor(model_type='sklearn')
        predictor.fit(df)
        forecast = predictor.predict(df, periods=2, freq='1h')
        self.assertEqual(len(forecast), 2)
        self.assertTrue(forecast['ds'].is_monotonic_increasing)


class TestTrendDetection(unittest.TestCase):
    """趋势判定测试（predict_service._calculate_trend）"""

    def test_rising(self):
        arr = np.array([1, 1, 1, 1, 10, 10, 10, 10], dtype=float)
        self.assertEqual(_calculate_trend(arr), 'rising')

    def test_falling(self):
        arr = np.array([10, 10, 10, 10, 1, 1, 1, 1], dtype=float)
        self.assertEqual(_calculate_trend(arr), 'falling')

    def test_stable(self):
        arr = np.array([5, 5, 5, 5, 5, 5, 5, 5], dtype=float)
        self.assertEqual(_calculate_trend(arr), 'stable')

    def test_short_array_returns_stable(self):
        self.assertEqual(_calculate_trend(np.array([1.0])), 'stable')


if __name__ == '__main__':
    unittest.main()
