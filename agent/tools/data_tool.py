"""
数据查询 Tool — Mock 实现
P0-2: B 的 data_tool 未到位前使用此 mock

B 完成真实实现后，将 workflow 中的 mock 调用替换为:
    from backend.services.data_service import data_tool
"""
import random
from datetime import datetime, timedelta


def data_tool_mock(params: dict) -> dict:
    """
    Mock: 查询设备时序数据

    生成符合 data_tool 签名的模拟返回值。
    """
    device_id = params.get("device_id", "generator_002")
    parameter = params.get("parameter", "steam_temp")
    hours = params.get("time_range_hours", 24)

    # 参数 → 单位 + 基准值映射
    param_config = {
        "steam_temp":     {"unit": "\u2103",  "base": 540,  "range": 15},
        "steam_pressure": {"unit": "MPa", "base": 16.7, "range": 0.5},
        "furnace_temp":   {"unit": "\u2103",  "base": 1200, "range": 50},
        "rpm":            {"unit": "rpm", "base": 3000, "range": 50},
        "bearing_temp":   {"unit": "\u2103",  "base": 85,   "range": 10},
        "vibration":      {"unit": "mm",  "base": 0.03, "range": 0.02},
        "power":          {"unit": "MW",  "base": 300,  "range": 50},
        "stator_temp":    {"unit": "\u2103",  "base": 105,  "range": 15},
    }

    cfg = param_config.get(parameter, {"unit": "", "base": 100, "range": 10})

    # 生成模拟数据（每小时 1 个点）
    now = datetime.now()
    data = []
    values = []
    for i in range(hours):
        t = now - timedelta(hours=hours - i)
        value = round(cfg["base"] + random.uniform(-cfg["range"], cfg["range"]), 2)
        data.append({"time": t.strftime("%Y-%m-%dT%H:%M:%S"), "value": value})
        values.append(value)

    return {
        "device_id": device_id,
        "parameter": parameter,
        "unit": cfg["unit"],
        "data": data,
        "stats": {
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "avg": round(sum(values) / len(values), 2),
            "count": len(values),
        },
    }


def predict_tool_mock(
    device_id: str = "generator_002",
    parameter: str = "steam_temp",
    hours: int = 6,
) -> dict:
    """
    Mock: 预测设备参数未来走势

    与 real predict_tool 签名一致: (device_id, parameter, hours)。
    """
    param_config = {
        "steam_temp":     {"unit": "℃",  "base": 540,  "trend": 0.8},
        "steam_pressure": {"unit": "MPa", "base": 16.7, "trend": -0.02},
        "furnace_temp":   {"unit": "℃",  "base": 1200, "trend": -2.5},
        "rpm":            {"unit": "rpm", "base": 3000, "trend": 1.2},
        "bearing_temp":   {"unit": "℃",  "base": 85,   "trend": 0.15},
        "vibration":      {"unit": "mm",  "base": 0.03, "trend": 0.002},
        "power":          {"unit": "MW",  "base": 300,  "trend": -1.0},
        "stator_temp":    {"unit": "℃",  "base": 105,  "trend": 0.3},
    }
    cfg = param_config.get(parameter, {"unit": "", "base": 100, "trend": 0})

    from datetime import datetime, timedelta
    now = datetime.now()
    predictions = []
    for i in range(1, hours + 1):
        t = now + timedelta(hours=i)
        value = round(cfg["base"] + cfg["trend"] * i, 2)
        predictions.append({"time": t.strftime("%Y-%m-%dT%H:%M:%S"), "value": value})

    return {
        "device_id": device_id,
        "parameter": parameter,
        "unit": cfg["unit"],
        "predictions": predictions,
        "trend": "上升" if cfg["trend"] > 0 else "下降",
        "forecast_hours": hours,
    }
