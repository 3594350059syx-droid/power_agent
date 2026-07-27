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
    device_id = diagnosis.get("device_id", "\u672a\u77e5\u8bbe\u5907")
    risk_score = diagnosis.get("risk_score", 0.0)
    causes = diagnosis.get("causes", ["\u5f85\u5206\u6790"])
    suggestions = diagnosis.get("suggestions", ["\u5f85\u751f\u6210"])

    # 风险等级
    if risk_score >= 0.75:
        risk_level = "\u9ad8\u98ce\u9669"
    elif risk_score >= 0.5:
        risk_level = "\u4e2d\u98ce\u9669"
    else:
        risk_level = "\u4f4e\u98ce\u9669"

    md = f"""# \u8bbe\u5907\u8bca\u65ad\u62a5\u544a

## \u8bbe\u5907\u4fe1\u606f
- \u8bbe\u5907 ID: `{device_id}`
- \u8bca\u65ad\u65f6\u95f4: {diagnosis.get("diagnosis_time", "\u5f85\u586b\u5199")}

## \u98ce\u9669\u8bc4\u4f30
| \u6307\u6807 | \u503c |
|------|------|
| \u98ce\u9669\u8bc4\u5206 | {risk_score:.2f} |
| \u98ce\u9669\u7b49\u7ea7 | {risk_level} |

## \u5f02\u5e38\u539f\u56e0
"""
    for i, cause in enumerate(causes, 1):
        md += f"{i}. {cause}\n"

    md += "\n## \u5904\u7f6e\u5efa\u8bae\n"
    for i, suggestion in enumerate(suggestions, 1):
        md += f"{i}. {suggestion}\n"

    md += f"\n---\n*Power-Agent \u667a\u80fd\u9884\u8b66\u7cfb\u7edf \u81ea\u52a8\u751f\u6210*\n"

    return md
