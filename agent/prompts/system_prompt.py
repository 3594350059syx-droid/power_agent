"""
Agent 系统提示词
P0-2: 基础版本，P0-3 将接入 DeepSeek LLM 使用此提示词

定义 Agent 的角色定位、可用 Tool 列表、参数抽取模板。
"""
from agent.tools.base import INTENT_TOOL_MAP


# ---------- Agent 角色定位 ----------
SYSTEM_PROMPT = """\
你是 Power-Agent，一个电厂智能预警与故障诊断助手。

你的职责是：
1. 分析用户提供的设备参数和运行状态
2. 判断是否存在异常或潜在风险
3. 给出专业的诊断建议和处置方案
4. 引用电厂运行规程中的相关知识

请用中文回答，专业、简洁。如果用户提供的是具体设备参数，
请给出「风险评分 / 异常类型 / 处置建议」三段式诊断结果。
"""


# ---------- 意图分类说明 ----------
INTENT_DESCRIPTIONS = """\
可用意图分类及对应 Tool:

| 意图 (intent)        | 说明               | 调用的 Tool                    |
|----------------------|-------------------|-------------------------------|
| data_query           | 查询设备历史数据    | data_tool                     |
| anomaly_detection    | 异常检测分析        | data_tool + alarm_tool        |
| prediction           | 趋势预测           | data_tool + predict_tool      |
| diagnosis            | 故障诊断           | data_tool + alarm_tool + rag_tool |
| chat                 | 闲聊/通用问答      | 无（直接回复）                  |
"""


# ---------- 参数抽取模板 ----------
PARAM_EXTRACTION_TEMPLATE = """\
请从用户消息中提取以下参数（如果存在）：

- device_id: 设备 ID（如 generator_002 / turbine_003 / generator_004）
- parameter: 参数名（如 steam_temp / steam_pressure / vibration / power）
- time_range_hours: 时间范围（小时，默认 24）

参数名映射表：
  主蒸汽温度 → steam_temp
  主蒸汽压力 → steam_pressure
  炉膛温度   → furnace_temp
  转速       → rpm
  轴承温度   → bearing_temp
  振动       → vibration
  有功功率   → power
  定子温度   → stator_temp

设备名映射表：
  2号锅炉   → generator_002
  3号汽轮机 → turbine_003
  4号发电机 → generator_004

请以 JSON 格式返回意图和参数：
{
  "intent": "data_query | anomaly_detection | prediction | diagnosis | chat",
  "params": {
    "device_id": "...",
    "parameter": "...",
    "time_range_hours": 24
  }
}
"""


# ---------- 意图关键词映射（P0-2 规则匹配用） ----------
INTENT_KEYWORDS = {
    "anomaly_detection": [
        "异常", "报警", "告警", "超过", "超标", "偏高", "偏低",
        "故障", "问题", "风险", "检测", "分析",
    ],
    "diagnosis": [
        "诊断", "原因", "为什么", "怎么回事", "怎么办",
        "建议", "处理", "维修", "排查",
    ],
    "prediction": [
        "预测", "趋势", "未来", "将会", "走势", "预估",
    ],
    "data_query": [
        "查询", "查看", "数据", "历史", "记录", "当前",
        "多少", "是什么", "显示",
    ],
}


def classify_intent(message: str) -> str:
    """
    P0-2: 基于关键词的意图分类（规则匹配）

    P0-3 将替换为 DeepSeek LLM 意图识别。
    匹配优先级: diagnosis > anomaly_detection > prediction > data_query > chat
    （"诊断/为什么/怎么处理" 优先于单纯的"异常/故障"检测）
    """
    msg_lower = message.lower()

    for intent in ["diagnosis", "anomaly_detection", "prediction", "data_query"]:
        keywords = INTENT_KEYWORDS.get(intent, [])
        for kw in keywords:
            if kw in msg_lower:
                return intent

    return "chat"


def extract_params(message: str) -> dict:
    """
    P0-2: 基于关键词的参数抽取（规则匹配）

    P0-3 将替换为 DeepSeek LLM 参数抽取。
    """
    params = {}
    msg_lower = message.lower()

    # 设备 ID
    device_map = {
        "2号锅炉": "generator_002",
        "2号机组": "generator_002",
        "3号汽轮机": "turbine_003",
        "3号机组": "turbine_003",
        "4号发电机": "generator_004",
        "4号机组": "generator_004",
    }
    for name, dev_id in device_map.items():
        if name in message:
            params["device_id"] = dev_id
            break

    # 参数名（长词在前，短词在后，避免"温度"吞掉"炉膛温度"）
    param_map = {
        "主蒸汽温度": "steam_temp",
        "炉膛温度": "furnace_temp",
        "蒸汽温度": "steam_temp",
        "轴承温度": "bearing_temp",
        "定子温度": "stator_temp",
        "主蒸汽压力": "steam_pressure",
        "温度": "steam_temp",
        "压力": "steam_pressure",
        "转速": "rpm",
        "振动": "vibration",
        "功率": "power",
    }
    for name, param in param_map.items():
        if name in message:
            params["parameter"] = param
            break

    # 时间范围
    time_keywords = {
        "24小时": 24, "过去一天": 24, "一天": 24,
        "48小时": 48, "两天": 48,
        "72小时": 72, "三天": 72,
        "一周": 168, "7天": 168, "过去7天": 168,
        "12小时": 12, "6小时": 6,
    }
    for kw, hours in time_keywords.items():
        if kw in message:
            params["time_range_hours"] = hours
            break

    if "time_range_hours" not in params:
        params["time_range_hours"] = 24  # 默认 24 小时

    return params
