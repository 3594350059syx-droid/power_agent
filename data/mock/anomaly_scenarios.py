"""
异常场景注入器

Week 2 规格：
- 主蒸汽温度：540℃ 线性升至 575℃（触发 HIGH 告警，threshold_high=570）
- 振动：0.03mm 持续升高至 0.12mm（触发 HIGH 告警，threshold_high=0.10）
"""
from datetime import timedelta


def inject_steam_temp_rise(data: list, start_offset: int, duration_minutes: int):
    """
    主蒸汽温度线性上升（减温水阀故障）
    540℃ → 575℃，线性变化（非三次缓动曲线）
    """
    affected_points = []
    base_time = data[0]['timestamp'] + timedelta(minutes=start_offset)
    end_time = base_time + timedelta(minutes=duration_minutes)

    for item in data:
        if item['point_name'] != 'steam_temp':
            continue
        ts = item['timestamp']
        if base_time <= ts <= end_time:
            progress = (ts - base_time).total_seconds() / 60 / duration_minutes
            item['value'] = round(540 + 35 * progress, 2)
            affected_points.append(item)
    return affected_points


def inject_vibration_rise(data: list, start_offset: int, duration_minutes: int):
    """
    振动持续升高（轴承磨损加剧）
    0.03mm → 0.12mm，线性持续 4 小时（非尖峰后衰减）
    """
    affected_points = []
    base_time = data[0]['timestamp'] + timedelta(minutes=start_offset)
    end_time = base_time + timedelta(minutes=duration_minutes)

    for item in data:
        if item['point_name'] != 'vibration':
            continue
        ts = item['timestamp']
        if base_time <= ts <= end_time:
            progress = (ts - base_time).total_seconds() / 60 / duration_minutes
            item['value'] = round(0.03 + 0.09 * progress, 4)
            affected_points.append(item)
    return affected_points
