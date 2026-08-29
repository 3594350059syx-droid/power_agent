"""
报告生成 Tool — Mock 实现
P1-1: 正式版由 A 在 P1-1 阶段实现
P0-2: 临时 mock，供 workflow 闭环测试
"""


def report_tool_mock(diagnosis: dict) -> str:
    """
    Mock: 生成诊断报告（Markdown 格式）

    输入: diagnosis={"device_id": "...", "risk_score": 0.85, "causes": [...], "suggestions": [...]}
    输出: Markdown 字符串
    """
    device_id = diagnosis.get("device_id", "未知设备")
    risk_score = diagnosis.get("risk_score", 0.0)
    causes = diagnosis.get("causes", ["待分析"])
    suggestions = diagnosis.get("suggestions", ["待生成"])

    # 风险等级
    if risk_score >= 0.75:
        risk_level = "高风险"
    elif risk_score >= 0.5:
        risk_level = "中风险"
    else:
        risk_level = "低风险"

    md = f"""# 设备诊断报告

## 设备信息
- 设备 ID: `{device_id}`
- 诊断时间: {diagnosis.get("diagnosis_time", "待填写")}

## 风险评估
| 指标 | 值 |
|------|------|
| 风险评分 | {risk_score:.2f} |
| 风险等级 | {risk_level} |

## 异常原因
"""
    for i, cause in enumerate(causes, 1):
        md += f"{i}. {cause}\n"

    md += "\n## 处置建议\n"
    for i, suggestion in enumerate(suggestions, 1):
        md += f"{i}. {suggestion}\n"

    md += f"\n---\n*Power-Agent 智能预警系统 自动生成*\n"

    return md
