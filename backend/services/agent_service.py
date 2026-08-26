"""
Agent 服务层
P0-5: 封装 LangGraph Agent，供 API 层调用

职责:
1. 创建并管理 Agent 实例（单例）
2. 调用 Agent 工作流（intent_router → tool_executor → response_generator）
3. 从 AgentState 提取结构化数据（chart_data, diagnosis）
4. 当 LLM 可用时，用 DeepSeek 增强自然语言诊断回复
5. 返回 API 层所需的标准响应格式
"""
import json
import logging
from typing import Any

from agent.graph.workflow import create_agent
from agent.prompts.llm_client import is_llm_available, call_deepseek
from agent.prompts.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


# ============================================================
# Agent 单例
# ============================================================

_agent_instance = None


def get_agent():
    """获取 Agent 单例（延迟初始化）"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = create_agent()
        logger.info("Agent 工作流实例已创建")
    return _agent_instance


# ============================================================
# 结构化数据提取
# ============================================================

def _extract_chart_data(tool_results: dict[str, Any]) -> dict | None:
    """
    从 data_tool 结果中提取图表数据，供前端 ECharts 渲染。
    """
    data_result = tool_results.get("data_tool")
    if not data_result or not isinstance(data_result, dict):
        return None
    if "error" in data_result or "data" not in data_result:
        return None

    data_points = data_result.get("data", [])
    if not data_points:
        return None

    return {
        "device_id": data_result.get("device_id"),
        "parameter": data_result.get("parameter"),
        "unit": data_result.get("unit", ""),
        "times": [p.get("time", "") for p in data_points],
        "values": [p.get("value", 0) for p in data_points],
        "stats": data_result.get("stats"),
    }


def _extract_diagnosis(tool_results: dict[str, Any], params: dict) -> dict | None:
    """
    从 alarm_tool 结果中提取诊断摘要，供前端诊断卡片展示。
    """
    alarm_result = tool_results.get("alarm_tool")
    if not alarm_result or not isinstance(alarm_result, dict):
        return None
    if "error" in alarm_result:
        return None

    risk_score = alarm_result.get("risk_score", 0)
    alarms = alarm_result.get("alarms", [])

    # 风险等级（与 RiskScorer 阈值口径统一：0.3/0.6 分 low/medium/high）
    if risk_score >= 0.6:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    # 从 RAG 结果中提取知识引用
    knowledge_refs = []
    rag_result = tool_results.get("rag_tool")
    if isinstance(rag_result, list):
        for doc in rag_result[:3]:
            knowledge_refs.append({
                "source": doc.get("source", ""),
                "similarity": doc.get("similarity", 0),
            })

    # 从预测结果中提取趋势
    trend_info = None
    pred_result = tool_results.get("predict_tool")
    if pred_result and isinstance(pred_result, dict) and "error" not in pred_result:
        trend_info = {
            "trend": pred_result.get("trend", "stable"),
            "confidence": pred_result.get("confidence", 0),
        }

    return {
        "device_id": alarm_result.get("device_id", params.get("device_id", "")),
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "alarm_count": len(alarms),
        "alarms": alarms,
        "knowledge_refs": knowledge_refs,
        "trend_info": trend_info,
        "params": params,
    }


# ============================================================
# LLM 增强回复
# ============================================================

_DIAGNOSIS_PROMPT = """\
你是 Power-Agent 电厂智能预警与故障诊断助手。
用户提出了一个问题，系统已自动查询了设备数据并执行了异常检测。

请根据以下工具返回的结果，生成一段专业、简洁的中文诊断回复。
回复应包含：
1. 设备状态概述
2. 异常发现（如果有）
3. 风险评估
4. 处置建议

如果数据正常，请说明设备运行平稳。
请直接输出诊断文本，不要使用 markdown 代码块。
"""


def _build_llm_context(message: str, intent: str, tool_results: dict) -> str:
    """将用户消息和 Tool 结果拼接为 LLM 上下文"""
    parts = [f"用户问题: {message}", f"识别意图: {intent}", ""]

    for tool_name, result in tool_results.items():
        if isinstance(result, dict) and "error" not in result:
            parts.append(f"[{tool_name} 返回结果]")
            parts.append(json.dumps(result, ensure_ascii=False, default=str))
            parts.append("")
        elif isinstance(result, list):
            parts.append(f"[{tool_name} 返回结果]")
            parts.append(json.dumps(result, ensure_ascii=False, default=str))
            parts.append("")

    return "\n".join(parts)


def _enhance_with_llm(
    message: str,
    intent: str,
    tool_results: dict,
    template_response: str,
) -> str:
    """
    当 LLM 可用时，用 DeepSeek 生成自然语言诊断回复。
    LLM 不可用或调用失败时，降级为模板回复。
    """
    if not is_llm_available():
        return template_response

    # chat 意图不需要增强
    if intent == "chat":
        return template_response

    context = _build_llm_context(message, intent, tool_results)

    messages = [
        {"role": "system", "content": _DIAGNOSIS_PROMPT},
        {"role": "user", "content": context},
    ]

    try:
        enhanced = call_deepseek(messages, temperature=0.3, max_tokens=1024)
        logger.info("[LLM] 诊断回复增强成功")
        return enhanced
    except Exception as e:
        logger.warning(f"[LLM] 诊断回复增强失败，降级为模板: {e}")
        return template_response


# ============================================================
# 核心入口
# ============================================================

def run_agent(message: str, mode: str = "chat") -> dict:
    """
    运行 Agent 工作流，返回结构化响应。

    流程:
        1. 调用 LangGraph Agent（intent_router → tool_executor → response_generator）
        2. 从 AgentState 提取 chart_data 和 diagnosis
        3. 当 LLM 可用时，用 DeepSeek 增强自然语言回复

    Args:
        message: 用户自然语言输入
        mode: 对话模式 (chat / diagnose / predict)

    Returns:
        {
            "reply": str,               # 自然语言回复
            "intent": str,              # 识别的意图
            "mode": str,                # 对话模式
            "chart_data": dict | None,  # 图表数据（时序数据）
            "diagnosis": dict | None,   # 诊断结果
            "tool_calls": list,         # Tool 调用记录
        }
    """
    agent = get_agent()

    # 调用 Agent 工作流
    logger.info(f"[agent_service] 调用 Agent, mode={mode}, message={message[:50]}...")
    state = agent.invoke({"messages": [message]})

    intent = state.get("intent", "chat")
    params = state.get("params", {})
    tool_results = state.get("tool_results", {})
    tool_calls = state.get("tool_calls", [])
    template_response = state.get("final_response", "")

    # 提取结构化数据
    chart_data = _extract_chart_data(tool_results)
    diagnosis = _extract_diagnosis(tool_results, params)

    # LLM 增强回复
    reply = _enhance_with_llm(message, intent, tool_results, template_response)

    return {
        "reply": reply,
        "intent": intent,
        "mode": mode,
        "chart_data": chart_data,
        "diagnosis": diagnosis,
        "tool_calls": tool_calls,
    }


def run_agent_simple(message: str) -> str:
    """
    简化版调用：仅返回回复文本（用于 health check 或轻量场景）。
    """
    result = run_agent(message, mode="chat")
    return result["reply"]
