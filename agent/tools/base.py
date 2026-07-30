"""
Tool 接口规范定义
P0-1 (Week 1): 接口契约 — B 和 D 按此签名实现
P0-2 (Week 2): Mock 实现 — B/D 的真实函数到位后替换

本文件定义了所有 Tool 的函数签名和返回格式。
B（工业数据与算法负责人）和 D（RAG 知识库负责人）必须按此规范实现。
"""
from typing import Any


# ============================================================
# B 负责的 Tool 签名
# ============================================================

def data_tool(params: dict) -> dict:
    """
    [B 实现] 查询设备时序数据

    输入:
        {
            "device_id": "boiler_002",
            "parameter": "steam_temp",
            "start_time": "2026-07-10T00:00:00",
            "end_time": "2026-07-11T00:00:00"
        }

    输出:
        {
            "device_id": "boiler_002",
            "parameter": "steam_temp",
            "unit": "℃",
            "data": [
                {"time": "2026-07-10T00:00:00", "value": 540.5},
                ...
            ],
            "stats": {"min": 535.0, "max": 575.0, "avg": 548.3, "count": 1440}
        }
    """
    raise NotImplementedError("B 负责实现: backend/services/data_service.py")


def alarm_tool(device_id: str, hours: int = 24) -> dict:
    """
    [B 实现] 检测设备异常

    输入: device_id="boiler_002", hours=24
    输出:
        {
            "device_id": "boiler_002",
            "risk_score": 0.85,
            "alarms": [
                {
                    "type": "threshold",
                    "parameter": "steam_temp",
                    "current_value": 565.0,
                    "threshold": 550.0,
                    "severity": "high",
                    "triggered_at": "2026-07-10T14:30:00"
                }
            ]
        }
    """
    raise NotImplementedError("B 负责实现: backend/services/alarm_service.py")


def predict_tool(device_id: str, parameter: str, hours: int = 6) -> dict:
    """
    [B 实现] 预测未来趋势

    输入: device_id="boiler_002", parameter="steam_temp", hours=6
    输出:
        {
            "predictions": [
                {"time": "2026-07-11T01:00:00", "value": 545.2},
                ...
            ],
            "trend": "rising",
            "confidence": 0.92
        }
    """
    raise NotImplementedError("B 负责实现: algorithms/prediction/")


# ============================================================
# D 负责的 Tool 签名
# ============================================================

def rag_tool(query: str, top_k: int = 3) -> list[dict]:
    """
    [D 实现] RAG 知识检索

    输入: query="主蒸汽温度过高原因", top_k=3
    输出:
        [
            {
                "source": "锅炉运行规程 §3.2",
                "content": "主蒸汽温度过高时，应检查减温水系统...",
                "similarity": 0.94
            },
            ...
        ]
    """
    raise NotImplementedError("D 负责实现: rag/retriever/")


# ============================================================
# A 负责的 Tool 签名
# ============================================================

def report_tool(diagnosis: dict) -> str:
    """
    [A 实现] 生成诊断报告（P1-1）

    输入: diagnosis={"device_id": "...", "risk_score": 0.85, "causes": [...], "suggestions": [...]}
    输出: Markdown 格式诊断报告字符串
    """
    raise NotImplementedError("A 负责实现: P1-1 阶段")


# ============================================================
# Tool 注册表 — 供 workflow 查找
# ============================================================

TOOL_REGISTRY: dict[str, Any] = {
    "data_tool": data_tool,
    "alarm_tool": alarm_tool,
    "predict_tool": predict_tool,
    "rag_tool": rag_tool,
    "report_tool": report_tool,
}

# 意图 → Tool 映射
INTENT_TOOL_MAP: dict[str, list[str]] = {
    "data_query":         ["data_tool"],
    "anomaly_detection":  ["data_tool", "alarm_tool"],
    "prediction":         ["data_tool", "predict_tool"],
    "diagnosis":          ["data_tool", "alarm_tool", "rag_tool"],
    "chat":               [],
}
