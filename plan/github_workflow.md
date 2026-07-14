# GitHub 团队协作规范

## 1. 分支策略

```
main          ← 稳定版本，只有队长 A 可以合并
  └── develop ← 开发集成分支，所有人 feature 分支合并到这里
       ├── feature/A/init-backend     ← A 的后端初始化
       ├── feature/A/agent-workflow   ← A 的 Agent 工作流
       ├── feature/A/llm-integration  ← A 的 LLM 对接
       ├── feature/B/database-schema  ← B 的数据库设计
       ├── feature/B/mock-data        ← B 的模拟数据
       ├── feature/B/anomaly-detect   ← B 的异常检测
       ├── feature/C/vue-scaffold     ← C 的前端脚手架
       ├── feature/C/chat-view        ← C 的对话页面
       ├── feature/C/dashboard        ← C 的监控面板
       ├── feature/D/knowledge-docs   ← D 的知识文档
       ├── feature/D/faiss-index      ← D 的 FAISS 索引
       └── feature/D/test-cases       ← D 的测试用例
```

**规则**：
- `main` 分支只有队长 A 有权限合并
- `develop` 分支是日常集成目标
- 每人从 `develop` 拉 `feature` 分支，完成后提 PR 到 `develop`
- 分支命名：`feature/{角色}/{简短描述}`
- 禁止直接 push 到 `main` 或 `develop`

## 2. Commit 规范

### 格式

```
<type>: <简短描述>

[可选的详细说明]
```

### Type 类型（这个可以省略，但是提交时候的修改内容介绍不能省）

| Type | 用途 | 示例 |
|------|------|------|
| `feat` | 新增功能 | `feat: 实现 Agent 意图识别` |
| `fix` | 修复 Bug | `fix: 修复时序查询时区错误` |
| `docs` | 文档修改 | `docs: 更新 API 接口列表` |
| `refactor` | 代码重构 | `refactor: 提取 Tool 基类` |
| `test` | 测试相关 | `test: 添加异常检测单元测试` |
| `chore` | 构建/工具 | `chore: 添加 faiss-cpu 依赖` |
| `style` | 格式调整 | `style: 统一代码缩进` |


### 要求

- 每次 commit 只做一件事
- commit message 用中文（团队内部项目）
- 不要提交 `__pycache__`、`.venv`、`node_modules` 等（已在 `.gitignore` 中）


## 3. Pull Request 流程

### 提 PR 前

1. 本地测试通过
2. 从 `develop` 拉最新代码，解决冲突
3. 确认没有遗留调试代码（`print` / `console.log`）

### PR 内容必须包含

```markdown
## 修改内容
[简述做了什么]

## 影响模块
[列出受影响的文件/模块]

## 测试结果
[贴测试截图或命令行输出]

## 接口变化
[如果有接口变化，列出变化前后的对比]
```

### 审核规则

| 角色 | 审核人 |
|------|--------|
| A | B 审核（涉及 Tool 接口时）|
| B | A 审核 |
| C | A 审核 |
| D | A 审核 |

### 合并规则

- 至少 1 人 Approve 后才能合并
- 合并使用 **Squash and Merge**（保持 develop 历史干净）
- 合并后删除 feature 分支



## 4. 日常协作流程

### 每日流程

```
上午：
  1. git pull origin develop（拉最新代码）
  2. 继续开发

下午（或任务完成时）：
  3. git add + git commit（提交本地）
  4. git push origin feature/xxx（推送到远程）
  5. 在 GitHub 创建 PR
  6. 在团队群通知审核人
```

### 冲突处理

- 遇到 merge conflict 时，**在本地解决冲突后再 push**
- 不要直接在 GitHub Web 界面解决冲突
- 如果不确定如何解决，找 A（队长）一起处理

## 5. 代码上传说明模板

每次创建 PR 时，必须在下方的 description 中填写：

```
修改内容：
[例如：实现 data_tool() 数据查询函数，支持按设备+参数+时间范围查询 TimescaleDB]

影响模块：
[例如：backend/services/data_service.py, agent/tools/data_tool.py]

测试结果：
[例如：
- 查询2号锅炉24小时温度数据，返回1440条记录 ✅
- 查询不存在的设备，返回空数据 ✅
- 时间范围跨天查询，时区正确 ✅
]

接口变化：
[例如：无变化 / data_tool 新增 params 参数 "aggregation": "5min" ]
```

## 6. .gitignore 确认

确保以下内容在 `.gitignore` 中：

```
# Python
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/

# Node
node_modules/
dist/

# IDE
.idea/
.vscode/

# Environment
.env

# Data
*.pkl
*.faiss
data/mock/output/*.csv

# OS
.DS_Store
Thumbs.db

#Qoder
.qoder
```
