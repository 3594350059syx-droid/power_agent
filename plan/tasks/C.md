# C 成员开发任务文档

## 1. 角色定位

**前端与产品负责人**

你是项目的"门面担当"。评委第一眼看到的是你的界面。你负责：
- Vue3 + Element Plus 前端工程搭建
- Web 监盘 Dashboard 开发
- ECharts 数据可视化图表
- 与 A 的后端 API 对接
- Demo 交互流程设计

## 2. MVP 目标

实现以下前端页面：

```
AI 对话窗口（用户可以输入自然语言与 Agent 交互）
  + 
实时监控面板（显示设备参数卡片，每 3 秒刷新）
```

MVP 验收标准：**用户在 AI 对话框输入"分析2号机组温度异常" → 后端返回诊断结果 → 前端展示诊断文本和简易趋势图。**

## 3. 具体开发任务

---

### P0-1: 初始化 Vue3 + Element Plus 前端工程

**技术方案**：
- 使用 Vite 创建 Vue3 项目
- 安装 Element Plus UI 组件库
- 安装 ECharts 图表库
- 安装 Axios HTTP 客户端
- 配置代理（开发环境代理到 `localhost:8000`）

**涉及目录**：
```
frontend/
├── package.json          ← 依赖管理
├── vite.config.js        ← Vite 配置 + API 代理
├── index.html            ← 入口 HTML
├── src/
│   ├── main.js           ← Vue 入口
│   ├── App.vue           ← 根组件 + 路由
│   ├── router/
│   │   └── index.js      ← Vue Router 路由
│   ├── api/
│   │   ├── index.js      ← Axios 实例 + 拦截器
│   │   ├── agent.js      ← Agent 对话 API
│   │   ├── telemetry.js  ← 数据查询 API
│   │   ├── alarm.js      ← 告警 API
│   │   └── report.js     ← 报告 API
│   ├── components/       ← 通用组件
│   └── views/            ← 页面组件
└── public/
```

**输入依赖**：无（基础搭建）

**输出结果**：
- `npm run dev` 可启动，访问 `http://localhost:5173`
- 页面显示 Element Plus 默认布局框架

**验收标准**：
```bash
cd frontend
npm install
npm run dev
# 浏览器访问 http://localhost:5173 → 看到 Vue3 + Element Plus 页面
```

---

### P0-2: 实现 AI 对话窗口组件

**技术方案**：
- Element Plus `el-input` + `el-button` 输入框
- 消息列表渲染（用户消息右侧、Agent 消息左侧）
- 支持 Enter 发送消息
- 调用 `POST /api/v1/agent/chat` 接口
- 响应中展示文本 + 简易数据摘要
- 快捷指令按钮行：[实时监控] [异常分析] [趋势预测] [故障诊断]

**涉及目录**：
```
frontend/src/
├── views/
│   └── ChatView.vue       ← AI 对话页面
├── components/
│   ├── ChatMessage.vue    ← 单条消息组件
│   ├── QuickCommands.vue  ← 快捷指令按钮组
│   └── DiagnosisCard.vue  ← 诊断结果卡片
└── api/
    └── agent.js           ← chat API 封装
```

**输入依赖**：
- A 的 `/api/v1/agent/chat` 接口可用（至少返回 mock 数据）

**输出结果**：
- 一个可用的 AI 对话页面
- 支持文本输入 + 快捷指令

**验收标准**：
1. 输入"分析2号机组温度异常"，点击发送
2. 前端显示发送中状态（loading）
3. 收到后端响应后，展示 AI 回复文本

---

### P0-3: 实现实时监控面板

**技术方案**：
- 设备参数卡片布局（3 台设备 × 3-4 个参数）
- 每个卡片显示：参数名、当前值、单位、状态颜色（绿/黄/红）
- 调用 `GET /api/v1/telemetry/live` 获取数据
- 每 3 秒自动轮询刷新
- 状态颜色规则：
  - 绿色：正常范围
  - 黄色：接近阈值（90%~100%）
  - 红色：超出阈值

**涉及目录**：
```
frontend/src/
├── views/
│   └── DashboardView.vue  ← 监控面板页面
├── components/
│   ├── DeviceCard.vue     ← 设备卡片组件
│   ├── ParamGauge.vue     ← 参数仪表盘组件
│   └── StatusIndicator.vue ← 状态指示器组件
└── api/
    └── telemetry.js       ← 实时数据 API 封装
```

**输入依赖**：
- A 的 `/api/v1/telemetry/live` 接口可用
- B 的数据库有模拟数据

**输出结果**：
- 一个仪表盘页面，展示 3 台设备的关键参数
- 数据每 3 秒自动刷新

**验收标准**：
1. 仪表盘默认显示 3 台设备卡片
2. 每 3 秒数据自动刷新（可观察数值变化）
3. 异常参数显示为红色/黄色

---

### P1-1: 实现趋势分析图表页面

**技术方案**：
- ECharts 折线图展示历史趋势
- 支持设备选择（下拉框）、参数选择、时间范围选择
- 支持图表缩放（dataZoom）
- 调用 A 的接口获取历史数据
- 异常区间高亮标注

**涉及目录**：
```
frontend/src/
├── views/
│   └── TrendView.vue      ← 趋势分析页面
├── components/
│   ├── TrendChart.vue     ← ECharts 趋势图组件
│   ├── TimeRangePicker.vue ← 时间范围选择器
│   └── ParamSelector.vue  ← 参数选择器
└── api/
    └── telemetry.js       ← 增加历史数据查询 API
```

**输入依赖**：
- A 的历史数据查询接口
- B 的数据库有足够历史数据

**输出结果**：
- 可选择设备和参数查看历史趋势曲线
- 支持缩放和时间范围选择

**验收标准**：
1. 选择"2号锅炉 → 主蒸汽温度 → 过去24小时"
2. ECharts 折线图正确展示数据
3. 鼠标滚轮可缩放图表
4. 异常区间以红色区域标注

---

### P1-2: 实现告警中心页面

**技术方案**：
- Element Plus `el-table` 展示告警列表
- 列：时间、设备、参数、告警类型、严重等级、当前值、阈值、状态
- 支持按严重等级过滤（全部/高/中/低）
- 支持按时间排序
- 严重等级颜色标签：HIGH=红色、MEDIUM=橙色、LOW=黄色
- 调用 `GET /api/v1/alarm/list` 接口

**涉及目录**：
```
frontend/src/
├── views/
│   └── AlarmView.vue      ← 告警中心页面
├── components/
│   ├── AlarmTable.vue     ← 告警表格组件
│   └── AlarmFilter.vue    ← 告警过滤器组件
└── api/
    └── alarm.js           ← 告警 API 封装
```

**输入依赖**：
- A 的 `/api/v1/alarm/list` 接口
- B 的数据库有告警记录

**验收标准**：
1. 告警列表正确展示（至少 5 条告警记录）
2. 过滤功能可用
3. 颜色标签正确显示

---

### P1-3: 实现历史统计页面

**技术方案**：
- ECharts 柱状图/饼图展示告警统计
- 展示维度：按设备、按告警类型、按时间段
- 风险趋势折线图（7 天变化）
- 调用 A 的接口获取统计数据

**涉及目录**：
```
frontend/src/
├── views/
│   └── StatisticsView.vue ← 历史统计页面
├── components/
│   ├── AlarmBarChart.vue  ← 告警柱状图
│   ├── AlarmPieChart.vue  ← 告警饼图
│   └── RiskTrendChart.vue ← 风险趋势图
```

**验收标准**：统计图表数据正确，切换维度正常刷新

---

### P2-1: 页面整合 + 导航系统

**技术方案**：
- Element Plus `el-menu` 侧边导航
- 路由：`/chat` `/dashboard` `/trend` `/alarm` `/statistics`
- 统一页面布局（Header + Sidebar + Main）
- 响应式适配

**涉及目录**：
```
frontend/src/
├── App.vue               ← 根布局
├── router/index.js       ← 完整路由
├── components/
│   └── Layout.vue        ← 统一布局组件
```

**验收标准**：所有页面通过侧边栏导航可正常切换

---

## 4. 开发流程

### 阶段 1：环境准备（Week 1 前两天）
- **做什么**：安装 Node.js 18+，创建 Vue3 项目，安装依赖
- **沟通对象**：无
- **产出文件**：`frontend/` 完整工程结构，`package.json`

### 阶段 2：接口确认（Week 1 后三天）
- **做什么**：与 A 逐一确认 API 接口格式、请求/响应结构
- **沟通对象**：A（API 规范）
- **产出文件**：`frontend/src/api/` 下所有 API 封装文件（先用 mock 数据）

### 阶段 3：模块开发（Week 2-4）
- **做什么**：P0-2 → P0-3 顺序执行，可先 mock 数据独立开发
- **沟通对象**：A（接口调试）
- **产出文件**：ChatView + DashboardView 可用

### 阶段 4：本地测试（Week 4 末尾）
- **做什么**：前端页面自测，确保 UI 无异常
- **沟通对象**：无
- **产出文件**：自测报告

### 阶段 5：提交 GitHub（持续）
- **做什么**：每完成一个页面 commit + push
- **沟通对象**：A（Code Review）
- **产出文件**：feature 分支 + PR

### 阶段 6：联调（Week 5-6）
- **做什么**：切换 mock 为真实 API，与 A 的后端联调
- **沟通对象**：A（后端 API）
- **产出文件**：全页面联调通过

---

## 5. 与 A 的 API 对接规范

### 开发阶段 mock 方案

在 A 后端就绪前，使用 mock 数据独立开发：

```javascript
// frontend/src/api/index.js
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

// mock 数据示例
const mockTelemetry = {
  success: true,
  data: {
    devices: [
      { id: "generator_002", name: "2号锅炉", parameters: [
        { name: "主蒸汽温度", value: 548.5, unit: "℃", status: "normal" },
        { name: "主蒸汽压力", value: 16.8, unit: "MPa", status: "normal" },
        { name: "炉膛温度", value: 1210, unit: "℃", status: "normal" }
      ]},
      // ... 其他设备
    ]
  }
}
```

### API 对接清单

| API | Method | 用途 | Mock 就绪 |
|-----|--------|------|----------|
| `/api/v1/agent/chat` | POST | AI 对话 | ✅ |
| `/api/v1/telemetry/live` | GET | 实时监控数据 | ✅ |
| `/api/v1/telemetry/history` | GET | 历史趋势数据 | ✅ |
| `/api/v1/alarm/list` | GET | 告警列表 | ✅ |
| `/api/v1/report/latest` | GET | 最新诊断报告 | P1 |

### 响应统一格式

```json
{
  "success": true,
  "message": "操作成功",
  "data": { /* 具体数据 */ }
}
```

前端统一处理：`success === false` 时用 `ElMessage.error()` 提示。
