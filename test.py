"""
P0-2 Agent 工作流 自动化验证测试
用法: python _test_p02.py
"""
import sys

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}  --  {detail}")


# ============================================================
# 1. 模块导入
# ============================================================
print("=" * 60)
print("1. 模块导入")
print("=" * 60)

try:
    from agent.graph.state import AgentState
    check("import AgentState", True)
except Exception as e:
    check("import AgentState", False, str(e))

try:
    from agent.graph.workflow import create_agent
    check("import create_agent", True)
except Exception as e:
    check("import create_agent", False, str(e))

try:
    from agent.tools import MOCK_REGISTRY, get_tool, call_tool
    check("import MOCK_REGISTRY / get_tool / call_tool", True)
except Exception as e:
    check("import MOCK_REGISTRY", False, str(e))

try:
    from agent.tools.base import TOOL_REGISTRY, INTENT_TOOL_MAP
    check("import INTENT_TOOL_MAP", True)
except Exception as e:
    check("import INTENT_TOOL_MAP", False, str(e))

try:
    from agent.prompts.system_prompt import (
        classify_intent, extract_params, INTENT_KEYWORDS
    )
    check("import classify_intent / extract_params", True)
except Exception as e:
    check("import classify_intent", False, str(e))


# ============================================================
# 2. AgentState 结构
# ============================================================
print("\n" + "=" * 60)
print("2. AgentState 结构")
print("=" * 60)

for f in ["messages", "intent", "params", "tool_calls", "tool_results", "final_response"]:
    check(f"has '{f}'", f in AgentState.__annotations__)


# ============================================================
# 3. Tool 注册中心
# ============================================================
print("\n" + "=" * 60)
print("3. Tool 注册中心")
print("=" * 60)

for t in ["data_tool", "alarm_tool", "predict_tool", "rag_tool", "report_tool"]:
    check(f"MOCK_REGISTRY has '{t}'", t in MOCK_REGISTRY)
    check(f"get_tool('{t}') is callable", callable(get_tool(t)))


# ============================================================
# 4. Mock Tool 返回值格式
# ============================================================
print("\n" + "=" * 60)
print("4. Mock Tool 返回值格式")
print("=" * 60)

# data_tool
r = call_tool("data_tool", params={
    "device_id": "boiler_002", "parameter": "steam_temp", "time_range_hours": 24
})
check("data_tool has 'data' list, len=24",
      isinstance(r.get("data"), list) and len(r["data"]) == 24)
check("data_tool has stats(min/max/avg/count)",
      all(k in r.get("stats", {}) for k in ["min", "max", "avg", "count"]))

# alarm_tool
r = call_tool("alarm_tool", device_id="boiler_002", hours=24)
check("alarm_tool risk_score in [0,1]",
      0 <= r.get("risk_score", -1) <= 1)
check("alarm_tool alarms >= 1",
      len(r.get("alarms", [])) >= 1)

# rag_tool
r = call_tool("rag_tool", query="test", top_k=3)
check("rag_tool returns list", isinstance(r, list))
check("rag_tool <= 3 items", len(r) <= 3)
if r:
    check("rag_tool item has source/content/similarity",
          all(k in r[0] for k in ["source", "content", "similarity"]))

# report_tool
r = call_tool("report_tool", diagnosis={
    "device_id": "g2", "risk_score": 0.85,
    "causes": ["原因A"], "suggestions": ["建议A"]
})
check("report_tool returns str", isinstance(r, str))
check("report_tool contains keyword", "\u8bca\u65ad\u62a5\u544a" in r)


# ============================================================
# 5. 意图分类（10 条测试）
# ============================================================
print("\n" + "=" * 60)
print("5. 意图分类")
print("=" * 60)

test_cases = [
    ("\u5206\u6790\u0032\u53f7\u673a\u7ec4\u6e29\u5ea6\u5f02\u5e38", "anomaly_detection"),
    ("\u67e5\u770b\u0034\u53f7\u53d1\u7535\u673a\u529f\u7387\u6570\u636e", "data_query"),
    ("\u9884\u6d4b\u0032\u53f7\u9505\u7089\u672a\u676d\u6e29\u5ea6\u8d8b\u52bf", "prediction"),
    ("\u4e3a\u4ec0\u4e48\u0033\u53f7\u6c7d\u8f6e\u673a\u632f\u52a8\u504f\u9ad8\uff0c\u600e\u4e48\u5904\u7406", "diagnosis"),
    ("\u4f60\u597d\uff0c\u4f60\u662f\u8c01", "chat"),
    ("\u8bca\u65ad\u0032\u53f7\u9505\u7089\u6545\u969c\u539f\u56e0", "diagnosis"),
    ("\u0032\u53f7\u9505\u7089\u4e3b\u84b8\u6c7d\u6e29\u5ea6\u8d85\u8fc7550\u2103\uff0c\u8bf7\u5206\u6790", "anomaly_detection"),
    ("\u663e\u793a\u0033\u53f7\u6c7d\u8f6e\u673a\u7684\u5f53\u524d\u8f6c\u901f", "data_query"),
    ("\u4eca\u5929\u5929\u6c14\u600e\u4e48\u6837", "chat"),
    ("\u0034\u53f7\u53d1\u7535\u673a\u5b9a\u5b50\u6e29\u5ea6\u5f02\u5e38\uff0c\u8bf7\u7ed9\u51fa\u5904\u7406\u5efa\u8bae", "diagnosis"),
]

for msg, expected in test_cases:
    result = classify_intent(msg)
    check(f"'{msg[:20]}...' -> {expected}", result == expected,
          f"got '{result}'")


# ============================================================
# 6. 参数抽取
# ============================================================
print("\n" + "=" * 60)
print("6. 参数抽取")
print("=" * 60)

r = extract_params("\u5206\u6790\u0032\u53f7\u673a\u7ec4\u4e3b\u84b8\u6c7d\u6e29\u5ea6\u8fc7\u53bb\u0032\u0034\u5c0f\u65f6\u5f02\u5e38")
check("boiler2 + steam_temp + 24h",
      r.get("device_id") == "boiler_002"
      and r.get("parameter") == "steam_temp"
      and r.get("time_range_hours") == 24,
      str(r))

r = extract_params("\u67e5\u770b\u0033\u53f7\u6c7d\u8f6e\u673a\u632f\u52a8\u4e00\u5468\u8bb0\u5f55")
check("turb3 + vibration + 168h",
      r.get("device_id") == "turbine_003"
      and r.get("parameter") == "vibration"
      and r.get("time_range_hours") == 168,
      str(r))

r = extract_params("\u0034\u53f7\u53d1\u7535\u673a\u529f\u7387\u0034\u0038\u5c0f\u65f6\u53d8\u5316")
check("gen4 + power + 48h",
      r.get("device_id") == "generator_004"
      and r.get("parameter") == "power"
      and r.get("time_range_hours") == 48,
      str(r))

r = extract_params("\u5206\u6790\u0032\u53f7\u9505\u7089\u7089\u819b\u6e29\u5ea6\u6700\u8fd112\u5c0f\u65f6")
check("furnace_temp + 12h",
      r.get("parameter") == "furnace_temp"
      and r.get("time_range_hours") == 12,
      str(r))


# ============================================================
# 7. 完整工作流（5 种意图全覆盖）
# ============================================================
print("\n" + "=" * 60)
print("7. 完整工作流 (create_agent + invoke)")
print("=" * 60)

agent = create_agent()

# 诊断类
r = agent.invoke({"messages": ["\u5206\u6790\u0032\u53f7\u673a\u7ec4\u6e29\u5ea6\u5f02\u5e38"]})
check("anomaly_detection intent", r["intent"] == "anomaly_detection", r.get("intent"))
check("2 tools (data+alarm)", len(r["tool_calls"]) == 2, str(len(r["tool_calls"])))
check("has final_response", bool(r.get("final_response")))

# 闲聊
r = agent.invoke({"messages": ["\u4f60\u597d\uff0c\u4f60\u662f\u8c01"]})
check("chat intent", r["intent"] == "chat", r.get("intent"))
check("0 tools (skip)", len(r["tool_calls"]) == 0)
check("has greeting response", bool(r.get("final_response")))

# 诊断（含 RAG）
r = agent.invoke({"messages": ["\u4e3a\u4ec0\u4e48\u0032\u53f7\u9505\u7089\u4e3b\u84b8\u6c7d\u6e29\u5ea6\u6301\u7eed\u5347\u9ad8\uff0c\u7ed9\u51fa\u5904\u7406\u5efa\u8bae"]})
check("diagnosis intent", r["intent"] == "diagnosis", r.get("intent"))
check("4 tools (data+alarm+predict+rag)", len(r["tool_calls"]) == 4, str(len(r["tool_calls"])))

# 数据查询
r = agent.invoke({"messages": ["\u67e5\u8be2\u0034\u53f7\u53d1\u7535\u673a\u8fc7\u53bb\u0032\u0034\u5c0f\u65f6\u7684\u529f\u7387\u6570\u636e"]})
check("data_query intent", r["intent"] == "data_query", r.get("intent"))
check("1 tool (data only)", len(r["tool_calls"]) == 1)

# 预测
r = agent.invoke({"messages": ["\u9884\u6d4b\u0032\u53f7\u9505\u7089\u672a\u676d\u0036\u5c0f\u65f6\u6e29\u5ea6\u8d8b\u52bf"]})
check("prediction intent", r["intent"] == "prediction", r.get("intent"))
check("2 tools (data+predict)", len(r["tool_calls"]) == 2, str(len(r["tool_calls"])))


# ============================================================
# 8. INTENT_TOOL_MAP 完整性
# ============================================================
print("\n" + "=" * 60)
print("8. INTENT_TOOL_MAP 完整性")
print("=" * 60)

for intent in ["data_query", "anomaly_detection", "prediction", "diagnosis", "chat"]:
    check(f"has '{intent}'", intent in INTENT_TOOL_MAP)

for intent, tools in INTENT_TOOL_MAP.items():
    for t in tools:
        check(f"tool '{t}' for '{intent}' in MOCK_REGISTRY", t in MOCK_REGISTRY)


# ============================================================
# 9. 降级机制
# ============================================================
print("\n" + "=" * 60)
print("9. 降级机制")
print("=" * 60)

agent_type = type(agent).__name__
check("SimpleAgent fallback working", agent_type == "SimpleAgent", f"got '{agent_type}'")


# ============================================================
# 10. 边界情况
# ============================================================
print("\n" + "=" * 60)
print("10. 边界情况")
print("=" * 60)

r = agent.invoke({"messages": [""]})
check("empty message -> chat", r["intent"] == "chat", r.get("intent"))

check("unknown tool returns None", get_tool("nonexistent") is None)

try:
    call_tool("nonexistent")
    check("call unknown tool raises ValueError", False)
except ValueError:
    check("call unknown tool raises ValueError", True)
except Exception as e:
    check("call unknown tool raises ValueError", False, str(type(e).__name__))


# ============================================================
# 汇总
# ============================================================
print("\n" + "=" * 60)
total = passed + failed
print(f"Results: {passed}/{total} passed, {failed}/{total} failed")
if failed == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"{failed} check(s) FAILED. Review [FAIL] items above.")
    sys.exit(1)