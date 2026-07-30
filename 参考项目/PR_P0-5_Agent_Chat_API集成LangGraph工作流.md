# PR P0-5: Agent Chat API 集成 LangGraph 工作流

**提交者**：A（队长，系统架构与 Agent 负责人）  
**分支**：本地实现（A-P0-5）  
**审查人**：A（自审）  
**审查日期**：2026-07-12

---

## 一、背景

P0-5 是 A 在 MVP 阶段的最后一个 P0 任务。此前 P0-2/P0-3/P0-4 已完成 Agent 工作流（LangGraph StateGraph）、LLM 意图识别（DeepSeek API）、Tool 调用框架（real + mock 降级），但 `/api/v1/agent/chat` 端点仍直接调用 DeepSeek API 做简单对话，未串联 LangGraph Agent 工作流。

**现状问题**：
```
旧：用户消息 → DeepSeek API → 简单对话回复
新：用户消息 → LangGraph Agent → intent_router → tool_executor → 
    response_generator → LLM 增强 → 结构化响应（reply + chart_data + diagnosis）
```

本次变更：创建 Agent 服务层，重构 API 端点，对接 D 的 RAG 真实实现，实现意图→Tool→LLM 全链路闭环。

---

## 二、变更摘要

| 维度 | 内容 |
|------|------|
| 新增文件 | 1 个（`backend/services/agent_service.py`, 251 行） |
| 重构文件 | 2 个（`backend/api/agent.py` 从 -88 行到 +55 行, `agent/tools/__init__.py` 新增 RAG 真实导入） |
| 架构升级 | Agent 工作流全链路闭环 + LLM 诊断回复增强 + RAG mock→真实对接 |
| 验证结果 | P0-2 回归 73/73 + P0-3 意图识别 10/10 + P0-5 端到端 2/2，全部通过 |

---

## 三、文件清单

### 新增文件（1 个）

| 文件 | 行数 | 说明 |
|------|------|------|
| `backend/services/agent_service.py` | 251 | Agent 服务层：封装 LangGraph Agent，提取结构化数据，LLM 增强回复 |

### 重构文件（2 个）

| 文件 | 变更 | 说明 |
|------|------|------|
| `backend/api/agent.py` | -88 / +55 | 移除直接 DeepSeek 调用逻辑，改为调用 `agent_service.run_agent()` |
| `agent/tools/__init__.py` | +11 / -4 | 新增 D 的 RAG 真实 import（try/except 自动降级 mock） |

---

## 四、架构设计

### 4.1 全链路调用流程

```
POST /api/v1/agent/chat
  │
  ▼
backend/api/agent.py          ← API 层：接收请求，返回统一响应
  │
  ▼
backend/services/agent_service.py  ← 服务层：编排 Agent 工作流
  │
  ├─1. create_agent()               ← 创建 Agent 单例（LangGraph/SimpleAgent 降级）
  ├─2. agent.invoke({"messages": [...]})  ← 运行工作流
  │     ├─ intent_router:      解析意图 + 抽取参数（DeepSeek LLM / 规则降级）
  │     ├─ tool_executor:      调用 Tool（数据库 / mock 降级）
  │     └─ response_generator: 模板拼接响应
  ├─3. _extract_chart_data()   ← 从 data_tool 结果提取 chart_data
  ├─4. _extract_diagnosis()    ← 从 alarm_tool 结果提取 diagnosis
  └─5. _enhance_with_llm()     ← 用 DeepSeek 生成自然语言诊断回复
  │
  ▼
返回 {reply, intent, mode, chart_data, diagnosis, tool_calls}
```

### 4.2 AgentService 核心函数

```python
def run_agent(message: str, mode: str = "chat") -> dict:
    """
    核心入口：运行 Agent 工作流，返回结构化响应。
    
    返回结构：
        {
            "reply": str,              # LLM 增强的自然语言回复
            "intent": str,             # 识别的意图
            "mode": str,               # 对话模式
            "chart_data": dict | None, # ECharts 图表数据
            "diagnosis": dict | None,  # 诊断结果（风险评分/告警/知识引用）
            "tool_calls": list,        # Tool 调用记录
        }
    """
```

### 4.3 LLM 增强机制

当 DeepSeek API Key 已配置时，Agent 会将 Tool 返回的结构化结果（数据查询、异常检测、RAG 知识）拼接为上下文，通过专用 System Prompt 指示 LLM 生成专业诊断回复：

```
System Prompt（诊断增强）:
  你是 Power-Agent 电厂智能预警与故障诊断助手...
  请根据工具返回的结果，生成一段专业、简洁的中文诊断回复。
  回复应包含：设备状态概述 / 异常发现 / 风险评估 / 处置建议

User Prompt（上下文）:
  用户问题: 分析2号锅炉过去24小时主蒸汽温度异常
  识别意图: anomaly_detection
  [data_tool 返回结果]
  [alarm_tool 返回结果]
```

LLM 不可用时降级为模板拼接回复，不影响系统可用性。

### 4.4 结构化数据提取

**chart_data**（供前端 ECharts 渲染趋势图）：
```json
{
  "device_id": "boiler_002",
  "parameter": "steam_temp",
  "unit": "℃",
  "times": ["2026-07-10T00:00:00", ...],
  "values": [540.5, ...],
  "stats": {"min": 535.0, "max": 575.0, "avg": 548.3, "count": 1440}
}
```

**diagnosis**（供前端诊断卡片展示）：
```json
{
  "device_id": "boiler_002",
  "risk_score": 0.72,
  "risk_level": "medium",
  "alarm_count": 2,
  "alarms": [...],
  "knowledge_refs": [{"source": "锅炉运行规程 §3.2", "similarity": 0.94}],
  "trend_info": {"trend": "rising", "confidence": 0.92}
}
```

---

## 五、RAG 真实实现对接

D 的 RAG 模块（15 篇知识文档 → FAISS 索引 → `rag/rag_tool.py`）已完成 P0-4。之前 `agent/tools/__init__.py` 中 rag_tool 固定使用 mock 版本。本次将 RAG 集成到 real + mock 自动降级机制中：

```python
# agent/tools/__init__.py
# D 的真实实现（依赖 faiss + sentence-transformers）
try:
    from rag.rag_tool import rag_tool as _real_rag_tool
    _REAL_REGISTRY["rag_tool"] = _real_rag_tool
except Exception as e:
    logger.warning(f"D 的真实 RAG Tool 不可用，降级为 mock: {e}")

ACTIVE_REGISTRY = {
    ...
    "rag_tool": _REAL_REGISTRY.get("rag_tool", rag_tool_mock),
    ...
}
```

当 `faiss` + `sentence-transformers` 已安装且 FAISS 索引文件存在时，Agent 自动使用真实 RAG 检索返回知识片段，为 LLM 诊断提供专业依据。

---

## 六、降级机制总结

| 组件 | 正常路径 | 降级路径 | 触发条件 |
|------|---------|---------|---------|
| Agent 工作流 | LangGraph StateGraph | SimpleAgent（纯 Python 状态机） | langgraph 未安装 |
| 意图识别 | DeepSeek LLM | 规则匹配（关键词） | API Key 未配置 / 调用失败 |
| data_tool | 查询 TimescaleDB | Mock 随机数据 | sqlalchemy 未安装 / DB 不可用 |
| alarm_tool | 异常检测算法 | Mock 预设告警 | 同上 |
| rag_tool | FAISS 检索 | Mock 模板知识 | faiss 未安装 / 索引文件缺失 |
| 诊断回复 | DeepSeek 自然语言 | 模板拼接 | LLM 增强失败 |

---

## 七、验证结果

### 7.1 P0-2 基础工作流回归

```
Results: 73/73 passed, 0/73 failed — ALL CHECKS PASSED
```

覆盖：模块导入、AgentState 结构、Tool 注册中心、Mock 返回值、意图分类、参数抽取、完整工作流、INTENT_TOOL_MAP、降级机制、边界情况。

### 7.2 P0-3 意图识别

```
10/10 通过 (100%) — 验收标准: >= 80% (PASS)
```

覆盖：5 种意图分类 × 10 条测试用例。

### 7.3 P0-5 端到端测试

**Test 1: Chat**（简单对话）
```
输入: "你好"
→ intent: chat
→ reply: "你好！我是 Power-Agent 电厂智能预警助手..."
→ chart_data: None, diagnosis: None
→ tool_calls: []（chat 意图跳过 Tool）
✅ PASS
```

**Test 2: 异常检测**（全链路）
```
输入: "分析2号锅炉过去24小时主蒸汽温度异常"  mode=diagnose
→ intent: anomaly_detection
→ data_tool 调用成功（24 条数据点）
→ alarm_tool 调用成功（risk_score=0.72, alarm_count=2）
→ chart_data: {device_id: "boiler_002", parameter: "steam_temp", ...}
→ diagnosis: {risk_score: 0.72, risk_level: "medium", alarm_count: 2}
→ reply: "2号锅炉过去24小时主蒸汽温度运行状态存在异常。
         数据显示温度波动较大，最低为525.52℃，最高达552.98℃，
         平均值为542.3℃。异常发现：系统检测到主蒸汽温度曾超过
         555℃阈值，最高达到568.5℃，属于高风险事件；同时过去
         30分钟内温度上升了12.3℃，呈快速上升趋势..."
         ← DeepSeek LLM 增强生成 ✅
✅ PASS
```

---

## 八、审查结论

| 评估维度 | 结果 |
|---------|------|
| 代码质量 | ✅ AgentService 职责清晰（创建→调用→提取→增强），降级链完整 |
| 接口契约 | ✅ 请求/响应格式与 P0-5 规范一致，兼容前端 Chat 组件 |
| 降级机制 | ✅ 6 层降级全覆盖（工作流/意图/Tool×3/回复），零依赖不崩溃 |
| 测试覆盖 | ✅ P0-2 73/73 + P0-3 10/10 + P0-5 2/2，回归无遗漏 |
| RAG 集成 | ✅ D 的真实 rag_tool 已对接，与 data/alarm 共享同一降级模式 |

---

## 九、后续衔接

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 🔴 **P0** | C-P0-2 前端 AI 对话窗口 | Chat.vue 当前仅占位，需对接 `/api/v1/agent/chat` 返回的 reply + chart_data + diagnosis |
| 🔴 **P0** | C-P0-3 前端实时监控面板 | Monitor.vue 需升级为 3 设备卡片布局 |
| 🟡 **P1** | 数据库部署 + 真实 Tool 联调 | `docker-compose up -d` → 初始化数据 → ACTIVE_REGISTRY 自动切换到真实实现 |
| 🟡 **P1** | A-P1-1 报告生成 Tool | 基于 LLM 模板生成 Markdown 诊断报告 |
| 🟡 **P1** | B-P1-1 预测模型 | Prophet 时序预测，替换 predict_tool mock |

---

*Power-Agent 智能预警系统 — A 的 P0 任务全部完成 ✅*
