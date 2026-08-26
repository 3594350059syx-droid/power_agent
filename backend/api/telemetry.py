"""P0-3 实时遥测接口。

当前阶段以可重复调用的 Mock 数据支撑前端监控面板。设备和测点契约与
``data/mock/config.py`` 保持一致：3 台设备、每台设备 3 个专属测点。
数据库实时查询接入后应保持本接口的响应结构不变。
"""

import random

from fastapi import APIRouter, Query

from backend.utils.response import success_response

router = APIRouter(tags=["telemetry"])

_DEVICE_METRICS = {
    "boiler_002": [
        {"key": "steam_temp", "name": "主蒸汽温度", "unit": "℃", "normal_range": [525, 555], "digits": 1},
        {"key": "steam_pressure", "name": "主蒸汽压力", "unit": "MPa", "normal_range": [16.2, 17.2], "digits": 2},
        {"key": "furnace_temp", "name": "炉膛温度", "unit": "℃", "normal_range": [1150, 1250], "digits": 1},
    ],
    "turbine_003": [
        {"key": "rpm", "name": "转速", "unit": "rpm", "normal_range": [2950, 3050], "digits": 0},
        {"key": "bearing_temp", "name": "轴承温度", "unit": "℃", "normal_range": [75, 95], "digits": 1},
        {"key": "vibration", "name": "振动", "unit": "mm", "normal_range": [0.01, 0.05], "digits": 3},
    ],
    "generator_004": [
        {"key": "power", "name": "有功功率", "unit": "MW", "normal_range": [250, 350], "digits": 1},
        {"key": "stator_temp", "name": "定子温度", "unit": "℃", "normal_range": [90, 120], "digits": 1},
        {"key": "reactive_power", "name": "无功功率", "unit": "Mvar", "normal_range": [30, 70], "digits": 1},
    ],
}


def _generate_mock_metrics(device_id: str) -> list[dict]:
    """生成指定设备的 3 个实时测点，不为未知设备制造错误回退数据。"""
    result = []
    for metric in _DEVICE_METRICS.get(device_id, []):
        normal_min, normal_max = metric["normal_range"]
        digits = metric["digits"]

        if random.random() < 0.15:
            # 产生正常区间外的少量预警/异常样本，便于仪表盘验证状态颜色。
            value = random.uniform(normal_max * 1.02, normal_max * 1.15)
            level = "warn" if random.random() < 0.7 else "danger"
        else:
            value = random.uniform(normal_min, normal_max)
            level = "normal"

        result.append({
            "key": metric["key"],
            "name": metric["name"],
            "unit": metric["unit"],
            "normal_range": metric["normal_range"],
            "value": round(value, digits),
            "level": level,
        })
    return result


@router.get("/telemetry/live")
def get_live_telemetry(
    device_id: str = Query(
        "boiler_002",
        description="设备 ID：boiler_002、turbine_003 或 generator_004",
    ),
):
    """获取单台设备实时遥测数据。"""
    known_device = device_id in _DEVICE_METRICS
    return success_response(
        data={
            "device_status": {
                "device_id": device_id,
                "status": "running" if known_device else "unknown",
            },
            "metrics": _generate_mock_metrics(device_id),
        },
        message="ok",
    )