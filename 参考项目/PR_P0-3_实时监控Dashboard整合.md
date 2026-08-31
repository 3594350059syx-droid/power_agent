# P0-3：实时监控 Dashboard 选择性整合与遥测契约修复

**类型**：`feat` + `fix`
**本地整合提交**：`44ab64e`（`feat: integrate realtime monitoring dashboard`）
**整合基线**：`e2d1d48`（PR #38 审查修复）
**前端来源参考**：PR #37 最新远程提交 `87e3f7c`
**整合日期**：2026-08-26
**分支**：`feature/A/init-backend`

---

## 一、背景

PR #37 提供了设备实时监控面板的前端设计，包括设备卡片、参数仪表、状态展示和定时轮询。直接整体合并会覆盖 PR #38 已完成的预测、Mock 数据、数据服务和前端 Chat 修复；同时其遥测 Mock 使用 6 个共享测点，与当前项目的设备数据契约不一致。

本次采用选择性整合：以 PR #38 修复提交 `e2d1d48` 为基线，参考 PR #37 最新提交 `87e3f7c` 的 Dashboard 设计，形成仅包含实时监控相关改动的本地提交 `44ab64e`。

```text
PR #38 审查修复基线 e2d1d48
        +
PR #37 Dashboard 设计参考 87e3f7c
        ↓
本地整合提交 44ab64e
```

目标是在保留 PR #38 修复的前提下，提供可在真实后端和 Vite Mock 模式下运行的实时监控 Dashboard，并统一前后端设备、测点和状态语义。

---

## 二、统一的设备与遥测数据契约

遥测定义严格使用 `data/mock/config.py` 中的 **3 台设备 × 每台 3 个专属测点**：

| 设备 ID | 设备名称 | 专属测点 |
|---|---|---|
| `boiler_002` | 2号锅炉 | `steam_temp`、`steam_pressure`、`furnace_temp` |
| `turbine_003` | 3号汽轮机 | `rpm`、`bearing_temp`、`vibration` |
| `generator_004` | 4号发电机 | `power`、`stator_temp`、`reactive_power` |

每个测点包含：

```json
{
  "key": "steam_temp",
  "name": "主蒸汽温度",
  "unit": "℃",
  "normal_range": [525, 555],
  "value": 540.2,
  "level": "normal"
}
```

`GET /api/v1/telemetry/live` 统一返回：

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "device_status": {
      "device_id": "boiler_002",
      "status": "running"
    },
    "metrics": []
  }
}
```

未知设备不再错误回退为锅炉数据，明确返回：

```json
{
  "device_status": {
    "device_id": "unknown_device",
    "status": "unknown"
  },
  "metrics": []
}
```

---

## 三、实现内容

### 3.1 Dashboard 与组件

| 文件 | 说明 |
|---|---|
| `frontend/src/views/Dashboard.vue` | 三设备实时监控首页；并发加载、3 秒轮询、手动刷新、连接状态和离线提示 |
| `frontend/src/components/DeviceCard.vue` | 单设备状态卡片、测点列表、空数据/连接失败展示 |
| `frontend/src/components/ParamGauge.vue` | 参数数值、正常范围、进度条和参数状态 |
| `frontend/src/components/StatusIndicator.vue` | 状态文字与颜色指示器 |

Dashboard 使用 `Promise.allSettled` 并发请求 3 台设备。单台请求失败不会掩盖其他设备；当**全部遥测请求失败**时，页面显示“离线”，不会误报“已连接”。

### 3.2 状态颜色规则

| 状态 | 显示语义 | 颜色 |
|---|---|---|
| `running` / `normal` | 运行中 / 正常 | 绿色 |
| `warn` / `warning` | 预警 | 黄色 |
| `danger` / `error` / `stopped` | 异常 / 连接失败 / 已停止 | 红色 |
| `unknown` | 未知设备或未知状态 | 灰色 |

### 3.3 前端 API 与 Mock 行为

| 文件 | 修改 |
|---|---|
| `frontend/src/api/index.js` | Axios `baseURL` 优先使用 `VITE_API_BASE_URL`，缺失时回退 `/api/v1`；Dashboard 轮询请求可静默处理错误，避免重复弹窗。 |
| `frontend/src/api/telemetry.js` | 提供单设备/多设备实时遥测 API；Mock 模式在 HTTP 请求前直接返回 3×3 本地遥测数据。 |
| `frontend/src/api/agent.js` | Chat Mock 模式在 HTTP 请求前直接返回本地回复。 |
| `frontend/package.json` | 显式声明 `@element-plus/icons-vue`，供刷新图标使用。 |

开发环境配置：

```dotenv
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Mock 模式示例：

```powershell
$env:VITE_USE_MOCK = 'true'
npm run dev
```

### 3.4 路由和布局兼容性

| 路径/行为 | 调整结果 |
|---|---|
| `/dashboard` | 新的监控首页 |
| `/monitor` | 保留为重定向到 `/dashboard`，兼容旧链接 |
| `/` | 重定向到 `/dashboard` |
| 退出登录 | 清除 `token` 后跳转 `/dashboard`；项目没有 `/login`，因此不再导航到无效路径 |

### 3.5 后端实时遥测接口

`backend/api/telemetry.py` 优先读取 TimescaleDB 中的最新遥测数据，并在数据库不可用或数据尚未初始化时提供与 Mock 配置一致的完整快照：

- 仅当该设备的 3 个专属测点均有最新数据库记录时，返回真实数据；避免真实/随机数据混杂；
- 按正常区间和高低阈值将真实值转换为 `normal`、`warn`、`danger`；
- 数据库连接、设备、测点或数据不完整时，按 `device_id` 降级生成 3 个专属 Mock 测点；
- 85% 概率生成正常数据，15% 概率生成预警或异常数据，便于验证 UI 状态；
- 未知设备返回 `unknown` 加空测点数组；
- 保持 `/api/v1/telemetry/live` 的统一响应包装不变。

---

## 四、文件清单

| 文件 | 类型 | 说明 |
|---|---|---|
| `backend/api/telemetry.py` | 修改 | 3×3 设备专属遥测接口，真实库优先、完整快照校验和安全 Mock 降级 |
| `backend/services/telemetry_service.py` | 新增 | 最新数据库测点聚合查询、正常区间/阈值状态映射和数据库读取降级边界 |
| `frontend/src/views/Dashboard.vue` | 新增 | 实时监控面板 |
| `frontend/src/components/DeviceCard.vue` | 新增 | 设备卡片 |
| `frontend/src/components/ParamGauge.vue` | 新增 | 参数仪表 |
| `frontend/src/components/StatusIndicator.vue` | 新增 | 参数状态指示器 |
| `frontend/src/api/index.js` | 修改 | 环境变量基址和静默轮询错误处理 |
| `frontend/src/api/telemetry.js` | 修改 | 实时遥测 API、并发拉取和 Mock 短路 |
| `frontend/src/api/agent.js` | 修改 | Chat Mock 请求前短路 |
| `frontend/src/components/Layout.vue` | 修改 | 菜单改为 `/dashboard`，退出导航修复 |
| `frontend/src/router/index.js` | 修改 | 新增 Dashboard 并保留 `/monitor` 重定向 |
| `frontend/package.json`、`frontend/package-lock.json` | 修改 | 显式声明 Element Plus 图标依赖 |
| `tests/api/test_telemetry.py` | 新增 | 已知设备测点集和未知设备响应回归测试 |

---

## 五、验证结果

### 5.1 Python 定向回归测试

```powershell
python -m unittest tests.api.test_telemetry tests.algorithm.test_data_generation tests.algorithm.test_prediction -v
```

结果：

```text
Ran 51 tests
OK
```

覆盖：

- 3 台已知设备分别只返回各自的 3 个测点，且完整数据库快照优先于 Mock；
- 未知设备返回 `unknown` 和空测点数组；
- 内存 SQLite 验证每个测点取最新值、状态映射和不完整数据库快照降级；
- PR #38 Mock 数据配置、异常窗口、清理顺序和 SQLAlchemy 2.x 聚合查询；
- PR #38 sklearn 预测降级、趋势判断、模型持久化和时间原点。

### 5.2 ASGI 路由验证

使用 FastAPI `ASGITransport` 验证 `/api/v1/telemetry/live`：

```text
ASGI telemetry route: 3 known device contracts + unknown device contract passed
```

### 5.3 前端构建

```powershell
cd frontend
npm run build
$env:VITE_USE_MOCK = 'true'; npm run build
```

真实后端模式和 Mock 模式构建均通过。

> Vite 会输出既有的大 chunk 体积警告；不影响构建成功，且不由本次 Dashboard 整合引入。

### 5.4 浏览器级端到端验证

在真实后端模式（`VITE_USE_MOCK=false`，前端访问 `http://localhost:5173/dashboard`）完成浏览器实测：

- Dashboard 正常加载并显示“已连接”；
- 真实数据库中的 3 台设备均正常显示：2 号锅炉、3 号汽轮机、4 号发电机；
- 每台设备均显示各自完整的 3 个专属测点及数值、单位、正常范围和状态颜色；
- 页面自动刷新和手动刷新可正常工作，刷新时间及“每 3 秒自动刷新”提示正常显示；
- AI 智能助手页面正常加载并显示“在线”；
- AI 助手四个快捷功能均可正常运行：**实时监控、异常分析、趋势预测、故障诊断**。点击快捷功能后可生成对应问题并获得后端回复；
- `/monitor` 可正常跳转至 `/dashboard`。

---

## 六、边界与后续工作

| 项目 | 当前状态 | 说明 |
|---|---|---|
| 真实数据库实时查询 | 已完成并验证 | `/telemetry/live` 已优先读取每个测点的最新数据库值；Docker TimescaleDB 已成功写入 90,720 条时序记录，并验证 3 台设备均返回完整的数据库快照。 |
| 数据库离线降级延迟 | 已限制 | PostgreSQL/psycopg2 对每个解析地址的连接超时限制为 1 秒；`localhost` 的 IPv6/IPv4 均不可用时实测约 2 秒后回退到完整 Mock 快照，避免 Dashboard 轮询长时间阻塞。 |
| Dashboard 轮询 | 已完成 | 每 3 秒轮询；单设备失败可见，全部失败显示离线。 |
| Vite Mock | 已完成 | telemetry 和 chat 均在请求前短路，不依赖后端。 |
| `/monitor` 兼容 | 已完成 | 重定向至 `/dashboard`。 |
| 浏览器端到端验证 | 已完成并验证 | 真实后端模式下 Dashboard、3 台设备 × 3 个测点、自动/手动刷新、状态展示、`/monitor` 跳转及 AI 助手四个快捷功能均已通过浏览器实测。 |

---

## 七、本地工作区说明

本次只提交 Dashboard 整合相关的 14 个文件。以下既有本地内容未纳入 `44ab64e`：

- `agent/tools/report_tool.py`：用户本地修改；
- `data/mock/__init__.py`：用户未跟踪文件；
- `.review-pr37/`：本地 PR #37 参考目录。

`44ab64e` 为本地提交，整合过程未执行 `git push`。

---

## 八、结论

PR #37 的实时监控 Dashboard 已以选择性迁移方式整合到 PR #38 修复基线之上。前后端统一为 **3 设备 × 3 专属测点**契约；网络失败、状态颜色、Mock 短路、环境变量基址、路由兼容和未知设备行为均已修复，并通过 51 项 Python 回归、ASGI 接口验证、真实/Mock 两种前端构建验证及浏览器级端到端验证。