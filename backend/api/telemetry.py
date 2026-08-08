# P0-3 (Week 3): GET /api/v1/telemetry/live — 实时遥测接口
# 依赖：B 的 backend/services/data_service.py 提供 data_tool() 函数
# 当前阶段：占位，B 数据库就绪后实现
# P0-3 (Week 3): GET /api/v1/telemetry/live — 实时遥测接口
# 依赖：B 的 backend/services/data_service.py 提供 data_tool() 函数
# 当前阶段：返回 mock 数据，B 数据库就绪后替换为真实查询

import random
from fastapi import APIRouter, Query
from backend.utils.response import success_response

router = APIRouter(tags=["telemetry"])

_MOCK_METRICS = [
    {"key": "steam_temp", "name": "主蒸汽温度", "unit": "℃", "normal_range": [535, 550]},
    {"key": "steam_pressure", "name": "主蒸汽压力", "unit": "MPa", "normal_range": [15.5, 17.5]},
    {"key": "furnace_temp", "name": "炉膛温度", "unit": "℃", "normal_range": [1000, 1250]},
    {"key": "vibration", "name": "轴承振动", "unit": "mm/s", "normal_range": [0, 4.5]},
    {"key": "lube_oil_temp", "name": "润滑油温度", "unit": "℃", "normal_range": [35, 50]},
    {"key": "feedwater_flow", "name": "给水流量", "unit": "t/h", "normal_range": [200, 280]},
]


def _generate_mock_metrics():
    result = []
    for m in _MOCK_METRICS:
        lo, hi = m["normal_range"]
        mid = (lo + hi) / 2
        if random.random() < 0.15:
            value = round(random.uniform(hi * 1.02, hi * 1.15), 1)
            level = "warn" if random.random() < 0.7 else "danger"
        else:
            value = round(random.uniform(lo, hi), 1)
            level = "normal"
        result.append({**m, "value": value, "level": level})
    return result


@router.get("/telemetry/live")
def get_live_telemetry(device_id: str = Query("dev_001", description="设备ID")):
    metrics = _generate_mock_metrics()
    return success_response(
        data={
            "device_status": {"device_id": device_id, "status": "running"},
            "metrics": metrics,
        },
        message="ok",
    )