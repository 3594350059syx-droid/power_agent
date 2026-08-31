"""
Tool 注册中心
P0-4: 统一管理所有 Tool 的真实/mock 实现

P0-5: D 的 RAG Tool 真实实现已对接

__init__ 自动检测各模块可用性：
- B 的 data_tool / alarm_tool: 数据库可用时使用真实实现，否则降级 mock
- D 的 rag_tool: faiss + sentence-transformers 可用时使用真实实现，否则降级 mock
- predict_tool: B 的 P1-1 已完成，数据库可用时使用真实实现，否则降级 mock
- report_tool: A 的 P1-1 正式 Markdown 实现
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
from agent.tools.report_tool import report_tool, report_tool_mock

MOCK_REGISTRY = {
    "data_tool": data_tool_mock,
    "alarm_tool": alarm_tool_mock,
    "predict_tool": predict_tool_mock,
    "rag_tool": rag_tool_mock,
    "report_tool": report_tool_mock,
}

# ============================================================
# 真实实现（依赖数据库/模型，首次调用时延迟加载）
# ============================================================
#
# 不在包导入阶段加载真实实现：RAG 的 SentenceTransformer 会在 import
# 时加载模型，导致不使用 RAG 的 API（例如报告接口）也被网络/模型初始化
# 阻塞。首次调用对应 Tool 时仍会优先加载真实实现，失败后沿用 mock 降级。
_REAL_REGISTRY = {}
_REAL_LOADERS = {
    "data_tool": ("agent.tools.data_tool", "data_tool"),
    "alarm_tool": ("agent.tools.alarm_tool", "alarm_tool"),
    "predict_tool": ("agent.tools.predict_tool", "predict_tool"),
    "rag_tool": ("rag.rag_tool", "rag_tool"),
}
_REAL_LOAD_FAILURES: set[str] = set()


def _load_real_tool(name: str):
    """按需加载真实 Tool，返回 None 表示不可用。"""
    if name in _REAL_REGISTRY:
        return _REAL_REGISTRY[name]
    if name in _REAL_LOAD_FAILURES or name not in _REAL_LOADERS:
        return None

    module_name, attribute_name = _REAL_LOADERS[name]
    try:
        from importlib import import_module

        fn = getattr(import_module(module_name), attribute_name)
        _REAL_REGISTRY[name] = fn
        logger.info("真实 Tool 已按需加载: %s", name)
        return fn
    except Exception as exc:
        _REAL_LOAD_FAILURES.add(name)
        logger.warning("真实 Tool '%s' 不可用，降级为 mock: %s", name, exc)
        return None


# ============================================================
# 活跃注册表：默认 mock，真实实现首次调用时替换
# ============================================================
ACTIVE_REGISTRY = {
    "data_tool": data_tool_mock,
    "alarm_tool": alarm_tool_mock,
    "predict_tool": predict_tool_mock,
    "rag_tool": rag_tool_mock,
    "report_tool": report_tool,           # A 的 P1-1 正式 Markdown 实现
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
    if name not in ACTIVE_REGISTRY:
        raise ValueError(f"未知的 Tool 名称: {name}")

    # 真实实现按需加载；导入或调用失败时自动降级为 mock。
    real_fn = _load_real_tool(name)
    if real_fn is not None:
        try:
            result = real_fn(**kwargs)
            ACTIVE_REGISTRY[name] = real_fn
            return result
        except Exception as exc:
            logger.warning("真实 Tool '%s' 调用失败，降级为 mock: %s", name, exc)
            mock_fn = MOCK_REGISTRY.get(name)
            if mock_fn:
                ACTIVE_REGISTRY[name] = mock_fn
                return mock_fn(**kwargs)
            raise

    return ACTIVE_REGISTRY[name](**kwargs)


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
