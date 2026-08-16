from datetime import datetime, timedelta
import os
import numpy as np
from backend.database.connection import get_db
from backend.database.models import Device, SensorPoint, TimeseriesData
from backend.services.data_service import get_device_by_code_or_name, resolve_param_name
from algorithms.prediction import TimeSeriesPredictor, fetch_history_data, prepare_training_data


MODEL_CACHE_DIR = 'models/prediction'
# 缓存 TTL（秒）：超过此时长认为模型过期，强制重训
MODEL_CACHE_TTL_SECONDS = 6 * 3600


def _model_cache_path(device_code: str, resolved_param: str) -> str:
    return os.path.join(MODEL_CACHE_DIR, f"{device_code}_{resolved_param}.pkl")


def _model_fresh(cache_path: str) -> bool:
    if not os.path.exists(cache_path):
        return False
    age = datetime.now().timestamp() - os.path.getmtime(cache_path)
    return age < MODEL_CACHE_TTL_SECONDS


def predict_parameter(device_id: str, parameter: str, hours: int = 6,
                      history_hours: int = 168, use_cache: bool = True) -> dict:
    """
    预测设备某参数未来趋势

    策略：优先读取 models/prediction/<device>_<param>.pkl 缓存模型；
    缓存不存在或超过 TTL（默认 6h）时，拉取历史数据重训并保存。
    与 P1-2 ModelSelector 的 train_and_save_model 产出的缓存共享同一目录。
    """
    db = next(get_db())
    try:
        device = get_device_by_code_or_name(db, device_id)
        if not device:
            return {'error': f"Device '{device_id}' not found"}

        resolved_name = resolve_param_name(parameter)
        sensor = db.query(SensorPoint).filter(
            SensorPoint.device_id == device.id,
            SensorPoint.point_name == resolved_name
        ).first()
        if not sensor:
            return {'error': f"Parameter '{parameter}' not found for device '{device.device_code}'"}

        cache_path = _model_cache_path(device.device_code, resolved_name)
        predictor = None
        df = None

        # 1) 尝试加载缓存模型
        if use_cache and _model_fresh(cache_path):
            try:
                predictor = TimeSeriesPredictor.load(cache_path)
            except Exception as e:
                # 跨环境 prophet 未安装 / pickle 损坏等，降级为重训
                predictor = None

        # 2) 缓存未命中 → 拉取数据 + fit + 保存
        if predictor is None:
            raw_df = fetch_history_data(device_id, parameter, hours=history_hours)
            if raw_df.empty:
                return {'error': 'No historical data available for training'}

            df = prepare_training_data(raw_df, resample_freq='1min')
            if len(df) < 30:
                return {'error': f'Insufficient training data: only {len(df)} samples'}

            predictor = TimeSeriesPredictor(model_type='auto')
            predictor.fit(df)
            try:
                predictor.save(cache_path)
            except Exception:
                # 保存失败不影响本次预测（只读文件系统 / 权限等）
                pass

        # 3) 预测时需要一份历史数据（用于取最后实际值 & prophet make_future_dataframe 的锚点）
        if df is None:
            raw_df = fetch_history_data(device_id, parameter, hours=min(history_hours, 24))
            if raw_df.empty:
                return {'error': 'No historical data available for prediction anchor'}
            df = prepare_training_data(raw_df, resample_freq='1min')

        periods = hours * 60
        forecast = predictor.predict(df, periods=periods, freq='1min')

        predictions = []
        for i in range(0, len(forecast), 60):
            row = forecast.iloc[i]
            predictions.append({
                'time': row['ds'].isoformat() if hasattr(row['ds'], 'isoformat') else str(row['ds']),
                'value': round(float(row['yhat']), 2),
                'lower': round(float(row['yhat_lower']), 2),
                'upper': round(float(row['yhat_upper']), 2)
            })

        trend = _calculate_trend(forecast['yhat'].values)
        confidence = _calculate_confidence(forecast)

        recent_values = df['y'].tail(60).values
        last_actual = round(float(recent_values[-1]), 2) if len(recent_values) > 0 else None
        last_predicted = round(float(forecast['yhat'].iloc[-1]), 2)

        return {
            'device_id': device.device_code,
            'device_name': device.device_name,
            'parameter': resolved_name,
            'unit': sensor.unit,
            'predictions': predictions,
            'trend': trend,
            'confidence': confidence,
            'last_actual_value': last_actual,
            'last_predicted_value': last_predicted,
            'prediction_hours': hours,
            'model_type': predictor.model_type,
            'generated_at': datetime.now().isoformat()
        }

    finally:
        db.close()


def _calculate_trend(yhat_values: np.ndarray) -> str:
    """根据预测值序列判断趋势"""
    if len(yhat_values) < 2:
        return 'stable'

    first_half = np.mean(yhat_values[:len(yhat_values) // 2])
    second_half = np.mean(yhat_values[len(yhat_values) // 2:])
    change_ratio = (second_half - first_half) / (abs(first_half) + 1e-8)

    if change_ratio > 0.02:
        return 'rising'
    elif change_ratio < -0.02:
        return 'falling'
    else:
        return 'stable'


def _calculate_confidence(forecast) -> float:
    """
    根据预测区间宽度计算置信度。

    原公式 confidence = 1 - mean(区间宽度)/|均值| 对 vibration/power_factor 等小量纲
    参数系统性偏低（区间绝对宽度小但均值更小 → 相对宽度被放大）。改为：
        1) 用四分位距（IQR）做归一化基准，避免均值靠近 0 时除零崩溃；
        2) 仍接近 0 时改用绝对区间宽度封顶（0.1 倍 range 对应 confidence≈0.9）。
    """
    yhat = forecast['yhat'].values.astype(float)
    width = (forecast['yhat_upper'] - forecast['yhat_lower']).values.astype(float)
    mean_width = float(np.mean(width))

    # 归一化基准：优先 IQR，其次 max-min，最差情况用均值绝对值 + 1e-8
    q75, q25 = np.percentile(yhat, [75, 25])
    iqr = q75 - q25
    spread = iqr if iqr > 1e-8 else (np.max(yhat) - np.min(yhat))
    if spread < 1e-8:
        spread = float(np.mean(np.abs(yhat))) + 1e-8

    relative_width = mean_width / spread
    confidence = max(0.0, min(1.0, 1.0 - relative_width))
    return round(float(confidence), 2)


def train_and_save_model(device_id: str, parameter: str, model_name: str = None,
                         history_hours: int = 168) -> dict:
    """
    训练并保存模型

    参数:
        device_id: str - 设备编码
        parameter: str - 测点参数名
        model_name: str - 模型文件名（不含扩展名）
        history_hours: int - 训练数据时长

    返回:
        dict - 训练结果
    """
    db = next(get_db())
    try:
        device = get_device_by_code_or_name(db, device_id)
        if not device:
            return {'error': f"Device '{device_id}' not found"}

        resolved_name = resolve_param_name(parameter)
        if not model_name:
            model_name = f"{device.device_code}_{resolved_name}"

        raw_df = fetch_history_data(device_id, parameter, hours=history_hours)
        if raw_df.empty:
            return {'error': 'No historical data available'}

        df = prepare_training_data(raw_df, resample_freq='1min')

        from algorithms.prediction.model_utils import split_train_test
        train_df, test_df = split_train_test(df, test_ratio=0.2)

        predictor = TimeSeriesPredictor(model_type='auto')
        predictor.fit(train_df)

        metrics = predictor.evaluate(test_df) if not test_df.empty else {}

        import os
        filepath = os.path.join(MODEL_CACHE_DIR, f"{model_name}.pkl")
        predictor.save(filepath)

        return {
            'model_name': model_name,
            'model_path': filepath,
            'model_type': predictor.model_type,
            'train_samples': len(train_df),
            'test_samples': len(test_df),
            'metrics': metrics
        }

    finally:
        db.close()