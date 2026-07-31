# C 成员 — Week 2 开发任务

## 上周回顾

| 任务 | 状态 | 说明 |
|------|------|------|
| P0-1 前端基座 | ✅ 完成 | Vite + Vue3 + Element Plus + ECharts + Axios，npm run dev 可启动 |
| P0-2 AI 对话窗口 | ✅ 已提交 PR #28 | ChatView + ChatMessage + QuickCommands + DiagnosisCard，待 review 合并 |

## 本周目标

**收尾 P0-2 + 实现实时监控面板（P0-3）。**

```
PR #28 合并 → 开始 P0-3 Dashboard → 3 设备卡片 + 3s 轮询 + 绿/黄/红状态色
```

---

## 任务 0：PR #28 合入（如有 review 意见则修改）

**截止**：Week 2 周一

### 要做什么

- 关注 PR #28 的 review 反馈，如有修改意见及时处理
- 确认 Chat 页面可以通过 npm run dev 正常访问 `/chat` 路由

### 验收

- PR #28 状态变为 **Merged**

---

## 任务 1：P0-3 — 实现实时监控面板（Dashboard）

**截止**：Week 2 周五

### 要做什么

**页面布局**：3 台设备卡片网格排列，每张卡片展示该设备的 3-4 个参数。

```
┌─────────────────────────────────────────────────┐
│  📊 设备实时监控面板                              │
│                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  │ ⚙ 2号锅炉    │ │ ⚙ 3号汽轮机  │ │ ⚙ 4号发电机  │
│  │              │ │              │ │              │
│  │ 主蒸汽温度    │ │ 转速         │ │ 有功功率      │
│  │ 548.5 ℃  🟢  │ │ 3012 rpm  🟢 │ │ 315 MW    🟡  │
│  │              │ │              │ │              │
│  │ 主蒸汽压力    │ │ 轴承温度      │ │ 定子温度      │
│  │ 16.8 MPa  🟢  │ │ 87 ℃     🟢  │ │ 118 ℃    🔴  │
│  │              │ │              │ │              │
│  │ 炉膛温度      │ │ 振动         │ │ 无功功率      │
│  │ 1210 ℃   🟡  │ │ 0.05 mm  🟢  │ │ 55 Mvar   🟢  │
│  └──────────────┘ └──────────────┘ └──────────────┘
│                                                  │
│  ⏱ 上次刷新：14:30:25          每 3 秒自动刷新   │
└─────────────────────────────────────────────────┘
```

### 状态颜色规则

| 颜色 | 条件 | 示例 |
|------|------|------|
| 🟢 绿色 | 值在正常范围内（normal_min ~ normal_max） | 温度 548℃ / 阈值 525~555 |
| 🟡 黄色 | 值接近阈值 90%~100% | 功率 315MW / 阈值上限 350MW |
| 🔴 红色 | 值超出阈值 | 定子温度 118℃ / 阈值上限 110℃ |

### 数据获取

- 调用 `GET /api/v1/telemetry/live` 获取所有设备实时数据
- 前端 `setInterval` 每 3 秒轮询一次
- 首次加载显示 loading 骨架屏
- 接口不可用时显示离线提示，不刷 502 错误

### 涉及文件

```
frontend/src/
├── views/
│   └── DashboardView.vue   ← 监控面板主页面（本周新建）
├── components/
│   ├── DeviceCard.vue      ← 单台设备卡片组件
│   ├── ParamGauge.vue      ← 单个参数显示组件（含状态色）
│   └── StatusIndicator.vue ← 状态指示器（绿/黄/红圆点）
└── api/
    └── telemetry.js        ← 实现 getLiveTelemetry() / getHistoryData()
```

### 验收标准

1. 仪表盘默认显示 3 台设备卡片
2. 每 3 秒数据自动刷新（mock 模式下数值应有变化）
3. 异常参数显示红色，接近阈值显示黄色，正常显示绿色
4. 接口不可用时显示"离线"提示而非白屏/刷屏
5. 页面卸载时清除定时器（无内存泄漏）

---

## 任务 2：在 api/index.js 中补充 telemetry mock

**截止**：Week 2 周三

### 要做什么

在 `api/index.js` 的 mock 字典中增加 `/telemetry/live` 的 mock 数据：

```javascript
const mocks = {
  '/agent/chat': {
    success: true,
    data: { reply: '这里是模拟的对话内容' }
  },
  '/telemetry/live': {
    success: true,
    data: {
      devices: [
        {
          device_id: 'generator_002',
          device_name: '2号锅炉',
          parameters: [
            { name: '主蒸汽温度', value: 548.5, unit: '℃', normal_min: 525, normal_max: 555, status: 'normal' },
            { name: '主蒸汽压力', value: 16.8, unit: 'MPa', normal_min: 16.0, normal_max: 17.5, status: 'normal' },
            { name: '炉膛温度', value: 1210, unit: '℃', normal_min: 1100, normal_max: 1250, status: 'warn' }
          ]
        },
        {
          device_id: 'turbine_003',
          device_name: '3号汽轮机',
          parameters: [
            { name: '转速', value: 3012, unit: 'rpm', normal_min: 2900, normal_max: 3100, status: 'normal' },
            { name: '轴承温度', value: 87, unit: '℃', normal_min: 70, normal_max: 95, status: 'normal' },
            { name: '振动', value: 0.05, unit: 'mm', normal_min: 0, normal_max: 0.08, status: 'normal' }
          ]
        },
        {
          device_id: 'generator_004',
          device_name: '4号发电机',
          parameters: [
            { name: '有功功率', value: 315, unit: 'MW', normal_min: 250, normal_max: 350, status: 'warn' },
            { name: '定子温度', value: 118, unit: '℃', normal_min: 85, normal_max: 110, status: 'danger' },
            { name: '无功功率', value: 55, unit: 'Mvar', normal_min: 20, normal_max: 80, status: 'normal' }
          ]
        }
      ]
    }
  }
}
```

> Mock 模式下可以给 value 加随机抖动（±2%），让 3 秒轮询能看到数值变化，Demo 效果更好。

---

## 本周沟通要点

- **周一**：关注 PR #28 review 状态
- **周三前**：完成 telemetry mock 数据 + telemetry.js API 封装
- **周五前**：完成 Dashboard 全部组件，`/dashboard` 路由可访问
- **周五**：提交 P0-3 PR（分支基于合并后的 develop）
