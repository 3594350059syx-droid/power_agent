
# Development Plan


## 1. 项目目标

项目名称：

Power-Agent

基于大语言模型 Agent 的电厂智能预警与故障诊断系统。

开发周期：

8周

最终目标：

完成一个可运行 Demo，实现：

- 电厂运行数据模拟
- 异常检测
- 故障诊断
- Agent智能问答
- 可视化展示


---


# 2. 开发原则

采用：

- 模块化开发
- API First
- Git协作
- 快速迭代

开发流程：

需求分析

↓

系统设计

↓

模块开发

↓

接口联调

↓

Demo优化


---


# 3. 团队分工


## Leader / 架构负责人

负责：

- 系统架构设计
- Agent流程设计（LangGraph）
- 项目管理
- 文档维护
- 最终集成

主要目录：

docs/

agent/


---


## Backend负责人

负责：

- 后端服务（FastAPI）
- API接口
- 数据库（PostgreSQL + TimescaleDB）
- 系统集成

主要目录：

backend/

data/database/


---


## Algorithm负责人

负责：

- 数据处理
- 异常检测模型
- 故障诊断模型
- 知识库构建（FAISS / RAG）

主要目录：

algorithms/

rag/


---


## Frontend负责人

负责：

- Web界面（Vue3 + Element Plus）
- 数据展示（ECharts）
- 告警展示
- 交互设计

主要目录：

frontend/


---


# 4. 开发阶段计划


# 第一阶段：项目初始化（Week 1）

目标：

完成基础工程框架。

任务：

- 创建Git仓库
- 确定目录结构
- 完成architecture.md
- 定义API规范
- 搭建FastAPI后端框架
- 准备模拟数据

输出：

✅ 项目骨架


---


# 第二阶段：核心功能开发（Week 2-4）

目标：

完成最小可运行Demo。

任务：

Backend：

- 完成API接口
- 完成PostgreSQL + TimescaleDB数据库设计
- 数据读取接口

Algorithm：

- 完成异常检测
- 完成故障分类模型

Agent：

- 接入DeepSeek API / ChatGLM
- 完成LangGraph任务调度

输出：

✅ 数据 → 模型 → 诊断结果 全流程运行


---


# 第三阶段：系统集成（Week 5-6）

目标：

完成完整系统。

任务：

- 前后端联调
- Agent接入
- 优化模型效果
- 增加FAISS知识库
- 完善告警流程
- MQTT实时数据接入

输出：

✅ 完整Demo系统


---


# 第四阶段：优化展示（Week 7-8）

目标：

比赛展示版本。

任务：

- 优化UI
- 增加演示案例
- 制作PPT
- 编写项目文档
- 准备答辩

输出：

✅ 比赛提交版本


---


# 5. 里程碑


| 时间 | 目标 |
| --- | --- |
| Week1 | 项目框架完成 |
| Week2 | 数据流跑通 |
| Week4 | 最小Demo完成 |
| Week6 | 完整功能完成 |
| Week8 | 比赛版本完成 |


---


# 6. Git开发规范

分支：

main：

正式版本

dev：

开发版本

feature：

个人功能开发

提交规范：

- feat: 新功能
- fix: 修复Bug
- docs: 文档更新
- refactor: 代码重构
- test: 测试相关
- chore: 构建/工具变动

示例：

feat: 添加异常检测模块
fix: 修复时序查询时间范围错误
docs: 更新API接口文档
=======
# Development Plan


## 1. 项目目标

项目名称：

Power-Agent

基于大语言模型 Agent 的电厂智能预警与故障诊断系统。

开发周期：

8周

最终目标：

完成一个可运行 Demo，实现：

- 电厂运行数据模拟
- 异常检测
- 故障诊断
- Agent智能问答
- 可视化展示


---


# 2. 开发原则

采用：

- 模块化开发
- API First
- Git协作
- 快速迭代

开发流程：

需求分析

↓

系统设计

↓

模块开发

↓

接口联调

↓

Demo优化


---


# 3. 团队分工


## Leader / 架构负责人

负责：

- 系统架构设计
- Agent流程设计（LangGraph）
- 项目管理
- 文档维护
- 最终集成

主要目录：

docs/

agent/


---


## Backend负责人

负责：

- 后端服务（FastAPI）
- API接口
- 数据库（PostgreSQL + TimescaleDB）
- 系统集成

主要目录：

backend/

data/database/


---


## Algorithm负责人

负责：

- 数据处理
- 异常检测模型
- 故障诊断模型
- 知识库构建（FAISS / RAG）

主要目录：

algorithms/

rag/


---


## Frontend负责人

负责：

- Web界面（Vue3 + Element Plus）
- 数据展示（ECharts）
- 告警展示
- 交互设计

主要目录：

frontend/


---


# 4. 开发阶段计划


# 第一阶段：项目初始化（Week 1）

目标：

完成基础工程框架。

任务：

- 创建Git仓库
- 确定目录结构
- 完成architecture.md
- 定义API规范
- 搭建FastAPI后端框架
- 准备模拟数据

输出：

✅ 项目骨架


---


# 第二阶段：核心功能开发（Week 2-4）

目标：

完成最小可运行Demo。

任务：

Backend：

- 完成API接口
- 完成PostgreSQL + TimescaleDB数据库设计
- 数据读取接口

Algorithm：

- 完成异常检测
- 完成故障分类模型

Agent：

- 接入DeepSeek API / ChatGLM
- 完成LangGraph任务调度

输出：

✅ 数据 → 模型 → 诊断结果 全流程运行


---


# 第三阶段：系统集成（Week 5-6）

目标：

完成完整系统。

任务：

- 前后端联调
- Agent接入
- 优化模型效果
- 增加FAISS知识库
- 完善告警流程
- MQTT实时数据接入

输出：

✅ 完整Demo系统


---


# 第四阶段：优化展示（Week 7-8）

目标：

比赛展示版本。

任务：

- 优化UI
- 增加演示案例
- 制作PPT
- 编写项目文档
- 准备答辩

输出：

✅ 比赛提交版本


---


# 5. 里程碑


| 时间 | 目标 |
| --- | --- |
| Week1 | 项目框架完成 |
| Week2 | 数据流跑通 |
| Week4 | 最小Demo完成 |
| Week6 | 完整功能完成 |
| Week8 | 比赛版本完成 |


---


# 6. Git开发规范

分支：

main：

正式版本

dev：

开发版本

feature：

个人功能开发

提交规范：

- feat: 新功能
- fix: 修复Bug
- docs: 文档更新
- refactor: 代码重构
- test: 测试相关
- chore: 构建/工具变动

示例：

feat: 添加异常检测模块
fix: 修复时序查询时间范围错误
docs: 更新API接口文档

