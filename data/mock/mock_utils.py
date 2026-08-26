"""不依赖数据库的 mock 数据生成辅助函数。"""
from datetime import datetime, timedelta

from anomaly_scenarios import inject_steam_temp_rise, inject_vibration_rise


def _data_start_time(data: list):
    """返回数据中的最早采样时间。"""
    return min(item['timestamp'] for item in data)


def calendar_window_start(data: list, window: dict):
    """根据数据首日和配置的日历时钟，计算异常窗口起点。"""
    if not data:
        return None
    first_timestamp = _data_start_time(data)
    first_day = first_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    return first_day + timedelta(
        days=window['day_offset'],
        hours=window['start_hour'],
        minutes=window.get('start_minute', 0),
    )


def get_generation_start_time(now: datetime = None) -> datetime:
    """返回最近完整 7 天数据的午夜起点。"""
    now = now or datetime.now()
    return (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)


def inject_configured_anomalies(device_type: str, data: list, anomaly_windows: dict):
    """按日历窗口配置向设备数据注入异常。"""
    if not data:
        return []

    if device_type == 'boiler':
        window = anomaly_windows['steam_temp_rise']
        window_start = calendar_window_start(data, window)
        return inject_steam_temp_rise(
            data, 0, window['duration'], window_start=window_start
        )
    if device_type == 'turbine':
        window = anomaly_windows['vibration_rise']
        window_start = calendar_window_start(data, window)
        return inject_vibration_rise(
            data, 0, window['duration'], window_start=window_start
        )
    return []