"""
告警检测 Tool — Mock 实现
P0-2: B 的 alarm_tool 未到位前使用此 mock

B 完成真实实现后，将 workflow 中的 mock 调用替换为:
    from agent.tools.alarm_tool import alarm_tool
"""


def alarm_tool_mock(device_id: str, hours: int = 24) -> dict:
    """
    Mock: 检测设备异常

    生成符合 alarm_tool 签名的模拟返回值，包含阈值异常和趋势异常。
    """
    return {
        "device_id": device_id,
        "risk_score": 0.72,
        "alarms": [
            {
                "type": "threshold",
                "parameter": "steam_temp",
                "current_value": 568.5,
                "threshold": 555.0,
                "severity": "high",
                "triggered_at": "2026-07-10T14:30:00",
                "message": f"{device_id} \u4e3b\u84b8\u6c7d\u6e29\u5ea6\u8d85\u9608\u503c 555\u2103\uff0c\u5f53\u524d 568.5\u2103",
            },
            {
                "type": "trend",
                "parameter": "steam_temp",
                "trend_desc": "\u8fc7\u53bb30\u5206\u949f\u4e3b\u84b8\u6c7d\u6e29\u5ea6\u4e0a\u5347 12.3\u2103",
                "slope": 0.41,
                "severity": "medium",
            },
        ],
    }
