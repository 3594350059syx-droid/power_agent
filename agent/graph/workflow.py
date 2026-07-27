"""
LangGraph Agent 工作流
P0-2: Agent 状态与工作流构建

节点流程:
    intent_router → tool_executor → response_generator
                        ↑ (chat 意图跳过)

当 LangGraph 已安装时使用 StateGraph，
未安装时降级为 SimpleAgent（纯 Python 状态机，接口一致）。
"""
import logging
from typing import Any

from agent.graph.state import AgentState
from agent.prompts.system_prompt import (
    SYSTEM_PROMPT,
    classify_intent,
    extract_params,
)
from agent.tools import call_tool
from agent.tools.base import INTENT_TOOL_MAP

logger = logging.getLogger(__name__)


# ============================================================
# 节点 1: intent_router — 意图识别 + 参数抽取
# ============================================================

def intent_router(state: AgentState) -> AgentState:
    """
    解析用户消息，识别意图并抽取参数。

    P0-2 使用关键词规则匹配，P0-3 将替换为 DeepSeek LLM。
    """
    messages = state.get("messages", [])
    user_message = messages[-1] if messages else ""

    intent = classify_intent(user_message)
    params = extract_params(user_message)

    logger.info(f"[intent_router] intent={intent}, params={params}")

    state["intent"] = intent
    state["params"] = params
    state["tool_calls"] = []
    state["tool_results"] = {}
    return state


# ============================================================
# 节点 2: tool_executor — 调用 Mock Tool
# ============================================================

def tool_executor(state: AgentState) -> AgentState:
    """
    根据意图调用对应的 Tool（P0-2 阶段全部使用 mock）。
    """
    intent = state.get("intent", "chat")
    params = state.get("params", {})
    tool_names = INTENT_TOOL_MAP.get(intent, [])

    tool_results: dict[str, Any] = {}
    tool_calls: list[dict[str, Any]] = []

    for tool_name in tool_names:
        logger.info(f"[tool_executor] 调用 {tool_name}")

        try:
            if tool_name == "data_tool":
                result = call_tool("data_tool", params=params)
            elif tool_name == "alarm_tool":
                device_id = params.get("device_id", "generator_002")
                hours = params.get("time_range_hours", 24)
                result = call_tool("alarm_tool", device_id=device_id, hours=hours)
            elif tool_name == "predict_tool":
                device_id = params.get("device_id", "generator_002")
                parameter = params.get("parameter", "steam_temp")
                hours = params.get("time_range_hours", 6)
                result = call_tool("predict_tool", device_id=device_id,
                                   parameter=parameter, hours=hours)
            elif tool_name == "rag_tool":
                query = f"{params.get('parameter', '')} 异常原因"
                result = call_tool("rag_tool", query=query, top_k=3)
            else:
                logger.warning(f"未知 Tool: {tool_name}")
                continue

            tool_results[tool_name] = result
            tool_calls.append({"tool": tool_name, "status": "success"})

        except Exception as e:
            logger.error(f"[tool_executor] {tool_name} 调用失败: {e}")
            tool_results[tool_name] = {"error": str(e)}
            tool_calls.append({"tool": tool_name, "status": "error", "error": str(e)})

    state["tool_calls"] = tool_calls
    state["tool_results"] = tool_results
    return state


# ============================================================
# 节点 3: response_generator — 生成最终响应
# ============================================================

def response_generator(state: AgentState) -> AgentState:
    """
    根据 Tool 返回结果生成最终响应文本。
    P0-2 使用模板拼接，P0-3 将接入 DeepSeek 生成自然语言。
    """
    intent = state.get("intent", "chat")
    params = state.get("params", {})
    tool_results = state.get("tool_results", {})

    if intent == "chat":
        state["final_response"] = (
            "你好！我是 Power-Agent 电厂智能预警助手。\n"
            "我可以帮您：\n"
            "1. 查询设备运行数据\n"
            "2. 分析设备异常和告警\n"
            "3. 预测参数趋势\n"
            "4. 诊断故障原因并给出建议\n\n"
            "请描述您的问题，例如：\"分析2号机组过去24小时主蒸汽温度异常\""
        )
        return state

    # 构建 Tool 结果摘要
    parts = []

    # 数据查询结果摘要
    if "data_tool" in tool_results:
        data_result = tool_results["data_tool"]
        if "error" not in data_result:
            stats = data_result.get("stats", {})
            parts.append(
                f"**数据查询**\n"
                f"- 设备: {data_result.get('device_id', 'N/A')}\n"
                f"- 参数: {data_result.get('parameter', 'N/A')} ({data_result.get('unit', '')})\n"
                f"- 统计: 最小={stats.get('min', 'N/A')}, "
                f"最大={stats.get('max', 'N/A')}, "
                f"均值={stats.get('avg', 'N/A')}, "
                f"数据点数={stats.get('count', 0)}"
            )

    # 异常检测结果摘要
    if "alarm_tool" in tool_results:
        alarm_result = tool_results["alarm_tool"]
        if "error" not in alarm_result:
            risk = alarm_result.get("risk_score", 0)
            alarms = alarm_result.get("alarms", [])
            parts.append(
                f"**异常检测**\n"
                f"- 风险评分: {risk:.2f}\n"
                f"- 告警数量: {len(alarms)}"
            )
            for i, alarm in enumerate(alarms, 1):
                msg = alarm.get("message", alarm.get("trend_desc", ""))
                parts.append(f"  {i}. [{alarm.get('severity', 'N/A')}] {msg}")

    # RAG 知识检索结果摘要
    if "rag_tool" in tool_results:
        rag_result = tool_results["rag_tool"]
        if isinstance(rag_result, list) and rag_result:
            parts.append("**相关知识**")
            for i, doc in enumerate(rag_result, 1):
                parts.append(
                    f"  {i}. [{doc.get('source', 'N/A')}] "
                    f"(相似度: {doc.get('similarity', 0):.2f})\n"
                    f"     {doc.get('content', '')[:80]}..."
                )

    # 预测结果摘要
    if "predict_tool" in tool_results:
        pred_result = tool_results["predict_tool"]
        if "error" not in pred_result and "predictions" in pred_result:
            parts.append(
                f"**趋势预测**\n"
                f"- 趋势: {pred_result.get('trend', 'N/A')}\n"
                f"- 置信度: {pred_result.get('confidence', 0):.2f}\n"
                f"- 预测点数: {len(pred_result.get('predictions', []))}"
            )

    if parts:
        state["final_response"] = "\n\n".join(parts)
    else:
        state["final_response"] = f"已处理意图 [{intent}]，但未获取到有效数据。"

    return state


# ============================================================
# 条件路由: 判断是否需要执行 Tool
# ============================================================

def should_call_tools(state: AgentState) -> str:
    """
    条件边: chat 意图跳过 Tool 直接回复，其他意图执行 Tool。
    """
    intent = state.get("intent", "chat")
    if intent == "chat":
        return "response_generator"
    return "tool_executor"


# ============================================================
# LangGraph 工作流构建（如果已安装 langgraph）
# ============================================================

def _build_langgraph():
    """使用 LangGraph StateGraph 构建工作流"""
    from langgraph.graph import StateGraph, END

    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("intent_router", intent_router)
    graph.add_node("tool_executor", tool_executor)
    graph.add_node("response_generator", response_generator)

    # 设置入口
    graph.set_entry_point("intent_router")

    # 条件边: intent_router 之后根据意图决定走向
    graph.add_conditional_edges(
        "intent_router",
        should_call_tools,
        {
            "tool_executor": "tool_executor",
            "response_generator": "response_generator",
        },
    )

    # tool_executor 之后必定走向 response_generator
    graph.add_edge("tool_executor", "response_generator")

    # response_generator 之后结束
    graph.add_edge("response_generator", END)

    return graph.compile()


# ============================================================
# 降级工作流（langgraph 未安装时使用）
# ============================================================

class SimpleAgent:
    """
    纯 Python 状态机，接口与 LangGraph compiled graph 一致。
    用于 langgraph 未安装时的降级运行。
    """

    def invoke(self, input_data: dict) -> AgentState:
        state: AgentState = {
            "messages": input_data.get("messages", []),
            "intent": "",
            "params": {},
            "tool_calls": [],
            "tool_results": {},
            "final_response": "",
        }

        # 节点 1: 意图识别
        state = intent_router(state)

        # 条件边: 是否调用 Tool
        route = should_call_tools(state)
        if route == "tool_executor":
            state = tool_executor(state)

        # 节点 3: 生成响应
        state = response_generator(state)

        return state


# ============================================================
# 统一入口: create_agent
# ============================================================

def create_agent():
    """
    创建 Agent 工作流实例。

    优先使用 LangGraph StateGraph（如果已安装），
    否则降级为 SimpleAgent（纯 Python 状态机）。

    Returns:
        具有 .invoke(input_data) 方法的 Agent 实例

    Usage:
        agent = create_agent()
        result = agent.invoke({"messages": ["分析2号机组温度异常"]})
        print(result["intent"])           # "anomaly_detection"
        print(result["final_response"])   # 诊断结果摘要
    """
    try:
        agent = _build_langgraph()
        logger.info("LangGraph StateGraph 工作流已启动")
        return agent
    except ImportError:
        logger.warning("langgraph 未安装，降级为 SimpleAgent")
        return SimpleAgent()
