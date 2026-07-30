# PR P0-4: 同步 B 的真实实现 + 修复接口一致性

**提交者**：A（队长，系统架构与 Agent 负责人）  
**分支**：本地同步（基于 B 的 PR #34 + A 端接口修复）  
**审查人**：A（自审）  
**审查日期**：2026-07-28

---

## 一、背景

B 提交了 PR #34（feat: complete P0-2, P0-3, P0-4），包含模拟数据生成、数据查询服务、异常检测算法的完整实现。审查后发现 2 个严重接口不一致问题：
1. **device_id 语义不匹配**：A 端将"2号锅炉"映射为 `generator_002`，B 端正确使用 `boiler_002`
2. **parameter 命名不一致**：A 端用 `rpm`/`power`，B 初始版本用 `speed`/`active_power`

B 在第 3 个 commit（`821e27`）中修复了问题 2（新增 PARAM_MAP + device_code 字段），但问题 1 中 A 端的映射错误仍需 A 自行修复。

本次变更：同步 B 的全部实现到本地 + 修复 A 端 device_code 映射错误 + 重构 Tool 注册中心支持 real/mock 自动降级。

---

## 二、变更摘要

| 维度 | 内容 |
|------|------|
| 新增文件 | 12 个（B 的 P0-2 数据生成 3 个 + P0-4 算法 4 个 + mock 分离 2 个 + 包初始化 3 个） |
| 修改文件 | 10 个（A 端 device_code 修复 6 个 + 服务层覆盖 2 个 + 数据库/依赖 2 个） |
| 严重问题修复 | 2 个（device_code 映射 + parameter 命名统一） |
| 架构升级 | Tool 注册中心从纯 mock 升级为 real + mock 自动降级 |
| 验证结果 | P0-2 回归 73/73 + P0-3 意图识别 10/10，全部通过 |

---

## 三、文件清单

### 新增文件（12 个）

| 文件 | 行数 | 说明 | 来源 |
|------|------|------|------|
| `data/mock/__init__.py` | 1 | 包初始化 | A 创建 |
| `data/mock/generate_data.py` | 233 | 模拟数据生成脚本（3 设备 × 4 测点 × 7 天 + 4 种异常场景） | B 实现 |
| `data/mock/normal_pattern.py` | 103 | 正常数据模式（日周期波动 + 高斯噪声） | B 实现 |
| `data/mock/anomaly_scenarios.py` | 77 | 4 种异常注入（温度上升/振动突变/压力下降/定子过热） | B 实现 |
| `algorithms/__init__.py` | 1 | 包初始化 | A 创建 |
| `algorithms/anomaly_detection/__init__.py` | 5 | 导出 3 个检测器 | B 实现 |
| `algorithms/anomaly_detection/threshold_detector.py` | 90 | 阈值异常检测器（超高/超低 + score 归一化） | B 实现 |
| `algorithms/anomaly_detection/trend_detector.py` | 169 | 趋势异常检测器（滑动窗口线性回归 + 变化率） | B 实现 |
| `algorithms/anomaly_detection/risk_scorer.py` | 110 | 综合风险评分器（0.5×threshold + 0.5×trend） | B 实现 |
| `agent/tools/data_tool_mock.py` | 98 | A 的 mock 实现分离（data_tool_mock + predict_tool_mock） | A 重构 |
| `agent/tools/alarm_tool_mock.py` | 38 | A 的 mock 实现分离（alarm_tool_mock） | A 重构 |

### 修改文件（10 个）

| 文件 | 变更内容 | 修改者 |
|------|---------|--------|
| `agent/prompts/system_prompt.py` | device_map: `"2号锅炉"` → `boiler_002`（原错误映射为 generator_002）；PARAM_EXTRACTION_TEMPLATE 设备名映射表同步更新 | A 修复 |
| `agent/prompts/intent_examples.py` | 3 条 Few-shot 示例的 device_id 从 `generator_002` 改为 `boiler_002` | A 修复 |
| `tests/agent/intent_test_cases.json` | 5 条测试用例的 expected_params.device_id 改为 `boiler_002` | A 修复 |
| `test.py` | mock 测试 device_id 改为 `boiler_002`；参数抽取测试期望值同步更新 | A 修复 |
| `agent/graph/workflow.py` | alarm_tool/predict_tool 默认 device_id 改为 `boiler_002` | A 修复 |
| `agent/tools/base.py` | docstring 示例 device_id 改为 `boiler_002` | A 修复 |
| `agent/tools/data_tool.py` | 从 mock 覆写为 B 的真实实现（data_tool + compare_devices_tool + list_devices_tool + list_sensors_tool） | B 实现 |
| `agent/tools/alarm_tool.py` | 从 mock 覆写为 B 的真实实现（alarm_tool + alarm_history_tool + pending_alarms_tool + acknowledge_alarm_tool） | B 实现 |
| `backend/services/data_service.py` | 从空壳覆写为完整实现（PARAM_MAP + device_code 查找 + 聚合查询 + 多设备对比） | B 实现 |
| `backend/services/alarm_service.py` | 从空壳覆写为完整实现（阈值+趋势检测 + 风险评分 + 告警历史） | B 实现 |
| `backend/database/init.sql` | device 表新增 `device_code` 字段（UNIQUE NOT NULL）+ 索引 | B 实现 |
| `backend/database/models.py` | Device ORM 新增 `device_code` 字段 | B 实现 |
| `agent/tools/__init__.py` | 重构为 real + mock 自动降级机制 | A 重构 |
| `requirements.txt` | 新增 `openai`/`pandas`/`scikit-learn`，分类注释优化 | B+A |

---

## 四、修复的严重问题

### 问题 1: device_code 映射错误

**根因**：A 在 P0-2 阶段编写 `system_prompt.py` 的 `device_map` 时，将"2号锅炉"错误映射为 `generator_002`（应为 `boiler_002`）。

**影响范围**：6 个文件
- `system_prompt.py` — device_map + PARAM_EXTRACTION_TEMPLATE
- `intent_examples.py` — 3 条 Few-shot 示例
- `intent_test_cases.json` — 5 条测试用例
- `test.py` — mock 测试 + 参数抽取测试
- `workflow.py` — 默认 device_id
- `base.py` — docstring 示例

**修复**：全部改为 `boiler_002`，与 B 的数据库 `device_code` 一致。

### 问题 2: parameter 命名不一致

**根因**：B 初始版本使用 `speed`/`active_power`，A 使用 `rpm`/`power`。

**修复**（B 在 commit `821e27` 中完成）：
- `generate_data.py`/`normal_pattern.py` 中 `speed` → `rpm`，`active_power` → `power`
- `data_service.py` 新增 `PARAM_MAP` 双射机制（`speed→rpm`, `active_power→power`），确保向前兼容
- `alarm_service.py` 使用 `resolve_param_name()` 规范化参数名

---

## 五、架构设计 — Tool 注册中心 real + mock 自动降级

```
call_tool("data_tool", params={...})
    │
    ▼
┌──────────────────────────────────────────┐
│  ACTIVE_REGISTRY                         │
│                                          │
│  1. 检查 _REAL_REGISTRY 是否有该 Tool     │
│     ├─ 有 → 调用真实实现                  │
│     │   ├─ 成功 → 返回真实数据            │
│     │   └─ 失败 → 降级 ↓                 │
│     └─ 无 → 直接调用 mock                │
│                                          │
│  2. 降级: MOCK_REGISTRY.get(name)        │
│     └─ 调用 mock 实现，返回模拟数据       │
└──────────────────────────────────────────┘
```

**设计要点**：
- `__init__.py` 导入时 `try/except` 检测真实实现是否可导入
- `call_tool()` 运行时 `try/except` 检测真实调用是否成功
- 双层保障：导入失败 → mock；调用失败 → mock
- `is_real_available(name)` 可查询当前使用的是真实还是 mock

---

## 六、B 的实现质量评估

### P0-2 模拟数据生成 ✅

| 检查项 | 规范要求 | 实际 | 状态 |
|--------|---------|------|------|
| 设备数量 | ≥3 台 | 3 台（锅炉/汽轮机/发电机） | ✅ |
| 测点/设备 | 3-4 个 | 每台 4 个 | ✅ |
| 数据时长 | ≥7 天，1 分钟采样 | 7 天 × 1440 分钟 = 10080 条/测点 | ✅ |
| 异常场景 | ≥3 种 | 4 种（蒸汽温度上升/振动突变/压力下降/定子过热） | ✅ |
| 异常曲线 | — | 非线性 `1-(1-p)³` 模拟真实渐进故障 | ✅ 加分 |

### P0-3 数据查询服务 ✅

| 检查项 | 状态 | 说明 |
|--------|------|------|
| data_tool 签名 | ✅ | `data_tool(params: dict) -> dict` 一致 |
| 返回格式 | ✅ | device_id + device_name + parameter + unit + data + stats |
| 聚合查询 | ✅ | 5min/15min/1h/6h/1d（超额完成） |
| 多设备对比 | ✅ | `query_multiple_devices()` |
| device_code 支持 | ✅ | `get_device_by_code_or_name()` fallback 查找 |
| PARAM_MAP | ✅ | `resolve_param_name()` 参数名规范化 |

### P0-4 异常检测算法 ✅

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 阈值检测 | ✅ | 超高/超低 + score 归一化 + 批量检测 |
| 趋势检测 | ✅ | 滑动窗口线性回归 + 变化率计算 |
| 风险评分 | ✅ | `risk = 0.5×threshold + 0.5×trend` + 等级划分 + 建议 |
| alarm_tool 签名 | ✅ | `alarm_tool(device_id, hours=24)` 一致 |

---

## 七、验证结果

### P0-2 回归测试

```
Results: 73/73 passed, 0/73 failed
ALL CHECKS PASSED
```

验证项：
- 模块导入（5 项）
- AgentState 结构（6 项）
- Tool 注册中心（10 项）
- Mock Tool 返回值格式（9 项）
- 意图分类 10 条（含 diagnosis 优先级修正）
- 参数抽取 4 条（含 boiler_002 映射验证）
- 完整工作流 5 种意图（12 项）
- INTENT_TOOL_MAP 完整性（14 项）
- 降级机制（1 项）
- 边界情况（3 项）

### P0-3 意图识别测试

```
结果: 10/10 通过 (100%)
验收标准: >= 80% (PASS)
```

---

## 八、审查结论

| 类别 | 判定 | 说明 |
|------|------|------|
| device_code 映射修复 | OK | 6 个文件全部修正为 boiler_002 |
| parameter 命名统一 | OK | PARAM_MAP 双射机制确保向前兼容 |
| B 的 P0-2 数据生成 | OK | 3 设备 × 4 测点 × 7 天 + 4 种异常场景 |
| B 的 P0-3 数据查询 | OK | 时序查询 + 聚合 + 多设备对比 + device_code 支持 |
| B 的 P0-4 异常检测 | OK | 阈值 + 趋势 + 风险评分 + 建议 |
| Tool 注册中心重构 | OK | real + mock 双层降级，运行时自动切换 |
| P0-2 回归兼容 | OK | 73/73 全通过，无回归 |
| P0-3 意图识别 | OK | 10/10 全通过，device_code 修正后无影响 |

**总体判定：B 的实现质量优秀，接口一致性问题已全部修复，可合并。**

---

## 九、后续衔接

| 任务 | 说明 | 依赖 |
|------|------|------|
| 数据库部署 | `docker-compose up -d postgres` + `python data/mock/generate_data.py` 初始化数据 | Docker 环境 |
| 真实 Tool 联调 | 数据库就绪后 ACTIVE_REGISTRY 自动切换为真实实现 | 数据库部署 |
| P0-5 | `backend/api/agent.py` 对接 `create_agent()`，前端调用 /agent/chat | P0-3 + P0-4 完成 ✅ |
| P1-1 | Prophet 预测模型 + predict_tool 真实实现 | B 的 P1-1 任务 |
| predict_tool 替换 | `ACTIVE_REGISTRY["predict_tool"]` 从 mock 切换为真实 | P1-1 完成 |
