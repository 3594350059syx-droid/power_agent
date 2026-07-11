# A 成员开发任务文档

## 1. 角色定位

**系统架构与 Agent 负责人（队长）**

你是整个项目的技术核心。你负责把 B、C、D 的工作串联成一个完整可运行系统。你需要：
- 设计并实现 Agent 控制流程（LangGraph）
- 搭建 FastAPI 后端服务
- 定义所有 Tool 接口规范（B 和 D 按你的规范实现）
- 对接 DeepSeek LLM API
- 系统最终集成和调试

## 2. MVP 目标

实现以下最小闭环：

```
用户在 C 的前端输入 "分析2号机组过去24小时主蒸汽温度异常"
  → A 的 /api/v1/agent/chat 接收
  → LangGraph Agent 解析意图 → 识别需要调用 data_tool + alarm_tool
  → 调用 B 的 data_tool 查询 TimescaleDB 24 小时温度数据
  → 调用 B 的 alarm_tool 检测异常
  → 调用 DeepSeek 生成诊断结论
  → 返回 JSON 结果给前端展示
```

MVP 验收标准：**自然语言输入 → Agent 自动调用 Tool → 返回包含数据和诊断结果的 JSON → 前端能展示出来**。

## 3. 具体开发任务

---

### P0-1: 初始化 FastAPI 后端项目骨架

**技术方案**：
- 使用 FastAPI + uvicorn
- 统一响应格式：`{"success": bool, "message": str, "data": {}}`
- CORS 中间件（允许前端跨域）
- 所有路由注册在 `backend/main.py`

**涉及目录**：
```
backend/
├── main.py              ← 应用入口
├── config/
│   └── settings.py      ← 配置读取（从 .env）
├── api/
│   ├── __init__.py
│   ├── agent.py         ← Agent 对话接口
│   ├── telemetry.py     ← 数据查询接口
│   ├── alarm.py         ← 告警查询接口
│   └── report.py        ← 报告接口
├── database/
│   ├── __init__.py
│   ├── connection.py    ← PostgreSQL 连接管理
│   └── models.py        ← SQLAlchemy 模型
└── services/
    ├── __init__.py
    └── agent_service.py ← Agent 业务逻辑
```

**输入依赖**：无（基础搭建）

**输出结果**：
- `backend/main.py` 可启动，访问 `http://localhost:8000/docs` 看到 Swagger
- `GET /api/v1/health` 返回 `{"success": true, "message": "ok"}`

**验收标准**：
```bash
cd backend
uvicorn main:app --reload --port 8000
# 浏览器访问 http://localhost:8000/docs 显示 Swagger UI
```

---

### P0-2: 实现 LangGraph Agent 状态与工作流

**技术方案**：
- 使用 LangGraph 的 StateGraph
- State 定义：`messages`, `intent`, `params`, `tool_calls`, `final_response`
- 节点：`intent_router` → `tool_executor` → `response_generator`
- 条件边：根据 intent 路由到不同 tool 或直接回复

**涉及目录**：
```
agent/
├── graph/
│   ├── state.py         ← AgentState TypedDict 定义
│   └── workflow.py      ← LangGraph 工作流构建
├── tools/
│   ├── __init__.py      ← Tool 注册中心
│   ├── base.py          ← Tool 基类/接口定义（给 B、D 参考）
│   ├── data_tool.py     ← 调用 B 的数据查询函数
│   ├── alarm_tool.py    ← 调用 B 的预警函数
│   ├── rag_tool.py      ← 调用 D 的 RAG 检索函数
│   └── report_tool.py   ← 报告生成
└── prompts/
    └── system_prompt.py ← Agent 系统提示词
```

**输入依赖**：
- B 提供 `data_tool(query: dict) -> dict` 函数签名
- B 提供 `alarm_tool(device_id: str, hours: int) -> dict` 函数签名
- D 提供 `rag_tool(query: str, top_k: int) -> list[dict]` 函数签名

**输出结果**：
- `agent/graph/state.py`：定义 AgentState
- `agent/graph/workflow.py`：可独立运行的 LangGraph 工作流
- `agent/tools/base.py`：Tool 接口规范（B 和 D 按此实现）

**验收标准**：
```python
# 在 Python 中运行：
from agent.graph.workflow import create_agent
agent = create_agent()
result = agent.invoke({"messages": ["分析2号机组温度异常"]})
# result 应包含 structured 的 intent 和 params
```

---

### P0-3: 对接 DeepSeek LLM API + 意图识别

**技术方案**：
- 使用 `langchain-openai` 兼容方式调用 DeepSeek API
- System Prompt：角色定位 + 可用 Tool 列表 + 参数抽取模板
- 意图分类：`data_query` | `anomaly_detection` | `prediction` | `diagnosis` | `chat`
- 参数抽取：从自然语言中提取 `device_id`, `parameter`, `time_range`, `threshold`

**涉及目录**：
```
agent/prompts/
├── system_prompt.py     ← Agent 系统提示词
└── intent_examples.py   ← Few-shot 示例
```

**输入依赖**：
- `.env` 中配置 `DEEPSEEK_API_KEY`
- `requirements.txt` 中添加 `langchain`, `langchain-openai`, `langgraph`

**输出结果**：
- LLM 可正确解析 "分析2号机组过去24小时主蒸汽温度异常" 返回：
```json
{
  "intent": "anomaly_detection",
  "params": {
    "device_id": "generator_002",
    "parameter": "steam_temp",
    "time_range_hours": 24
  }
}
```

**验收标准**：
- 10 条测试指令中至少 8 条意图识别正确，参数抽取完整
- 测试指令由 D 提供（`tests/agent/intent_test_cases.json`）

---

### P0-4: 实现 Tool 调用框架 + Agent 主循环

**技术方案**：
- LangGraph tool_node 执行 Tool 调用
- Tool 返回结果注入 State
- 支持多 Tool 并行调用（如同时查数据 + 知识库）
- 错误处理：Tool 调用失败时返回降级响应

**涉及目录**：
```
agent/graph/workflow.py   ← 完善工作流
agent/tools/__init__.py   ← Tool 注册
agent/tools/data_tool.py  ← 对接 B 的函数
agent/tools/alarm_tool.py ← 对接 B 的函数
agent/tools/rag_tool.py   ← 对接 D 的函数
```

**输入依赖**：
- B 的 `data_tool()` 和 `alarm_tool()` 函数可调用（即使是 mock 返回值）
- D 的 `rag_tool()` 函数可调用

**输出结果**：
- Agent 能自动决策调用哪个 Tool
- Tool 调用结果正确注入对话上下文

**验收标准**：
```python
# 模拟 B 和 D 的 tool 函数返回 mock 数据
result = agent.invoke({"messages": ["分析2号机组温度异常"]})
assert "anomaly_detection" in result["tool_calls"]
assert result["final_response"] is not None
```

---

### P0-5: 实现 `/api/v1/agent/chat` 接口

**技术方案**：
- FastAPI POST 接口
- 接收前端用户消息 → 调用 LangGraph Agent → 返回响应
- 支持流式（SSE）和非流式两种模式
- 返回结构包含：响应文本 + 可能的图表数据 + 诊断结果

**涉及目录**：
```
backend/api/agent.py         ← /api/v1/agent/chat 端点
backend/services/agent_service.py  ← Agent 调用封装
```

**输入依赖**：
- Agent 工作流（P0-2, P0-4）已完成
- 前端请求格式已确认：`{"message": str, "mode": "chat"|"diagnose"}`

**输出结果**：
```json
POST /api/v1/agent/chat
Request:  {"message": "分析2号机组温度异常", "mode": "diagnose"}
Response: {
  "success": true,
  "data": {
    "reply": "检测到2号机组主蒸汽温度异常...",
    "chart_data": {"times": [...], "values": [...]},
    "diagnosis": {"risk_score": 0.85, "causes": [...], "suggestions": [...]}
  }
}
```

**验收标准**：
```bash
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "分析2号机组温度异常", "mode": "diagnose"}'
# 返回 200，包含诊断结果
```

---

### P1-1: 实现报告生成 Tool

**技术方案**：
- 基于 LLM 模板生成标准化诊断报告
- 报告包含：设备信息、异常摘要、趋势描述、原因分析、处理建议
- 输出 Markdown 格式，前端渲染

**涉及目录**：
```
agent/tools/report_tool.py      ← 报告生成
agent/prompts/report_prompt.py  ← 报告模板提示词
```

**输入依赖**：Agent 诊断结果（已有 risk_score, causes, suggestions）

**输出结果**：Markdown 格式诊断报告字符串

**验收标准**：Agent 诊断完成后可生成包含设备名、风险评分、建议的结构化报告

---

### P1-2: 系统集成 + 全链路联调

**技术方案**：
- 将 B 的 data/alarm/predict 函数注册为 Agent Tool
- 将 D 的 rag 函数注册为 Agent Tool
- 确保 C 的前端能正确调用所有接口
- 处理跨模块错误

**涉及目录**：
```
agent/tools/__init__.py    ← 所有 Tool 注册
backend/main.py            ← 路由汇总
```

**输入依赖**：B、C、D 全部完成 P0 任务

**输出结果**：全链路可运行：前端输入 → Agent 处理 → 数据查询 → 异常检测 → RAG 检索 → 结果返回前端

**验收标准**：按 `docs/demo_case.md` 中场景 5（全流程智能诊断）完整走通

---

### P2-1: WebSocket 实时推送

**技术方案**：
- FastAPI WebSocket 端点
- 模拟 MQTT 数据推送到前端
- 前端实时更新监控面板

**涉及目录**：`backend/api/telemetry.py`

**输入依赖**：B 的模拟数据生成器可定时产生新数据

**验收标准**：前端监控面板每 3 秒自动刷新一次数据

---

## 4. 开发流程

### 阶段 1：环境准备（Week 1 前两天）
- **做什么**：搭建 Python 虚拟环境，安装依赖，配置 .env
- **沟通对象**：无
- **产出文件**：`requirements.txt`（完整依赖列表）、`.env` 配置

### 阶段 2：接口确认（Week 1 后三天）
- **做什么**：定义所有 Tool 接口规范，与 B、D 确认函数签名；与 C 确认 API 格式
- **沟通对象**：B（数据/预警 tool 签名）、D（RAG tool 签名）、C（API 响应格式）
- **产出文件**：`agent/tools/base.py`（Tool 接口基类）、`docs/api_spec.md` 补充实际接口列表

### 阶段 3：模块开发（Week 2-4）
- **做什么**：实现 FastAPI 后端 → LangGraph Agent → Tool 框架 → LLM 对接
- **沟通对象**：B（对接 data_tool/alarm_tool）、D（对接 rag_tool）
- **产出文件**：所有 backend/* 和 agent/* 下的 .py 文件

### 阶段 4：本地测试（Week 4 末尾）
- **做什么**：使用 D 提供的测试用例验证 Agent 闭环
- **沟通对象**：D（测试用例）
- **产出文件**：测试通过记录

### 阶段 5：提交 GitHub（持续进行）
- **做什么**：每完成一个 P0 任务提交一次 PR
- **沟通对象**：全员 Code Review
- **产出文件**：feature 分支 + PR

### 阶段 6：联调（Week 5-6）
- **做什么**：与 B（Tool 对接）、C（API 对接）、D（RAG 对接）
- **沟通对象**：B、C、D 全员
- **产出文件**：全链路可运行 Demo

---

## 5. 给 B 的接口契约

```python
# agent/tools/base.py —— B 必须按此签名实现

def data_tool(params: dict) -> dict:
    """
    查询设备时序数据
    输入: {
        "device_id": "generator_002",
        "parameter": "steam_temp",
        "start_time": "2026-07-10T00:00:00",
        "end_time": "2026-07-11T00:00:00"
    }
    输出: {
        "device_id": "generator_002",
        "parameter": "steam_temp",
        "unit": "℃",
        "data": [
            {"time": "2026-07-10T00:00:00", "value": 540.5},
            ...
        ]
    }
    """

def alarm_tool(device_id: str, hours: int = 24) -> dict:
    """
    检测设备异常
    输入: device_id="generator_002", hours=24
    输出: {
        "device_id": "generator_002",
        "risk_score": 0.85,
        "alarms": [
            {
                "type": "threshold",
                "parameter": "steam_temp",
                "current_value": 565.0,
                "threshold": 550.0,
                "severity": "high"
            }
        ]
    }
    """

def predict_tool(device_id: str, parameter: str, hours: int = 6) -> dict:
    """
    预测未来趋势
    输入: device_id="generator_002", parameter="steam_temp", hours=6
    输出: {
        "predictions": [
            {"time": "2026-07-11T01:00:00", "value": 545.2},
            ...
        ],
        "trend": "rising",
        "confidence": 0.92
    }
    """
```

## 6. 给 D 的接口契约

```python
# agent/tools/base.py —— D 必须按此签名实现

def rag_tool(query: str, top_k: int = 3) -> list[dict]:
    """
    RAG 知识检索
    输入: query="主蒸汽温度过高原因", top_k=3
    输出: [
        {
            "source": "锅炉运行规程 §3.2",
            "content": "主蒸汽温度过高时，应检查减温水系统...",
            "similarity": 0.94
        },
        ...
    ]
    """
```

## 7. 给 C 的 API 文档

```
POST /api/v1/agent/chat
  功能: Agent 对话
  输入: {"message": "str", "mode": "chat|diagnose"}
  输出: {"success": bool, "data": {"reply": "str", ...}}

GET /api/v1/telemetry/live?device_id=xxx
  功能: 获取设备实时数据
  输出: {"success": bool, "data": {"device_id": "str", "parameters": {...}}}

GET /api/v1/alarm/list?device_id=xxx&hours=24
  功能: 获取告警列表
  输出: {"success": bool, "data": {"alarms": [...]}}

GET /api/v1/report/latest?device_id=xxx
  功能: 获取最新诊断报告
  输出: {"success": bool, "data": {"report": "str (markdown)"}}
```
