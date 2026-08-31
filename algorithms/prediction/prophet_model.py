import os
import pickle
import numpy as np
import pandas as pd
from datetime import timedelta
from .model_utils import extract_features

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline


_REQUIRED_COLUMNS = {'ds', 'y'}
_VALID_MODEL_TYPES = {'auto', 'prophet', 'sklearn'}


def _normalise_frame(df: pd.DataFrame, require_values: bool = True) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError('Prediction data must be a pandas DataFrame')
    required = _REQUIRED_COLUMNS if require_values else {'ds'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Prediction data is missing columns: {sorted(missing)}")

    columns = ['ds', 'y'] if require_values else ['ds']
    frame = df[columns].copy()
    frame['ds'] = pd.to_datetime(frame['ds'], errors='coerce')
    if require_values:
        frame['y'] = pd.to_numeric(frame['y'], errors='coerce')
        frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=['ds', 'y'])
    else:
        frame = frame.dropna(subset=['ds'])
    frame = (frame.drop_duplicates(subset='ds', keep='last')
                 .sort_values('ds')
                 .reset_index(drop=True))
    if frame.empty:
        raise ValueError('Prediction data contains no valid observations')
    return frame


def _as_naive_timestamps(values: pd.Series) -> pd.Series:
    timestamps = pd.to_datetime(values)
    if getattr(timestamps.dt, 'tz', None) is not None:
        return timestamps.dt.tz_localize(None)
    return timestamps



def _validate_periods(periods) -> int:
    if isinstance(periods, bool) or not isinstance(periods, (int, np.integer)):
        raise ValueError('periods must be a positive integer')
    periods = int(periods)
    if periods <= 0:
        raise ValueError('periods must be a positive integer')
    return periods


class TimeSeriesPredictor:
    """
    时序预测模型封装

    优先使用 Prophet，若未安装则降级为 scikit-learn 多项式回归 + 周期特征。
    """

    def __init__(self, model_type: str = 'auto'):
        """
        参数:
            model_type: str - 模型类型 ('auto', 'prophet', 'sklearn')
        """
        if model_type not in _VALID_MODEL_TYPES:
            raise ValueError(
                f"Unsupported model_type={model_type!r}; expected one of {sorted(_VALID_MODEL_TYPES)}"
            )
        self.model_type = model_type
        self.model = None
        self._poly_features = None
        self._feature_time_origin = None

        if model_type == 'prophet':
            if not PROPHET_AVAILABLE:
                raise ImportError("Prophet not installed, use model_type='sklearn' or 'auto'")
        elif model_type == 'auto':
            self.model_type = 'prophet' if PROPHET_AVAILABLE else 'sklearn'

    def fit(self, df: pd.DataFrame):
        """
        训练模型

        参数:
            df: pd.DataFrame - 训练数据，包含 ds 和 y 列
        """
        frame = _normalise_frame(df)
        if len(frame) < 2:
            raise ValueError('At least two valid observations are required')

        if self.model_type == 'prophet':
            self._fit_prophet(frame)
        else:
            self._fit_sklearn(frame)
        return self

    def _fit_prophet(self, df: pd.DataFrame):
        self.model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10,
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False
        )
        train_df = df[['ds', 'y']].copy()
        train_df['ds'] = _as_naive_timestamps(train_df['ds'])
        self.model.fit(train_df)

    def _fit_sklearn(self, df: pd.DataFrame):
        self._feature_time_origin = pd.Timestamp(df['ds'].iloc[0])
        features = extract_features(df, time_origin=self._feature_time_origin)
        self._poly_features = PolynomialFeatures(degree=2, include_bias=False)
        X = self._poly_features.fit_transform(features.values)
        y = df['y'].values

        self.model = Pipeline([
            ('regressor', LinearRegression())
        ])
        self.model.fit(X, y)

    def predict(self, df: pd.DataFrame, periods: int, freq: str = '1min') -> pd.DataFrame:
        """
        预测未来数据

        参数:
            df: pd.DataFrame - 历史数据（用于确定起始时间）
            periods: int - 预测步数
            freq: str - 预测频率

        返回:
            pd.DataFrame - 预测结果，包含 ds, yhat, yhat_lower, yhat_upper
        """
        periods = _validate_periods(periods)
        if self.model is None:
            raise RuntimeError("Model not trained, call fit() first")
        history = _normalise_frame(
            df, require_values=self.model_type == 'sklearn'
        )

        if self.model_type == 'prophet':
            return self._predict_prophet(history, periods, freq)
        return self._predict_sklearn(history, periods, freq)

    def _predict_prophet(self, df: pd.DataFrame, periods: int, freq: str):
        self._freq_to_seconds(freq)
        last_time = _as_naive_timestamps(df['ds']).iloc[-1]
        future_times = pd.date_range(
            start=last_time, periods=periods + 1, freq=freq
        )[1:]
        forecast = self.model.predict(pd.DataFrame({'ds': future_times}))

        result = pd.DataFrame({
            'ds': forecast['ds'],
            'yhat': forecast['yhat'],
            'yhat_lower': forecast['yhat_lower'],
            'yhat_upper': forecast['yhat_upper']
        })
        return result

    def _predict_sklearn(self, df: pd.DataFrame, periods: int, freq: str):
        last_time = df['ds'].iloc[-1]

        freq_seconds = self._freq_to_seconds(freq)
        future_times = [last_time + timedelta(seconds=freq_seconds * (i + 1)) for i in range(periods)]
        future_df = pd.DataFrame({'ds': future_times})

        features = extract_features(future_df, time_origin=self._feature_time_origin)
        X = self._poly_features.transform(features.values)
        yhat = self.model.predict(X)

        residuals_std = 0.0
        if len(df) > 10:
            train_features = extract_features(df, time_origin=self._feature_time_origin)
            train_X = self._poly_features.transform(train_features.values)
            train_pred = self.model.predict(train_X)
            residuals_std = np.std(df['y'].values - train_pred)

        result = pd.DataFrame({
            'ds': future_times,
            'yhat': yhat,
            'yhat_lower': yhat - 1.96 * residuals_std,
            'yhat_upper': yhat + 1.96 * residuals_std
        })
        return result

    def _freq_to_seconds(self, freq: str) -> float:
        try:
            offset = pd.tseries.frequencies.to_offset(freq)
            seconds = float(offset.nanos) / 1_000_000_000
        except (TypeError, ValueError, AttributeError, OverflowError):
            raise ValueError(f"Unsupported fixed forecast frequency: {freq!r}") from None
        if seconds <= 0:
            raise ValueError(f"Forecast frequency must be positive: {freq!r}")
        return seconds

    def save(self, filepath: str):
        """保存模型到文件"""
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'model_type': self.model_type,
                'poly_features': self._poly_features,
                'feature_time_origin': self._feature_time_origin,
            }, f)

    @classmethod
    def load(cls, filepath: str):
        """
        从文件加载模型。

        跨环境兼容：若 pickle 中保存的 model_type='prophet' 但当前环境 PROPHET_AVAILABLE=False，
        直接 cls('prophet') → ImportError；改为抛 ImportError 由上层捕获并触发重训，
        或返回 None 让调用方降级（predict_parameter 里已 try/except 保护）。
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        saved_model_type = data.get('model_type', 'sklearn')
        # 环境不兼容（有 prophet 环境训练 → 无 prophet 环境加载）
        if saved_model_type == 'prophet' and not PROPHET_AVAILABLE:
            raise ImportError(
                f"Model at {filepath} was saved with prophet, but prophet is not installed. "
                f"Re-train or install prophet to load."
            )

        try:
            instance = cls(model_type=saved_model_type)
        except ImportError:
            # 其他原因（例：model_type 硬编码 'prophet' 但 prophet 缺失）
            raise ImportError(
                f"Cannot instantiate predictor with model_type={saved_model_type} in current env."
            )
        instance.model = data['model']
        instance._poly_features = data.get('poly_features')
        instance._feature_time_origin = data.get('feature_time_origin')
        if saved_model_type == 'sklearn' and instance._feature_time_origin is None:
            raise ValueError(
                f"Model at {filepath} predates continuous time features; re-train before loading."
            )
        return instance

    def evaluate(self, test_df: pd.DataFrame) -> dict:
        """
        在测试集上评估模型

        参数:
            test_df: pd.DataFrame - 测试数据，包含 ds 和 y 列

        返回:
            dict - 评估指标 {rmse, mae, mape}
        """
        if self.model is None:
            raise RuntimeError("Model not trained")

        frame = _normalise_frame(test_df)
        if self.model_type == 'prophet':
            eval_df = frame[['ds', 'y']].copy()
            eval_df['ds'] = _as_naive_timestamps(eval_df['ds'])
            forecast = self.model.predict(eval_df[['ds']])
            y_true = frame['y'].to_numpy(dtype=float)
            y_pred = forecast['yhat'].to_numpy(dtype=float)
        else:
            features = extract_features(frame, time_origin=self._feature_time_origin)
            X = self._poly_features.transform(features.values)
            y_true = frame['y'].to_numpy(dtype=float)
            y_pred = self.model.predict(X)

        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        mae = float(np.mean(np.abs(y_true - y_pred)))

        nonzero_mask = np.abs(y_true) > 1e-8
        if np.any(nonzero_mask):
            mape = float(np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100)
        else:
            mape = 0.0

        return {'rmse': round(rmse, 4), 'mae': round(mae, 4), 'mape': round(mape, 2)}