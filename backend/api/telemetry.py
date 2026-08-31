"""P0-3 实时遥测接口。

优先读取 TimescaleDB 中的最新遥测数据；数据库不可用或数据未初始化时降级为
可重复调用的 Mock。设备和测点契约与 ``data/mock/config.py`` 保持一致：3 台
设备、每台设备 3 个专属测点。
"""

import random

from fastapi import APIRouter, Query

from backend.services.telemetry_service import DEVICE_METRICS, get_database_live_telemetry
from backend.utils.response import success_response

router = APIRouter(tags=["telemetry"])


def _generate_mock_metrics(device_id: str) -> list[dict]:
    """生成指定设备的 3 个实时测点，不为未知设备制造错误回退数据。"""
    result = []
    for metric in DEVICE_METRICS.get(device_id, []):
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
    known_device = device_id in DEVICE_METRICS
    if not known_device:
        data = {
            "device_status": {"device_id": device_id, "status": "unknown"},
            "metrics": [],
        }
    else:
        # 真实库中必须同时存在该设备的 3 个配置测点最新值；否则返回完整的
        # Mock 快照，避免在一个仪表盘中混入不同来源和时间点的数据。
        data = get_database_live_telemetry(device_id)
        if data is None:
            data = {
                "device_status": {"device_id": device_id, "status": "running"},
                "metrics": _generate_mock_metrics(device_id),
            }

    return success_response(
        data=data,
        message="ok",
    )