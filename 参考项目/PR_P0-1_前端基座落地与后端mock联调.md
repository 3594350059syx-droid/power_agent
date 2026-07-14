## 修改内容

将 C 的 PR #17 前端基座落地到本地 `frontend/` 目录，修复 4 个关键问题，并补齐后端 telemetry mock 接口——

1. **落地 PR #17 前端文件**：从 C 的 `feature/starking729/dashboard` 分支提取全部前端工程文件（package.json、vite.config.js、main.js、App.vue、router、request.js、telemetry.js、Monitor.vue、style.css 等），放入本地 `frontend/` 目录
2. **修复 App.vue `/chat` 死链接**：原文件侧边栏仍保留 `default-active="/chat"` 和「AI 对话诊断」菜单项，但 Chat.vue 和 `/chat` 路由已被删除；修复为 `default-active="/monitor"`，仅保留「实时监控面板」菜单
3. **修复 router `/chat` 残留**：`router/index.js` 仍含 `/chat` 路由懒加载 + `redirect: '/chat'`；移除，首页重定向改为 `/monitor`
4. **补齐缺失 API 文件**：C 只提供了 `request.js` 和 `telemetry.js`，按要求补充——
   - `api/index.js`：重导出 request.js，作为统一入口
   - `api/agent.js`：TODO 空壳（P0-2, Week 2）
   - `api/alarm.js`：TODO 空壳（P0-3, Week 3）
   - `api/report.js`：TODO 空壳（P1, Week 5）
5. **后端 telemetry mock 接口**：`backend/api/telemetry.py` 从纯 TODO 注释升级为完整 mock 端点，返回 6 个设备参数（温度/压力/振动/流量等），含 15% 概率异常值（黄/红告警），每 3 秒由前端轮询
6. **修复 `backend/main.py` 代码顺序**：telemetry router 的 import/注册被误放在 `app = FastAPI()` 之前导致 `NameError`；调整到正确位置，同时清理重复的 `health_router` import
7. **修复 `frontend/src/api/request.js` 重复拦截器**：响应拦截器因合并残留重复了两份；合并为一份，优化错误提示区分"后端未启动"与"HTTP 状态码错误"

---

## 影响模块

### 新增文件（前端基座，共 13 个）

| 文件 | 来源 |
|------|------|
| `frontend/package.json` | C 的 PR #17（依赖：vue, vue-router, axios, echarts, element-plus, vite） |
| `frontend/vite.config.js` | C 的 PR #17（代理 `/api` → `localhost:8000`，`@` 别名） |
| `frontend/index.html` | C 的 PR #17（标题改为项目名） |
| `frontend/.gitignore` | C 的 PR #17（node_modules, dist, .vscode 等） |
| `frontend/src/main.js` | C 的 PR #17（Vue3 + ElementPlus + Router 全局注册） |
| `frontend/src/App.vue` | **修复版**（移除 `/chat` 死链接） |
| `frontend/src/style.css` | C 的 PR #17（Vite 脚手架样式） |
| `frontend/src/router/index.js` | **修复版**（移除 `/chat` 路由） |
| `frontend/src/api/request.js` | **修复版**（合并重复拦截器） |
| `frontend/src/api/telemetry.js` | C 的 PR #17（`getLiveTelemetry`，3s 轮询用） |
| `frontend/src/views/Monitor.vue` | C 的 PR #17（3s 轮询 + 绿/黄/红状态色 + Mock fallback） |

### 补充新增文件（C 缺失的 API 空壳）

| 文件 | 内容 |
|------|------|
| `frontend/src/api/index.js` | 重导出 request.js，统一入口 |
| `frontend/src/api/agent.js` | P0-2 TODO 空壳 |
| `frontend/src/api/alarm.js` | P0-3 TODO 空壳 |
| `frontend/src/api/report.js` | P1 TODO 空壳 |

### 修改文件（后端）

| 文件 | 变更 |
|------|------|
| `backend/api/telemetry.py` | 从 4 行 TODO → 60 行 mock 端点（6 参数 + 随机异常值） |
| `backend/main.py` | 修复 import/路由注册顺序 + 注册 telemetry_router |

### 清理

| 操作 | 说明 |
|------|------|
| 删除 `frontend/api/`、`components/`、`views/` | 旧骨架空目录，不在 Vite 项目结构中 |

---

## 测试结果

### 1. 前端文件结构

```powershell
Get-ChildItem -Path frontend -Recurse -Name
```

```text
src/
.gitignore
index.html
package.json
vite.config.js
src/api/
src/router/
src/views/
src/App.vue
src/main.js
src/style.css
src/api/agent.js
src/api/alarm.js
src/api/index.js
src/api/report.js
src/api/request.js
src/api/telemetry.js
src/router/index.js
src/views/Monitor.vue
```

✅ 19 个文件，目录结构符合 C.md P0-1 规格

### 2. 前端启动

```powershell
cmd /c npm install   # 无报错 ✅
cmd /c npm run dev   # http://localhost:5173 正常启动 ✅
```

### 3. `/chat` 死链接确认

- 侧边栏仅显示「实时监控面板」，无「AI 对话诊断」菜单 ✅
- 地址栏自动跳转 `/#/monitor` ✅
- F12 Console 无 `/chat` 相关路由报错 ✅

### 4. 后端 mock 接口

```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/v1/telemetry/live?device_id=dev_001
```

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "device_status": {"device_id": "dev_001", "status": "running"},
    "metrics": [
      {"key": "steam_temp", "name": "主蒸汽温度", "value": 542.3, "unit": "℃", "level": "normal"},
      {"key": "steam_pressure", "name": "主蒸汽压力", "value": 16.7, "unit": "MPa", "level": "normal"},
      ...
    ]
  }
}
```

✅ 6 个参数全部返回，格式符合统一响应规范

### 5. 前后端联调

前端 `localhost:5173` 监控面板：
- 首次加载显示参数卡片（绿/黄/红状态色）✅
- 每 3 秒自动刷新，数值波动变化 ✅
- 偶发黄色/红色告警（~15% 概率）✅
- 终端无 404/502 报错 ✅

---

## 接口变化

| 接口 | 状态变化 |
|------|---------|
| `/api/v1/telemetry/live` | 从 ⏳ Week 3 占位 → 🔨 mock 实现（6 参数 + 随机异常值，联调可用） |
| 其他接口 | 无变化 |
