# Power-Agent MVP 架构总结

## 项目定位

基于 LLM Agent 的电厂智能预警与故障诊断系统，3~4 人团队，8 周开发周期，MVP 优先。

## 技术栈（已锁定，不可变更）

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| Agent 框架 | LangGraph |
| LLM | DeepSeek API（主）/ ChatGLM（备） |
| 业务数据库 | PostgreSQL |
| 时序数据库 | TimescaleDB（PG 扩展） |
| 向量数据库 | FAISS（Demo 阶段） |
| 前端 | Vue3 + Element Plus + ECharts |
| 数据接入 | MQTT / WebSocket（模拟） |
| 部署 | Docker Compose |

## MVP 核心闭环

```
用户输入自然语言
      ↓
Agent 解析意图 (LangGraph + DeepSeek)
      ↓
并行调用 Tool:
  ├── data_tool     → TimescaleDB 查询时序数据
  ├── alarm_tool    → 多策略异常检测
  ├── predict_tool  → LSTM/Prophet 趋势预测
  └── rag_tool      → FAISS 知识检索 + DeepSeek 推理
      ↓
结果融合 → 生成诊断报告
      ↓
Web 前端展示（Vue3 + ECharts）
```

## 角色分工

| 成员 | 角色 | 核心职责 | 关键交付 |
|------|------|---------|---------|
| A | 系统架构 + Agent + 后端 | Agent 流程、FastAPI 后端、Tool 框架、系统集成 | Agent 闭环可运行 |
| B | 工业数据 + 算法 | 数据库、模拟数据、异常检测、预测模型 | 数据+算法可用 |
| C | 前端 + 产品 | Vue3 监盘平台、图表、交互 | 完整 Dashboard |
| D | RAG + 测试 + 文档 | 知识库、FAISS、测试、比赛材料 | RAG 可用 + 文档齐全 |

## 模块接口契约（MVP 阶段锁定）

```
A 提供 → C:  REST API  (FastAPI, /api/v1/*)
B 提供 → A:  Python函数 (data_tool / alarm_tool / predict_tool)
D 提供 → A:  Python函数 (rag_tool)
B + D:       数据格式  (device / alarm / diagnosis JSON Schema)
```

## 时间规划

| 阶段 | 周次 | 里程碑 |
|------|------|--------|
| 环境搭建 | Week 1-2 | 所有人环境跑通，接口确认 |
| MVP 闭环 | Week 3-4 | 对话→数据→异常→展示 链路打通 |
| 智能增强 | Week 5-6 | RAG + 预测 + 完整面板 |
| 比赛冲刺 | Week 7-8 | 优化 + PPT + 演示 |
