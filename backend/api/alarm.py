"""告警中心的查询和确认接口。"""

from datetime import datetime

from fastapi import APIRouter, Query

from backend.services.alarm_service import acknowledge_alarm, list_alarm_records
from backend.utils.response import error_response, success_response

router = APIRouter(tags=["alarm"])


# 数据库未初始化时保持和实时遥测相同的可演示降级策略。字段与真实接口完全一致，
# 前端不需要因数据来源不同维护另一套结构。
MOCK_ALARMS = [
    {
        "id": 1,
        "device_id": "boiler_002",
        "device_name": "2号锅炉",
        "parameter": "steam_temp",
        "parameter_name": "主蒸汽温度",
        "alarm_type": "threshold",
        "severity": "high",
        "current_value": 568.0,
        "threshold_value": 550.0,
        "message": "主蒸汽温度超过高阈值",
        "status": "pending",
        "triggered_at": "2026-08-31T14:23:15",
    },
    {
        "id": 2,
        "device_id": "turbine_003",
        "device_name": "3号汽轮机",
        "parameter": "vibration",
        "parameter_name": "振动",
        "alarm_type": "trend",
        "severity": "medium",
        "current_value": 0.08,
        "threshold_value": 0.05,
        "message": "振动持续上升",
        "status": "pending",
        "triggered_at": "2026-08-31T13:45:02",
    },
    {
        "id": 3,
        "device_id": "generator_004",
        "device_name": "4号发电机",
        "parameter": "stator_temp",
        "parameter_name": "定子温度",
        "alarm_type": "threshold",
        "severity": "low",
        "current_value": 112.0,
        "threshold_value": 105.0,
        "message": "定子温度偏高",
        "status": "acknowledged",
        "triggered_at": "2026-08-31T12:10:33",
    },
    {
        "id": 4,
        "device_id": "boiler_002",
        "device_name": "2号锅炉",
        "parameter": "steam_pressure",
        "parameter_name": "主蒸汽压力",
        "alarm_type": "trend",
        "severity": "medium",
        "current_value": 18.2,
        "threshold_value": 17.5,
        "message": "主蒸汽压力波动异常",
        "status": "pending",
        "triggered_at": "2026-08-31T10:05:21",
    },
    {
        "id": 5,
        "device_id": "turbine_003",
        "device_name": "3号汽轮机",
        "parameter": "bearing_temp",
        "parameter_name": "轴承温度",
        "alarm_type": "threshold",
        "severity": "low",
        "current_value": 78.0,
        "threshold_value": 72.0,
        "message": "轴承温度异常",
        "status": "pending",
        "triggered_at": "2026-08-31T08:30:45",
    },
]


def _filter_mock_alarms(severity: str, sort: str, device_id: str | None) -> list[dict]:
    alarms = [
        alarm.copy()
        for alarm in MOCK_ALARMS
        if (severity == "all" or alarm["severity"] == severity)
        and (device_id is None or alarm["device_id"] == device_id)
    ]
    alarms.sort(
        key=lambda alarm: datetime.fromisoformat(alarm["triggered_at"]),
        reverse=sort == "time_desc",
    )
    return alarms


@router.get("/alarm/list")
def get_alarm_list(
    severity: str = Query("all", pattern="^(all|high|medium|low)$"),
    sort: str = Query("time_desc", pattern="^(time_desc|time_asc)$"),
    device_id: str | None = Query(None, description="可选设备 ID"),
    hours: int | None = Query(None, ge=1, le=168, description="可选历史时间范围（小时）"),
):
    """返回按严重等级过滤、按触发时间排序的告警记录。"""
    alarms = list_alarm_records(
        severity=severity,
        sort=sort,
        device_id=device_id,
        hours=hours,
    )
    if alarms is None:
        alarms = _filter_mock_alarms(severity, sort, device_id)

    return success_response(data={"alarms": alarms, "total": len(alarms)}, message="ok")


@router.post("/alarm/{alarm_id}/acknowledge")
def acknowledge_alarm_record(alarm_id: int):
    """将待处理告警状态更新为 ``acknowledged``。"""
    result = acknowledge_alarm(alarm_id)
    if result is True:
        return success_response(
            data={"id": alarm_id, "status": "acknowledged"},
            message="告警已确认",
        )

    # 当数据库不可用或尚未初始化时，确认同一份降级数据，避免列表和确认操作的
    # 数据来源不一致；真实库中不存在的 ID 则由下方返回错误。
    if result is None:
        for alarm in MOCK_ALARMS:
            if alarm["id"] == alarm_id:
                alarm["status"] = "acknowledged"
                return success_response(
                    data={"id": alarm_id, "status": "acknowledged"},
                    message="告警已确认",
                )

    return error_response(message="告警不存在", data={"id": alarm_id})
