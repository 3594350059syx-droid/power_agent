"""实时遥测数据读取服务。

Dashboard 使用的设备和测点契约在此集中定义。数据库中 3 个配置测点都有
最新记录时返回真实数据；数据库不可用或数据尚未初始化时由 API 层降级为
契约 Mock，从而保证开发和演示环境都能稳定运行。
"""

import logging

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.database.models import Device, SensorPoint, TimeseriesData

logger = logging.getLogger(__name__)


DEVICE_METRICS = {
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

_SUPPORTED_DEVICE_STATUSES = {
    "running", "normal", "warn", "warning", "danger", "error", "stopped",
}


def _metric_level(value: float, sensor: SensorPoint) -> str:
    """根据真实测点的正常区间和阈值映射 Dashboard 状态。"""
    if (
        (sensor.threshold_high is not None and value > sensor.threshold_high)
        or (sensor.threshold_low is not None and value < sensor.threshold_low)
    ):
        return "danger"
    if (
        (sensor.normal_max is not None and value > sensor.normal_max)
        or (sensor.normal_min is not None and value < sensor.normal_min)
    ):
        return "warn"
    return "normal"


def _device_status(device: Device) -> str:
    """限制返回状态为前端 StatusIndicator 可识别的枚举值。"""
    status = (device.status or "running").lower()
    return status if status in _SUPPORTED_DEVICE_STATUSES else "unknown"


def get_database_live_telemetry(device_id: str, db: Session | None = None) -> dict | None:
    """读取一台设备每个配置测点的最新数据库记录。

    返回 ``None`` 表示无法形成完整的真实 3 测点快照（连接失败、设备/测点不
    存在或有测点尚无数据）。调用方应在已知设备场景降级为 Mock，不能将其视为
    未知设备。

    ``db`` 仅用于服务级测试或复用；未传入时函数自行创建并关闭 Session。
    """
    metric_definitions = DEVICE_METRICS.get(device_id)
    if not metric_definitions:
        return None

    owns_session = db is None
    db = db or SessionLocal()
    try:
        device = db.query(Device).filter(Device.device_code == device_id).first()
        if not device:
            return None

        metric_by_key = {metric["key"]: metric for metric in metric_definitions}
        sensors = db.query(SensorPoint).filter(
            SensorPoint.device_id == device.id,
            SensorPoint.point_name.in_(metric_by_key),
        ).all()
        sensor_by_key = {sensor.point_name: sensor for sensor in sensors}
        if set(sensor_by_key) != set(metric_by_key):
            logger.info("设备 %s 的实时测点尚未完整初始化，降级为 Mock", device_id)
            return None

        sensor_ids = [sensor.id for sensor in sensors]
        latest_times = db.query(
            TimeseriesData.sensor_id.label("sensor_id"),
            func.max(TimeseriesData.recorded_at).label("recorded_at"),
        ).filter(
            TimeseriesData.device_id == device.id,
            TimeseriesData.sensor_id.in_(sensor_ids),
        ).group_by(TimeseriesData.sensor_id).subquery()

        latest_rows = db.query(TimeseriesData).join(
            latest_times,
            and_(
                TimeseriesData.sensor_id == latest_times.c.sensor_id,
                TimeseriesData.recorded_at == latest_times.c.recorded_at,
            ),
        ).all()
        value_by_sensor_id = {row.sensor_id: row.value for row in latest_rows}
        if len(value_by_sensor_id) != len(metric_definitions):
            logger.info("设备 %s 的实时数据尚未完整写入，降级为 Mock", device_id)
            return None

        metrics = []
        for definition in metric_definitions:
            sensor = sensor_by_key[definition["key"]]
            normal_range = [
                sensor.normal_min if sensor.normal_min is not None else definition["normal_range"][0],
                sensor.normal_max if sensor.normal_max is not None else definition["normal_range"][1],
            ]
            value = value_by_sensor_id[sensor.id]
            metrics.append({
                "key": definition["key"],
                "name": definition["name"],
                "unit": sensor.unit or definition["unit"],
                "normal_range": normal_range,
                "value": round(value, definition["digits"]),
                "level": _metric_level(value, sensor),
            })

        return {
            "device_status": {
                "device_id": device_id,
                "status": _device_status(device),
            },
            "metrics": metrics,
        }
    except SQLAlchemyError as exc:
        logger.warning("读取设备 %s 的实时数据库遥测失败，降级为 Mock: %s", device_id, exc)
        return None
    finally:
        if owns_session:
            db.close()