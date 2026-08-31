"""P0-3 实时遥测接口。

优先读取 TimescaleDB 中的最新遥测数据；数据库不可用或数据未初始化时降级为
可重复调用的 Mock。设备和测点契约与 ``data/mock/config.py`` 保持一致：3 台
设备、每台设备 3 个专属测点。
"""

import math
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from backend.services.telemetry_service import (
    DEVICE_METRICS,
    get_database_history_trend,
    get_database_live_telemetry,
)
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


def _generate_mock_history(device_id: str, parameter: str, hours: int) -> dict:
    """生成确定性的历史趋势，包含一个连续的异常高亮区间。"""
    metric = next(item for item in DEVICE_METRICS[device_id] if item["key"] == parameter)
    normal_min, normal_max = metric["normal_range"]
    sample_count = max(24, min(hours * 4, 672))
    start_time = datetime.now().replace(microsecond=0) - timedelta(hours=hours)
    step = timedelta(seconds=hours * 3600 / (sample_count - 1))
    midpoint = (normal_min + normal_max) / 2
    amplitude = (normal_max - normal_min) * 0.28
    anomaly_start = int(sample_count * 0.65)
    anomaly_end = min(anomaly_start + 3, sample_count)

    timestamps = []
    values = []
    anomaly_ranges = []
    for index in range(sample_count):
        timestamp = (start_time + step * index).isoformat()
        value = midpoint + math.sin(index / 4) * amplitude
        if anomaly_start <= index < anomaly_end:
            value = normal_max + (normal_max - normal_min) * (1.35 + (index - anomaly_start) * 0.08)
            if index == anomaly_start:
                anomaly_ranges.append({"start": timestamp, "end": timestamp})
            else:
                anomaly_ranges[-1]["end"] = timestamp
        timestamps.append(timestamp)
        values.append(round(value, metric["digits"]))

    return {
        "device_id": device_id,
        "parameter": parameter,
        "unit": metric["unit"],
        "timestamps": timestamps,
        "values": values,
        "anomaly_ranges": anomaly_ranges,
    }


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


@router.get("/telemetry/history")
def get_history_trend(
    device_id: str = Query(
        "boiler_002",
        description="设备 ID：boiler_002、turbine_003 或 generator_004",
    ),
    parameter: str = Query("steam_temp", description="设备所属的测点 key"),
    hours: int = Query(24, ge=1, le=168, description="历史时间范围（小时）"),
):
    """获取单台设备一个测点的历史趋势和连续异常区间。"""
    metric_keys = {metric["key"] for metric in DEVICE_METRICS.get(device_id, [])}
    if parameter not in metric_keys:
        return success_response(
            data={
                "device_id": device_id,
                "parameter": parameter,
                "unit": "",
                "timestamps": [],
                "values": [],
                "anomaly_ranges": [],
            },
            message="设备或测点不存在",
        )

    data = get_database_history_trend(device_id, parameter, hours)
    if data is None:
        data = _generate_mock_history(device_id, parameter, hours)

    return success_response(data=data, message="ok")