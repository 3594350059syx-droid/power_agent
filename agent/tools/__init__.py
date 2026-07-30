"""
Tool 注册中心
P0-4: 统一管理所有 Tool 的真实/mock 实现

P0-5: D 的 RAG Tool 真实实现已对接

__init__ 自动检测各模块可用性：
- B 的 data_tool / alarm_tool: 数据库可用时使用真实实现，否则降级 mock
- D 的 rag_tool: faiss + sentence-transformers 可用时使用真实实现，否则降级 mock
- predict_tool: B 的 P1-1 未完成，暂用 mock
- report_tool: A 的 P1-1 未实现，暂用 mock
"""
import logging

from agent.tools.base import (
    TOOL_REGISTRY,
    INTENT_TOOL_MAP,
)

logger = logging.getLogger(__name__)

# ============================================================
# Mock 实现（始终可用，不依赖数据库）
# ============================================================
from agent.tools.data_tool_mock import data_tool_mock, predict_tool_mock
from agent.tools.alarm_tool_mock import alarm_tool_mock
from agent.tools.rag_tool import rag_tool_mock
from agent.tools.report_tool import report_tool_mock

MOCK_REGISTRY = {
    "data_tool": data_tool_mock,
    "alarm_tool": alarm_tool_mock,
    "predict_tool": predict_tool_mock,
    "rag_tool": rag_tool_mock,
    "report_tool": report_tool_mock,
}

# ============================================================
# 真实实现（依赖数据库，导入失败则降级为 mock）
# ============================================================
_REAL_REGISTRY = {}

# B 的真实实现（依赖数据库）
try:
    from agent.tools.data_tool import data_tool as _real_data_tool
    from agent.tools.alarm_tool import alarm_tool as _real_alarm_tool
    _REAL_REGISTRY["data_tool"] = _real_data_tool
    _REAL_REGISTRY["alarm_tool"] = _real_alarm_tool
    logger.info("B 的真实 Tool 实现已加载（data_tool, alarm_tool）")
except Exception as e:
    logger.warning(f"B 的真实 Tool 不可用，降级为 mock: {e}")

# D 的真实实现（依赖 faiss + sentence-transformers）
try:
    from rag.rag_tool import rag_tool as _real_rag_tool
    _REAL_REGISTRY["rag_tool"] = _real_rag_tool
    logger.info("D 的真实 RAG Tool 实现已加载（rag_tool）")
except Exception as e:
    logger.warning(f"D 的真实 RAG Tool 不可用，降级为 mock: {e}")

# ============================================================
# 活跃注册表：优先真实实现，降级为 mock
# ============================================================
ACTIVE_REGISTRY = {
    "data_tool": _REAL_REGISTRY.get("data_tool", data_tool_mock),
    "alarm_tool": _REAL_REGISTRY.get("alarm_tool", alarm_tool_mock),
    "predict_tool": predict_tool_mock,   # P1-1 未完成，暂用 mock
    "rag_tool": _REAL_REGISTRY.get("rag_tool", rag_tool_mock),
    "report_tool": report_tool_mock,     # A 的 P1-1 待实现
}


def get_tool(name: str):
    """
    获取 Tool 函数（优先真实实现，降级为 mock）

    Returns:
        callable or None
    """
    return ACTIVE_REGISTRY.get(name)


def call_tool(name: str, **kwargs):
    """调用指定 Tool（真实实现失败时自动降级为 mock）"""
    fn = get_tool(name)
    if fn is None:
        raise ValueError(f"未知的 Tool 名称: {name}")

    # 真实实现调用失败时，自动降级为 mock
    if name in _REAL_REGISTRY and _REAL_REGISTRY[name] is fn:
        try:
            return fn(**kwargs)
        except Exception as e:
            logger.warning(f"真实 Tool '{name}' 调用失败，降级为 mock: {e}")
            mock_fn = MOCK_REGISTRY.get(name)
            if mock_fn:
                return mock_fn(**kwargs)
            raise

    return fn(**kwargs)


def is_real_available(tool_name: str) -> bool:
    """检查指定 Tool 是否使用真实实现"""
    return tool_name in _REAL_REGISTRY and _REAL_REGISTRY[tool_name] is ACTIVE_REGISTRY.get(tool_name)


__all__ = [
    "TOOL_REGISTRY",
    "INTENT_TOOL_MAP",
    "MOCK_REGISTRY",
    "ACTIVE_REGISTRY",
    "get_tool",
    "call_tool",
    "is_real_available",
]
