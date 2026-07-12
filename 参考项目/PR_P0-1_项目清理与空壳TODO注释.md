## 修改内容

完成 Day 1 项目清理工作——

1. **`.gitignore`**：新增 `.qoder/` 排除规则，避免 IDE 工具生成内容污染仓库
2. **`docs/api_spec.md`**：清理合并冲突残留（内容重复两份 → 去重为一份），第 5 节接口列表从空表填充为 5 行实际接口（health / agent/chat / telemetry/live / alarm/list / report/latest），每行含 Method、URL、功能描述、负责人、当前状态
3. **全部 14 个空壳文件**：新增标准化 TODO 注释，每个文件包含 P0 任务编号、预期交付周、前置依赖、当前阶段说明，将"无约束占位"升级为"有时间承诺的预留位"

---

## 影响模块

### 修改文件

| 文件 | 变更 |
|------|------|
| `.gitignore` | 新增 `.qoder/` 一行 |
| `docs/api_spec.md` | 清理合并冲突 → 填充接口列表（第 5 节） |

### 空壳文件新增 TODO 注释（14 个）

| 文件 | P0 任务 | 预期周 | 前置依赖 |
|------|---------|--------|---------|
| `agent/graph/state.py` | P0-2 | Week 2-3 | agent/chat mock 已跑通 + DeepSeek API |
| `agent/graph/workflow.py` | P0-2 | Week 2-3 | state.py 完成 + DeepSeek API |
| `agent/tools/data_tool.py` | P0-4 | Week 3 | B 的 data_service.py |
| `agent/tools/alarm_tool.py` | P0-4 | Week 3 | B 的 alarm_service.py |
| `agent/tools/rag_tool.py` | P0-4 | Week 3 | D 的 rag/rag_tool.py |
| `agent/tools/report_tool.py` | P1-1 | Week 5 | Agent 诊断结果 |
| `backend/api/agent.py` | P0-5 | Week 2 | DeepSeek API（.env） |
| `backend/api/alarm.py` | P0-4 | Week 3 | B 的 alarm_tool() |
| `backend/api/report.py` | P1-1 | Week 5 | Agent 诊断流程 + 报告 Tool |
| `backend/api/telemetry.py` | P0-3 | Week 3 | B 的 data_tool() |
| `backend/services/data_service.py` | P0-3 | Week 3 | models.py + PostgreSQL |
| `backend/services/alarm_service.py` | P0-4 | Week 3 | B 的 anomaly_detection 算法 |
| `backend/services/report_service.py` | P1-1 | Week 5 | Agent 诊断结果 + LLM Prompt |
| `backend/database/models.py` | P0-1 | Week 2 | B 的 init.sql |
| `backend/database/init.sql` | P0-1 | Week 2 | PostgreSQL + TimescaleDB |

---

## 测试结果

### 1. `.gitignore` 验证

```bash
git status
# .qoder/ 目录不再出现在未跟踪文件列表中 ✅
```

### 2. `api_spec.md` 验证

```bash
wc -l docs/api_spec.md
# 116 行（合并前为 232 行，重复内容已去重）✅
```

接口表内容：
```
| 健康检查 | GET | /api/v1/health | 服务存活检测 | A | ✅ 已完成 |
| Agent 对话 | POST | /api/v1/agent/chat | ... | A | 🔨 Week 2 |
| 实时遥测 | GET | /api/v1/telemetry/live | ... | A | ⏳ Week 3 |
| 告警列表 | GET | /api/v1/alarm/list | ... | A | ⏳ Week 3 |
| 诊断报告 | GET | /api/v1/report/latest | ... | A | ⏳ Week 5 |
```

### 3. TODO 注释验证（抽样）

```bash
head -3 agent/graph/state.py
# P0-2 (Week 2-3): LangGraph AgentState 定义
# 前置条件：agent/chat 接口 mock 闭环已跑通 + DeepSeek API 已对接
# 当前阶段：占位，由 backend/services/agent_service.py 直接处理请求

head -3 backend/api/agent.py
# P0-5 (Week 2): POST /api/v1/agent/chat — Agent 对话接口
# 前置条件：DeepSeek API 已配置（.env 中 DEEPSEEK_API_KEY）
# 当前阶段：提供 mock 实现，返回固定诊断结果
```

✅ 14 个文件全部包含 P0 编号 + 周次 + 前置条件 + 当前阶段

---

## 接口变化

无新增接口。`docs/api_spec.md` 接口列表从空表填充为 5 行，均为已预留路由的状态标注。

| 接口 | 状态变化 |
|------|---------|
| `/api/v1/health` | 无变化（✅ 已完成） |
| `/api/v1/agent/chat` | 从"无记录"→ 标注为 🔨 Week 2 |
| `/api/v1/telemetry/live` | 从"无记录"→ 标注为 ⏳ Week 3 |
| `/api/v1/alarm/list` | 从"无记录"→ 标注为 ⏳ Week 3 |
| `/api/v1/report/latest` | 从"无记录"→ 标注为 ⏳ Week 5 |
