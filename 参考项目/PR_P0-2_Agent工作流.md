# PR P0-2: LangGraph Agent 状态与工作流

**提交者**：A（队长，系统架构与 Agent 负责人）  
**分支**：`feature/agent-core`（本地实现，待提交）  
**审查人**：A（自审）  
**审查日期**：2026-07-22

---

## 一、背景

P0-2 任务：实现 LangGraph Agent 的状态定义与工作流构建，为后续 P0-3（DeepSeek LLM 对接）和 P0-4（Tool 调用框架）打好基础。本次实现覆盖 12 个文件，包含 AgentState 定义、三节点工作流、Tool 注册中心、4 个 Mock Tool 和系统提示词。

---

## 二、变更摘要

| 维度 | 内容 |
|------|------|
| 新增文件 | 9 个（3 个 `__init__.py` + 6 个功能文件） |
| 覆盖文件 | 3 个（state.py / workflow.py / 4 个 tool 占位 → 实现） |
| 依赖变更 | requirements.txt 解注释 langchain / langgraph / langchain-openai |
| 核心架构 | `intent_router → tool_executor → response_generator` 三节点 StateGraph |
| 降级机制 | langgraph 未安装时自动降级为 SimpleAgent（纯 Python 状态机） |

---

## 三、文件清单

### ✅ 新增文件（9 个）

| 文件 | 行数 | 说明 |
|------|------|------|
| `agent/__init__.py` | 4 | Agent 模块包初始化 |
| `agent/graph/__init__.py` | 1 | graph 子包初始化 |
| `agent/prompts/__init__.py` | 1 | prompts 子包初始化 |
| `agent/tools/base.py` | 108 | Tool 接口规范（B/D 按此签名实现）+ TOOL_REGISTRY + INTENT_TOOL_MAP |
| `agent/tools/__init__.py` | 56 | Tool 注册中心：MOCK_REGISTRY + get_tool() + call_tool() |
| `agent/prompts/system_prompt.py` | 171 | 系统提示词 + 意图关键词映射 + classify_intent() + extract_params() |
| `agent/graph/workflow.py` | 230 | LangGraph StateGraph 三节点工作流 + SimpleAgent 降级 |

### 🔄 从占位替换为实现（4 个）

| 文件 | 原状态 | 现状态 | 说明 |
|------|--------|--------|------|
| `agent/graph/state.py` | 3 行注释占位 | 36 行 | AgentState TypedDict，6 个字段 |
| `agent/tools/data_tool.py` | 3 行注释占位 | 57 行 | Mock：按参数生成时序数据 + 统计摘要 |
| `agent/tools/alarm_tool.py` | 3 行注释占位 | 37 行 | Mock：阈值异常 + 趋势异常告警 |
| `agent/tools/rag_tool.py` | 3 行注释占位 | 38 行 | Mock：3 条电厂知识文档 |
| `agent/tools/report_tool.py` | 3 行注释占位 | 51 行 | Mock：Markdown 格式诊断报告 |

### 📝 依赖更新

| 文件 | 变更 |
|------|------|
| `requirements.txt` | 解注释 langchain>=0.1.0 / langgraph>=0.0.40 / langchain-openai>=0.1.0 |

---

## 四、与 A.md 任务对照

| A.md P0-2 要求 | 达成 | 说明 |
|----------------|------|------|
| 使用 LangGraph StateGraph | ✅ | `_build_langgraph()` 构建 StateGraph，未安装时降级 |
| State 定义：messages, intent, params, tool_calls, final_response | ✅ | AgentState TypedDict，6 个字段（含 tool_results） |
| 节点：intent_router → tool_executor → response_generator | ✅ | 三节点 + 条件边 |
| 条件边：根据 intent 路由到不同 tool 或直接回复 | ✅ | `should_call_tools()`：chat 跳过 tool，其余执行 |
| Tool 节点初期用 mock 返回值 | ✅ | 4 个 mock 全部实现，B/D 到位后替换 |
| Tool 注册中心 | ✅ | `agent/tools/__init__.py`：MOCK_REGISTRY + call_tool() |
| `agent/tools/base.py` 接口规范 | ✅ | 5 个 Tool 签名 + INTENT_TOOL_MAP |

### 验收标准验证

```python
from agent.graph.workflow import create_agent

agent = create_agent()

# 测试 1：诊断类意图
result = agent.invoke({"messages": ["分析2号机组温度异常"]})
assert result["intent"] == "anomaly_detection"           # ✅
assert result["params"]["device_id"] == "generator_002"  # ✅
assert result["params"]["parameter"] == "steam_temp"     # ✅
assert len(result["tool_calls"]) == 2                    # ✅ data_tool + alarm_tool

# 测试 2：闲聊类意图
result = agent.invoke({"messages": ["你好，你是谁"]})
assert result["intent"] == "chat"                        # ✅
assert result["tool_calls"] == []                        # ✅ 跳过 Tool
assert result["final_response"] is not None              # ✅

# 测试 3：诊断意图（含 RAG 检索）
result = agent.invoke({"messages": ["为什么2号锅炉主蒸汽温度会持续升高，给出处理建议"]})
assert result["intent"] == "diagnosis"                   # ✅
assert len(result["tool_calls"]) == 3                    # ✅ data + alarm + rag
```

---

## 五、架构设计

```
用户消息
    │
    ▼
┌─────────────┐
│ intent_router │ ── 关键词规则匹配 → intent + params
└──────┬──────┘
       │
       ▼ should_call_tools()
   ┌───┴───┐
   │       │
 chat    其他意图
   │       │
   │       ▼
   │  ┌──────────────┐
   │  │ tool_executor  │ ── 调用 mock tools（data/alarm/rag/predict）
   │  └──────┬───────┘
   │         │
   └────┬────┘
        ▼
┌─────────────────┐
│ response_generator │ ── 模板拼接最终响应
└─────────────────┘
        │
        ▼
   final_response
```

**降级机制**：`create_agent()` 优先尝试 `from langgraph.graph import StateGraph`，若 ImportError 则返回 `SimpleAgent`（纯 Python 状态机，接口一致）。

---

## 六、Mock Tool 说明

| Tool | Mock 返回内容 | 真实实现替换路径 |
|------|-------------|----------------|
| `data_tool_mock` | 24h 时序数据 + min/max/avg 统计 | `backend/services/data_service.py`（B 实现） |
| `alarm_tool_mock` | 阈值告警 + 趋势告警，risk_score=0.72 | `backend/services/alarm_service.py`（B 实现） |
| `rag_tool_mock` | 3 条电厂规程/案例/维护手册 | `rag/retriever/`（D 实现） |
| `report_tool_mock` | Markdown 诊断报告 | P1-1 阶段 A 实现 |

**替换方式**：在 `agent/tools/__init__.py` 的 `MOCK_REGISTRY` 中将 mock 函数替换为真实导入。

---

## 七、审查结论

| 类别 | 判定 | 说明 |
|------|------|------|
| AgentState 定义 | ✅ 通过 | TypedDict 6 字段，total=False 允许部分更新 |
| 工作流三节点 | ✅ 通过 | intent_router / tool_executor / response_generator 逻辑正确 |
| 条件边路由 | ✅ 通过 | chat 跳过 Tool，其余意图执行对应 Tool |
| Mock Tool | ✅ 通过 | 4 个 mock 返回格式与 base.py 签名一致 |
| Tool 注册中心 | ✅ 通过 | MOCK_REGISTRY + call_tool() 统一管理 |
| 降级机制 | ✅ 通过 | langgraph 未安装时 SimpleAgent 正常工作 |
| 系统提示词 | ✅ 通过 | 角色定位 + 意图关键词 + 参数抽取映射表 |

**总体判定：✅ P0-2 完成，可进入 P0-3（DeepSeek LLM 对接）。**

---

## 八、后续衔接

| 任务 | 说明 | 依赖 |
|------|------|------|
| P0-3 | 将 `classify_intent()` / `extract_params()` 替换为 DeepSeek LLM 调用 | DEEPSEEK_API_KEY |
| P0-4 | 将 MOCK_REGISTRY 替换为 B/D 真实函数 | B 的 data_tool/alarm_tool + D 的 rag_tool |
| P0-5 | 将 `backend/api/agent.py` 的 `_call_deepseek()` 对接 `create_agent()` | P0-3 完成 |
