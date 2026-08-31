"""诊断报告服务。

报告不写入数据库：每次请求都复用 Agent 的诊断链路按需生成，保证报告内容
与当前数据、告警、预测和知识检索结果一致。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.services.agent_service import run_agent


def _report_message(device_id: str, hours: int) -> str:
    # 使用 anomaly_detection 链路即可生成报告；避免“诊断”关键词触发
    # 专用于故障问答的 RAG 重型初始化，报告接口仍会复用告警/数据结果。
    return f"分析设备 {device_id} 过去 {hours} 小时的异常并生成报告"


def get_latest_report(device_id: str, hours: int = 24) -> dict[str, Any]:
    """生成并返回指定设备的最新诊断报告。"""
    if not device_id or not device_id.strip():
        raise ValueError("device_id 不能为空")

    normalized_device_id = device_id.strip()
    result = run_agent(
        _report_message(normalized_device_id, hours), mode="diagnose"
    )
    report = result.get("report")
    if not isinstance(report, str) or not report.strip():
        raise RuntimeError("未生成有效诊断报告")

    return {
        "device_id": normalized_device_id,
        "report": report,
        "diagnosis": result.get("diagnosis"),
        "generated_at": datetime.now().isoformat(),
    }