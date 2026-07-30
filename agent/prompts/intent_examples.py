"""
Few-shot 示例 — LLM 意图识别 + 参数抽取

为 DeepSeek LLM 提供 6 条标注示例，覆盖全部 5 种意图。
LLM 调用时作为 few-shot context 注入 messages。
"""
from agent.prompts.system_prompt import SYSTEM_PROMPT, INTENT_DESCRIPTIONS, PARAM_EXTRACTION_TEMPLATE


# ---------- 完整 System Prompt（角色 + 意图表 + 参数模板） ----------
INTENT_SYSTEM_PROMPT = (
    SYSTEM_PROMPT
    + "\n\n"
    + INTENT_DESCRIPTIONS
    + "\n\n"
    + PARAM_EXTRACTION_TEMPLATE
    + "\n\n"
    "请严格按照上述 JSON 格式返回结果，不要添加额外解释。"
)


# ---------- Few-shot 示例 ----------
# 每条示例: {"message": 用户输入, "intent": 期望意图, "params": 期望参数}
FEW_SHOT_EXAMPLES = [
    {
        "message": "分析2号机组过去24小时主蒸汽温度异常",
        "intent": "anomaly_detection",
        "params": {
            "device_id": "boiler_002",
            "parameter": "steam_temp",
            "time_range_hours": 24,
        },
    },
    {
        "message": "查看4号发电机过去48小时的功率数据",
        "intent": "data_query",
        "params": {
            "device_id": "generator_004",
            "parameter": "power",
            "time_range_hours": 48,
        },
    },
    {
        "message": "预测2号锅炉未来6小时主蒸汽温度趋势",
        "intent": "prediction",
        "params": {
            "device_id": "boiler_002",
            "parameter": "steam_temp",
            "time_range_hours": 6,
        },
    },
    {
        "message": "为什么3号汽轮机振动持续偏高，怎么处理",
        "intent": "diagnosis",
        "params": {
            "device_id": "turbine_003",
            "parameter": "vibration",
            "time_range_hours": 24,
        },
    },
    {
        "message": "你好，你是谁",
        "intent": "chat",
        "params": {},
    },
    {
        "message": "2号锅炉炉膛温度最近12小时有异常，请给出处理建议",
        "intent": "diagnosis",
        "params": {
            "device_id": "boiler_002",
            "parameter": "furnace_temp",
            "time_range_hours": 12,
        },
    },
]


def build_messages(user_message: str) -> list[dict]:
    """
    构建 LLM 消息列表: system + few-shot examples + user message

    Returns:
        [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}, ...]
    """
    import json

    messages = [{"role": "system", "content": INTENT_SYSTEM_PROMPT}]

    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example["message"]})
        messages.append({
            "role": "assistant",
            "content": json.dumps(
                {"intent": example["intent"], "params": example["params"]},
                ensure_ascii=False,
            ),
        })

    messages.append({"role": "user", "content": user_message})
    return messages
