"""诊断报告生成 Tool（Week 5 P1-1）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _text(value: Any, default: str = "暂无") -> str:
    text = str(value).strip() if value is not None else ""
    return text or default


def _list(value: Any, fallback: list[str]) -> list[str]:
    if isinstance(value, (list, tuple)):
        result = [str(item).strip() for item in value if str(item).strip()]
        return result or list(fallback)
    if value is not None and str(value).strip():
        return [str(value).strip()]
    return list(fallback)


def _level(score: float, value: Any = None) -> str:
    levels = {
        "low": "低风险", "medium": "中风险", "high": "高风险",
        "低风险": "低风险", "中风险": "中风险", "高风险": "高风险",
    }
    if value is not None and str(value).lower() in levels:
        return levels[str(value).lower()]
    return "高风险" if score >= 0.6 else "中风险" if score >= 0.3 else "低风险"


def _default_causes(alarms: list[dict[str, Any]]) -> list[str]:
    causes: list[str] = []
    for alarm in alarms:
        cause = alarm.get("message") or alarm.get("trend_desc")
        if not cause:
            cause = f"{_text(alarm.get('parameter'), '未知测点')} 检测到 {alarm.get('type', '异常')} 异常"
        cause = str(cause).strip()
        if cause and cause not in causes:
            causes.append(cause)
    return causes or ["当前分析窗口内未检测到明确异常原因。"]


def _default_suggestions(alarm_result: dict[str, Any], alarms: list[dict[str, Any]]) -> list[str]:
    recommendations = _list(alarm_result.get("recommendations"), [])
    if recommendations:
        return recommendations
    if alarms:
        return [
            "请现场核查相关测点、执行机构及保护阈值，确认异常是否持续。",
            "建议结合设备运行规程完成复核，必要时安排检修并持续观察趋势。",
        ]
    return ["设备当前运行平稳，建议保持现有巡检频率并持续关注后续趋势。"]


def build_diagnosis(
    tool_results: dict[str, Any], params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """把多个 Tool 的结果合并成 report_tool 的标准输入。"""
    params = params or {}
    alarm = tool_results.get("alarm_tool")
    alarm = alarm if isinstance(alarm, dict) else {}
    data = tool_results.get("data_tool")
    data = data if isinstance(data, dict) else {}
    prediction = tool_results.get("predict_tool")
    prediction = prediction if isinstance(prediction, dict) else {}
    rag = tool_results.get("rag_tool")
    rag = rag if isinstance(rag, list) else []

    alarms = alarm.get("alarms", [])
    alarms = [item for item in alarms if isinstance(item, dict)] if isinstance(alarms, list) else []
    score = _score(alarm.get("risk_score", 0))
    refs = [
        {"source": item.get("source", ""), "content": item.get("content", ""),
         "similarity": item.get("similarity", 0)}
        for item in rag[:3]
        if isinstance(item, dict)
    ]
    device_id = (
        alarm.get("device_id") or data.get("device_id") or prediction.get("device_id")
        or params.get("device_id") or "未知设备"
    )
    return {
        "device_id": device_id,
        "device_name": alarm.get("device_name") or data.get("device_name")
        or prediction.get("device_name") or device_id,
        "diagnosis_time": alarm.get("analysis_time") or prediction.get("generated_at")
        or datetime.now().isoformat(),
        "analysis_window_hours": alarm.get(
            "analysis_window_hours", params.get("time_range_hours", 24)
        ),
        "risk_score": score,
        "risk_level": _level(score, alarm.get("risk_level")),
        "alarms": alarms,
        "causes": _list(params.get("causes"), _default_causes(alarms)),
        "suggestions": _list(
            params.get("suggestions"), _default_suggestions(alarm, alarms)
        ),
        "trend_info": (
            {
                "trend": prediction.get("trend", "stable"),
                "confidence": prediction.get("confidence", 0),
                "last_actual_value": prediction.get("last_actual_value"),
                "last_predicted_value": prediction.get("last_predicted_value"),
            }
            if prediction and "error" not in prediction
            else None
        ),
        "knowledge_refs": refs,
        "data_summary": data.get("stats") if "error" not in data else None,
    }


def report_tool(diagnosis: dict[str, Any]) -> str:
    """生成包含设备、风险、异常、趋势、原因和建议的 Markdown 报告。"""
    diagnosis = diagnosis if isinstance(diagnosis, dict) else {}
    score = _score(diagnosis.get("risk_score", 0))
    alarms = diagnosis.get("alarms", [])
    alarms = [item for item in alarms if isinstance(item, dict)] if isinstance(alarms, list) else []
    causes = _list(diagnosis.get("causes"), _default_causes(alarms))
    suggestions = _list(diagnosis.get("suggestions"), ["待生成"])
    trend = diagnosis.get("trend_info")
    refs = diagnosis.get("knowledge_refs", [])
    stats = diagnosis.get("data_summary")

    lines = [
        "# 设备诊断报告", "", "## 设备信息",
        f"- 设备名称: {_text(diagnosis.get('device_name'), diagnosis.get('device_id', '未知设备'))}",
        f"- 设备 ID: `{_text(diagnosis.get('device_id'), '未知设备')}`",
        f"- 诊断时间: {_text(diagnosis.get('diagnosis_time'), '待填写')}",
        f"- 分析窗口: {_text(diagnosis.get('analysis_window_hours'), '24')} 小时", "",
        "## 风险评估", "| 指标 | 值 |", "|------|------|",
        f"| 风险评分 | {score:.2f} |",
        f"| 风险等级 | {_level(score, diagnosis.get('risk_level'))} |",
        f"| 告警数量 | {len(alarms)} |", "", "## 异常摘要",
    ]
    if alarms:
        for index, alarm in enumerate(alarms, 1):
            detail = alarm.get("message") or alarm.get("trend_desc") or alarm.get("type", "异常")
            lines.append(
                f"{index}. **{_text(alarm.get('parameter'), '未知测点')}**"
                f"（{_text(alarm.get('severity'), 'unknown')}）：{_text(detail)}"
            )
    else:
        lines.append("- 当前分析窗口内未检测到告警。")

    lines.extend(["", "## 趋势分析"])
    if isinstance(trend, dict):
        lines.extend([
            f"- 预测趋势: {_text(trend.get('trend'), 'stable')}",
            f"- 预测置信度: {_score(trend.get('confidence', 0)):.2f}",
        ])
        if trend.get("last_actual_value") is not None:
            lines.append(f"- 最后实际值: {trend['last_actual_value']}")
        if trend.get("last_predicted_value") is not None:
            lines.append(f"- 最后预测值: {trend['last_predicted_value']}")
    else:
        lines.append("- 当前诊断未包含预测结果。")

    # 保留既有报告契约中的标题，新增内容仍覆盖原因分析。
    lines.extend(["", "## 异常原因"])
    lines.extend(f"{index}. {cause}" for index, cause in enumerate(causes, 1))
    lines.extend(["", "## 处置建议"])
    lines.extend(f"{index}. {suggestion}" for index, suggestion in enumerate(suggestions, 1))

    if isinstance(stats, dict):
        lines.extend([
            "", "## 数据概览", f"- 最小值: {_text(stats.get('min'))}",
            f"- 最大值: {_text(stats.get('max'))}", f"- 平均值: {_text(stats.get('avg'))}",
            f"- 数据点数: {_text(stats.get('count'))}",
        ])

    lines.extend(["", "## 知识依据"])
    if refs:
        for index, ref in enumerate(refs[:3], 1):
            lines.append(
                f"{index}. **{_text(ref.get('source'), '未知来源')}**"
                f"（相似度: {_score(ref.get('similarity', 0)):.2f}）"
            )
            content = " ".join(_text(ref.get("content"), "").split())
            if content:
                lines.append(f"   - {content}")
    else:
        lines.append("- 本次未返回知识库引用。")

    lines.extend(["", "---", "*Power-Agent 智能预警系统 自动生成*"])
    return "\n".join(lines) + "\n"


def report_tool_mock(diagnosis: dict[str, Any]) -> str:
    """兼容旧调用方的入口，格式与正式 Tool 一致。"""
    return report_tool(diagnosis)