"""
AgentState 定义
P0-2: LangGraph Agent 状态与工作流

定义 Agent 在整个工作流中传递的状态对象。
所有节点（intent_router / tool_executor / response_generator）共享此状态。
"""
from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    """
    LangGraph Agent 状态对象

    字段说明:
        messages:         用户消息列表（对话上下文）
        intent:           意图分类结果
                          - data_query:          数据查询
                          - anomaly_detection:   异常检测
                          - prediction:          趋势预测
                          - diagnosis:           故障诊断
                          - chat:                闲聊
        params:           从自然语言中抽取的参数
                          - device_id:           设备 ID
                          - parameter:           参数名 (steam_temp / vibration / ...)
                          - time_range_hours:    时间范围（小时）
        tool_calls:       Tool 调用记录列表
        tool_results:     Tool 返回结果
        final_response:   最终响应文本（返回给前端）
    """
    messages: list[str]
    intent: str
    params: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    tool_results: dict[str, Any]
    final_response: str
