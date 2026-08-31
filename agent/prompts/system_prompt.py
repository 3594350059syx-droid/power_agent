"""
Agent 系统提示词
P0-2: 基础版本（关键词规则匹配）
P0-3: 接入 DeepSeek LLM 意图识别 + 参数抽取，规则匹配作为降级

定义 Agent 的角色定位、可用 Tool 列表、参数抽取模板。
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

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

- device_id: 设备 ID（如 boiler_002 / turbine_003 / generator_004）
- parameter: 参数名（如 steam_temp / steam_pressure / vibration / power）
- time_range_hours: 时间范围（小时，默认 24）
- threshold: 阈值（用户提到的数值阈值，如 550、80 等，无则不填）

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
  2号锅炉   → boiler_002
  2号机组   → boiler_002
  3号汽轮机 → turbine_003
  3号机组   → turbine_003
  4号发电机 → generator_004
  4号机组   → generator_004

请以 JSON 格式返回意图和参数：
{
  "intent": "data_query | anomaly_detection | prediction | diagnosis | chat",
  "params": {
    "device_id": "...",
    "parameter": "...",
    "time_range_hours": 24,
    "threshold": null
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
        "2号锅炉": "boiler_002",
        "2号机组": "boiler_002",
        "3号汽轮机": "turbine_003",
        "3号机组": "turbine_003",
        "4号发电机": "generator_004",
        "4号机组": "generator_004",
    }
    for name, dev_id in device_map.items():
        if name in message:
            params["device_id"] = dev_id
            break

    # 直接传入规范设备 ID 时也保持同一参数契约（报告接口等内部调用会使用此形式）。
    device_id_match = re.search(
        r"\b(?:boiler|turbine|generator)_\d{3}\b", message, re.IGNORECASE
    )
    if device_id_match:
        params["device_id"] = device_id_match.group(0).lower()

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


# ============================================================
# P0-3: LLM 意图识别 + 参数抽取
# ============================================================

# 合法意图集合
_VALID_INTENTS = {"data_query", "anomaly_detection", "prediction", "diagnosis", "chat"}


def parse_llm_response(response_text: str) -> tuple[str, dict]:
    """
    解析 LLM 返回的 JSON 文本，提取 intent 和 params。

    LLM 可能返回纯 JSON、带 markdown 代码块或附带额外说明，
    本函数使用正则提取 JSON 部分，容错性高。

    Returns:
        (intent, params)
    """
    # 尝试直接解析
    text = response_text.strip()

    # 去除 markdown 代码块包裹
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # 尝试提取 JSON 对象（包含 "intent" 字段）
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 正则匹配包含 intent 的 JSON 对象
        match = re.search(r'\{[^{}]*"intent"[^{}]*\}', response_text, re.DOTALL)
        if not match:
            logger.warning(f"LLM 响应无法解析为 JSON: {response_text[:200]}")
            return "chat", {}
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning(f"LLM 响应 JSON 解析失败: {match.group()[:200]}")
            return "chat", {}

    intent = data.get("intent", "chat")
    params = data.get("params", {})

    # 校验意图合法性
    if intent not in _VALID_INTENTS:
        logger.warning(f"LLM 返回未知意图 '{intent}'，降级为 chat")
        intent = "chat"

    # 确保 params 是 dict
    if not isinstance(params, dict):
        params = {}

    # 默认 time_range_hours
    if "time_range_hours" not in params:
        params["time_range_hours"] = 24

    return intent, params


def parse_intent_and_params(message: str) -> tuple[str, dict]:
    """
    P0-3 统一入口: 意图识别 + 参数抽取

    优先使用 DeepSeek LLM（通过 langchain-openai 或 urllib），
    失败时降级为 P0-2 规则匹配（classify_intent + extract_params）。

    降级场景:
    1. DEEPSEEK_API_KEY 未配置 → 规则匹配
    2. API 调用网络错误 → 规则匹配
    3. LLM 返回无法解析 → 规则匹配

    Returns:
        (intent, params)
    """
    from agent.prompts.llm_client import is_llm_available, call_deepseek
    from agent.prompts.intent_examples import build_messages

    if is_llm_available():
        try:
            messages = build_messages(message)
            response = call_deepseek(messages, temperature=0.1, max_tokens=512)
            intent, params = parse_llm_response(response)
            logger.info(f"[LLM] 意图识别成功: intent={intent}, params={params}")
            return intent, params
        except Exception as e:
            logger.warning(f"[LLM] 意图识别失败，降级为规则匹配: {e}")

    # 降级: P0-2 规则匹配
    intent = classify_intent(message)
    params = extract_params(message)
    logger.info(f"[规则] 意图识别: intent={intent}, params={params}")
    return intent, params
