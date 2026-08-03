from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from backend.database.connection import get_db
from backend.database.models import Device, SensorPoint, TimeseriesData
from backend.services.data_service import get_device_by_code_or_name, resolve_param_name


def fetch_history_data(device_id: str, parameter: str, hours: int = 168) -> pd.DataFrame:
    """
    从 TimescaleDB 拉取历史时序数据用于模型训练

    参数:
        device_id: str - 设备编码（英文ID或中文名）
        parameter: str - 测点参数名
        hours: int - 历史数据时长（小时），默认 7 天

    返回:
        pd.DataFrame - 包含 ds(时间) 和 y(值) 两列
    """
    db = next(get_db())
    try:
        device = get_device_by_code_or_name(db, device_id)
        if not device:
            return pd.DataFrame()

        resolved_name = resolve_param_name(parameter)
        sensor = db.query(SensorPoint).filter(
            SensorPoint.device_id == device.id,
            SensorPoint.point_name == resolved_name
        ).first()
        if not sensor:
            return pd.DataFrame()

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        rows = db.query(
            TimeseriesData.recorded_at,
            TimeseriesData.value
        ).filter(
            TimeseriesData.device_id == device.id,
            TimeseriesData.sensor_id == sensor.id,
            TimeseriesData.recorded_at >= start_time,
            TimeseriesData.recorded_at <= end_time
        ).order_by(TimeseriesData.recorded_at).all()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([
            {'ds': row.recorded_at, 'y': row.value}
            for row in rows
        ])
        df['ds'] = pd.to_datetime(df['ds'])
        return df

    finally:
        db.close()


def prepare_training_data(df: pd.DataFrame, resample_freq: str = '1min') -> pd.DataFrame:
    """
    数据预处理：重采样、缺失值填充、去异常

    参数:
        df: pd.DataFrame - 原始数据，包含 ds 和 y 列
        resample_freq: str - 重采样频率

    返回:
        pd.DataFrame - 处理后的数据
    """
    if df.empty:
        return df

    df = df.copy()
    df = df.drop_duplicates(subset='ds').sort_values('ds')

    df = df.set_index('ds').resample(resample_freq).mean()
    df['y'] = df['y'].interpolate(method='linear')
    df['y'] = df['y'].fillna(method='ffill').fillna(method='bfill')

    df = df.reset_index()

    return df


def split_train_test(df: pd.DataFrame, test_ratio: float = 0.2):
    """
    划分训练集和测试集

    参数:
        df: pd.DataFrame - 处理后的数据
        test_ratio: float - 测试集比例

    返回:
        tuple - (train_df, test_df)
    """
    if df.empty:
        return df, df

    split_idx = int(len(df) * (1 - test_ratio))
    return df.iloc[:split_idx], df.iloc[split_idx:]


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    提取时间特征用于 scikit-learn 回归（降级方案）

    参数:
        df: pd.DataFrame - 包含 ds 列

    返回:
        pd.DataFrame - 特征矩阵
    """
    features = pd.DataFrame()
    features['hour'] = df['ds'].dt.hour
    features['day_of_week'] = df['ds'].dt.dayofweek
    features['day_of_year'] = df['ds'].dt.dayofyear
    features['minute'] = df['ds'].dt.minute

    features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
    features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)
    features['dow_sin'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
    features['dow_cos'] = np.cos(2 * np.pi * features['day_of_week'] / 7)

    features['timestep'] = np.arange(len(df))

    return features