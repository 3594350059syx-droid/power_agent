"""
Tool 注册中心
P0-2: 统一管理所有 Tool 的 mock/真实实现

B 和 D 的真实函数到位后，在此处替换 mock 为真实导入。
"""
from agent.tools.base import (
    TOOL_REGISTRY,
    INTENT_TOOL_MAP,
)
from agent.tools.data_tool import data_tool_mock, predict_tool_mock
from agent.tools.alarm_tool import alarm_tool_mock
from agent.tools.rag_tool import rag_tool_mock
from agent.tools.report_tool import report_tool_mock


# ============================================================
# Mock 注册 — P0-2 阶段使用 mock 实现
# B/D 真实函数到位后，将下面的 mock 替换为真实导入
# ============================================================

MOCK_REGISTRY = {
    "data_tool": data_tool_mock,
    "alarm_tool": alarm_tool_mock,
    "predict_tool": predict_tool_mock,
    "rag_tool": rag_tool_mock,
    "report_tool": report_tool_mock,
}


def get_tool(name: str):
    """
    获取 Tool 函数（优先返回 mock 实现）

    当 B/D 的真实函数可用时，可通过 TOOL_REGISTRY 获取真实实现。
    P0-2 阶段统一返回 mock。
    """
    return MOCK_REGISTRY.get(name)


def call_tool(name: str, **kwargs):
    """调用指定 Tool（mock 模式）"""
    fn = get_tool(name)
    if fn is None:
        raise ValueError(f"未知的 Tool 名称: {name}")
    return fn(**kwargs)


__all__ = [
    "TOOL_REGISTRY",
    "INTENT_TOOL_MAP",
    "MOCK_REGISTRY",
    "get_tool",
    "call_tool",
]
