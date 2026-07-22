# PR P0-1: 前端脚手架搭建

**提交者**：C (StarKing729)  
**PR 编号**：#23  
**分支**：`feature/starking729/vue-scaffold` → `develop`  
**审查人**：A  
**审查日期**：2026-07-16

---

## 一、背景

P0-1 任务：初始化 Vue3 + Element Plus 前端工程，为后续监控面板（P02）和 AI 对话（P03）开发打好基础。C 累计提交了 14 个 commit，覆盖 24 个文件，本次 PR 经过了前后两轮审查。

---

## 二、变更摘要

| 维度 | 内容 |
|------|------|
| 代码 | +334 行 / -207 行，24 个文件 |
| 脚手架 | Vite + Vue3 + ElementPlus + ECharts + Axios 全栈依赖 |
| 布局 | 深色侧边栏 Layout 组件（96 行） |
| 路由 | 嵌套路由，Layout 为父组件，/monitor 和 /chat 为子路由 |
| 代理 | Vite proxy `/api` → `localhost:8000`（第二轮审查已修复） |

---

## 三、文件清单

### ✅ 已合并至本地的脚手架文件（11 个）

| 文件 | 行数 | 说明 |
|------|------|------|
| `.gitignore` | 90 | 分区扩展：Python/Node/IDE/数据/模型/输出 |
| `frontend/.env.development` | 1 | `VITE_USE_MOCK=false` |
| `frontend/index.html` | 12 | 入口 HTML，favicon 改为 vite.svg |
| `frontend/vite.config.js` | 23 | **代理已恢复** + port:5173 + open:true |
| `frontend/src/App.vue` | 14 | 简化为纯 `<router-view/>` + 全局 CSS reset |
| `frontend/src/main.js` | 16 | ElementPlus 图标全局注册 |
| `frontend/src/router/index.js` | 28 | 嵌套路由 + Layout + meta 标题 |
| `frontend/src/style.css` | — | `100vh` → `100svh` 适配 |
| `frontend/src/components/Layout.vue` | 96 | 深色侧边栏 + 顶部导航 + 面包屑 |
| `frontend/src/views/Chat.vue` | 15 | AI 对话占位页面 |
| `frontend/src/components/.gitkeep` | 0 | 目录占位 |

### 🛡️ 保护未覆盖的本地文件（7 个）

| 文件 | 保护原因 |
|------|----------|
| `frontend/src/api/index.js` | C 的版本有 mock bug + 端口错误（8080→应为8000） |
| `frontend/src/api/request.js` | 仅有空格变化，无需合并 |
| `frontend/src/api/telemetry.js` | C 删除了 `getLiveTelemetry()` 函数 |
| `frontend/src/api/agent.js` | C 删除了 import + 函数模板 |
| `frontend/src/api/alarm.js` | 同上 |
| `frontend/src/api/report.js` | 同上 |
| `frontend/src/views/Monitor.vue` | C 替换为占位符，本地有 81 行完整轮询实现 |

---

## 四、与 C.md 任务对照

| C.md P0-1 要求 | 达成 |
|----------------|------|
| Vite + Vue3 项目可启动 | ✅ |
| Element Plus + ECharts + Axios 已安装 | ✅ |
| Vite 代理到 `localhost:8000` | ✅（第二轮修复） |
| `api/index.js` = Axios 实例 + 拦截器 | ✅（本地保留） |
| `api/agent.js` 等 = import + 函数模板 | ✅（本地保留） |
| 路由 `/monitor` + `/chat` | ✅ |
| Layout 布局组件 | ✅ |

---

## 五、审查结论

| 类别 | 数量 | 说明 |
|------|------|------|
| ✅ 脚手架结构 | — | 目录完整，依赖齐全，可启动 |
| ✅ vite.config.js | — | 代理已恢复，上次的关键 bug 已修复 |
| ✅ Layout.vue | — | 96 行深色侧边栏，结构清晰 |
| 🔴 不合并 | 7 | API 文件被清空 / Monitor.vue 被替换为占位符 |

### 🔴 本地已保护（C 需在后续 PR 中注意）

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 1 | `api/index.js` 与 `request.js` 脱钩 | frontend/src/api/ | C 的版本重复创建 axios 实例，mock 模式有 bug |
| 2 | API 文件被清空 | agent.js / telemetry.js / alarm.js / report.js | 删除了 import + 函数模板，仅剩单行注释 |
| 3 | Monitor.vue 被替换 | frontend/src/views/ | 81 行轮询代码被替换为"页面开发中..."占位符 |
| 4 | 错误端口号 | api/index.js | 错误提示写 `localhost:8080`，应为 `localhost:8000` |

---

## 六、C 的三个分支合并建议

C 在远程有三个分支：
- `feature/starking729/vue-scaffold`（PR #23，本次审查）
- `feature/starking729/dashboard`（监控面板，无 PR）
- `feature/starking729/chat-view`（AI 对话，无 PR）

**建议**：将三个分支合并到 `vue-scaffold`，统一维护一个分支一个 PR，避免线性依赖导致的合并冲突。

---

## 七、本地落盘（已由 A 完成）

仅合并脚手架文件，业务代码文件保持本地版本不变。C 需要在后续开发中：
1. 基于本次合并后的 develop 分支继续开发
2. `api/` 下的文件不要清空，保留 import + 函数模板
3. Monitor.vue 的轮询逻辑不要删除
