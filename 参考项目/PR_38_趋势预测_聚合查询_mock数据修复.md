# PR #38: 修复趋势预测、TimescaleDB 聚合与 Mock 数据生成审查问题

**类型**：`fix`
**基线提交**：`7f12968`（`fix: PR #38 审查问题修复（幂等性/SQLAlchemy 2.x/异常场景/配置契约）`）
**审查日期**：2026-08-26

---

## 一、背景

PR #38 审查发现以下会影响预测正确性、TimescaleDB 查询可执行性和模拟数据幂等性的缺陷：

1. **sklearn 降级模型时间特征重置**：原实现使用当前 DataFrame 的行号作为 `timestep`。预测未来数据或评估独立测试集时，时间步会从 0 重新开始，线性趋势无法向未来正确外推。
2. **聚合 SQL 对多单位间隔无效**：PostgreSQL 的 `date_trunc` 只接收 `minute`、`hour`、`day` 等字段名，不能处理 `5 minutes`、`6 hours` 等间隔字符串。
3. **Mock 清理范围和外键顺序不完整**：重复生成数据时需要只删除当前 Mock 配置的设备数据，并先清理依赖 `alarm_record` 的诊断记录，避免外键约束失败或误删业务设备数据。
4. **异常窗口依赖分钟偏移**：原异常注入依赖相对分钟偏移，生成起点不是午夜或采样时间带秒数时，异常可能偏离 Week 2 规定的墙钟窗口。

本次修复保持既有 REST API 响应结构不变，并为上述问题补充回归测试。

---

## 二、修改内容

### 2.1 sklearn 连续时间特征与模型持久化

- `extract_features()` 的 `timestep` 改为相对于训练起点的**真实经过分钟数**，不再使用 DataFrame 行号；不规则采样、评估集和未来预测均使用同一时间坐标。
- sklearn 训练时保存 `_feature_time_origin`；预测、残差计算和评估均复用该起点。
- sklearn 模型 pickle 增加 `feature_time_origin` 字段，加载后保持与训练时相同的特征定义。
- 对不含 `feature_time_origin` 的旧 sklearn pickle 明确抛出 `ValueError`，由既有上层加载失败/重训练流程接管，避免静默产生错误预测。
- 统一时区感知与非时区时间戳的原点处理，避免时间相减时的时区不兼容。
- 将已弃用的 `fillna(method='ffill'/'bfill')` 改为 `.ffill().bfill()`。

### 2.2 TimescaleDB 聚合查询

- 将 `aggregate_query()` 的时间分桶由无效的多单位 `date_trunc` 用法替换为：

  ```sql
  time_bucket(CAST('<interval>' AS INTERVAL), recorded_at)
  ```

- 保持 `5min`、`15min`、`1h`、`6h`、`1d` 五种聚合粒度和原返回结构不变。
- 保持 SQLAlchemy 2.x 兼容：直接以 `Session` 构建、分组和排序查询，不使用已移除的 `Query.from_self()`。

### 2.3 Mock 数据清理与外键安全

- 增加 `get_mock_device_ids()`：仅按 `data/mock/config.py` 中的 `DEVICES[*].code` 查询当前 Mock 管理的设备 ID，不依赖硬编码主键。
- 增加 `clear_device_data()`，并在写入新模拟数据前调用，实现重复执行的幂等清理。
- 按外键依赖顺序删除指定设备的数据：

  ```text
  DiagnosisResult → AlarmRecord → TimeseriesData
  ```

- `DiagnosisResult` 直接按 `device_id` 清理，因此 `alarm_id IS NULL` 的 Mock 设备诊断记录也会被删除；非 Mock 设备的数据不会受到影响。

### 2.4 日历化异常窗口

- `ANOMALY_WINDOWS` 从相对分钟偏移改为日历字段：`day_offset`、`start_hour`、`start_minute`、`duration`。
- 数据生成起点改为“当前时间向前 7 天后的午夜”，生成连续 7 天窗口。
- 新增无数据库依赖的 `mock_utils.py`，负责生成起点计算、日历窗口计算和按设备类型分发异常注入。
- 异常注入以数据的最早时间戳为基准，而不是列表第一项，消除数据排序依赖。
- 对带秒数的非午夜采样起点直接传递日历窗口起点，避免原先整分钟偏移截断导致异常在规定窗口前开始。

### 2.5 回归测试

- 验证 sklearn 长时间线性趋势能持续向未来外推。
- 验证独立测试集评估使用训练时间原点。
- 验证 sklearn 保存/加载后保留时间原点且预测一致。
- 验证所有支持的聚合粒度均编译为 PostgreSQL `time_bucket` SQL，且不包含 `date_trunc`。
- 验证 Mock 清理调用顺序、配置设备范围和生成前清理行为。
- 验证非午夜且带秒数的生成起点仍在文档规定的蒸汽温度、振动异常墙钟窗口内。

---

## 三、影响模块

| 模块/文件 | 类型 | 影响说明 |
|---|---|---|
| `algorithms/prediction/model_utils.py` | 修改 | 连续时间特征、时区兼容处理、Pandas 空值填充 API 更新 |
| `algorithms/prediction/prophet_model.py` | 修改 | sklearn 训练原点保存、预测/评估复用、pickle 兼容性保护 |
| `backend/services/data_service.py` | 修改 | 聚合查询改用 TimescaleDB `time_bucket` |
| `data/mock/anomaly_scenarios.py` | 修改 | 注入函数支持显式日历窗口起点 |
| `data/mock/config.py` | 修改 | 异常窗口改为日历字段配置 |
| `data/mock/generate_data.py` | 修改 | Mock 设备范围查询、FK 安全清理、调用日历化注入逻辑 |
| `data/mock/mock_utils.py` | 新增 | 与数据库解耦的生成起点、窗口计算和异常分发工具 |
| `tests/algorithm/test_prediction.py` | 修改 | sklearn 外推、训练原点评估和持久化回归测试 |
| `tests/algorithm/test_data_generation.py` | 修改 | 聚合 SQL、清理范围/顺序及日历窗口回归测试 |

**不涉及**：前端、FastAPI 路由、Agent Tool 入参/出参、数据库表结构和迁移脚本。

---

## 四、接口变化

| 项目 | 变化 | 兼容性与处理方式 |
|---|---|---|
| `extract_features` | 签名从 `extract_features(df)` 扩展为 `extract_features(df, time_origin=None)` | 新参数可选；既有单参数调用保持可用。sklearn 内部调用传入训练起点。 |
| sklearn 模型 pickle | 新增 `feature_time_origin` 持久化字段 | 新模型可正常保存/加载；缺失该字段的旧 sklearn 模型会提示重训练，避免生成错误的重置时间特征。 |
| `ANOMALY_WINDOWS` 配置 | 从分钟偏移改为 `day_offset/start_hour/start_minute/duration` | 直接读取该配置的外部调用方需同步使用新的日历字段；项目内生成入口已完成适配。 |
| 异常注入函数 | `inject_steam_temp_rise`、`inject_vibration_rise` 新增可选 `window_start` | 原有三个位置参数调用保持兼容；日历调度场景可传入精确窗口起点。 |
| 时序聚合 API | HTTP 入参和返回 JSON 结构不变 | 服务端生成的 SQL 从 `date_trunc` 改为 TimescaleDB `time_bucket`；目标库需启用 TimescaleDB 扩展。 |

---

## 五、测试结果

### 5.1 定向回归测试

```powershell
.\.venv\Scripts\python.exe -m unittest tests.algorithm.test_prediction tests.algorithm.test_data_generation -v
```

```text
Ran 45 tests in 0.551s

OK
```

覆盖范围：

- 预测指标、趋势判定、Prophet 不可用时 sklearn 降级；
- sklearn 拟合、未来外推、独立评估、保存/加载；
- 3 台设备 × 3 测点配置契约及 90,720 条数据量口径；
- 主蒸汽温度和振动异常曲线、日历窗口及午夜生成起点；
- Mock 清理范围、外键删除顺序和生成前清理；
- SQLAlchemy 2.x 查询签名和 TimescaleDB 聚合 SQL 构造。

### 5.2 PostgreSQL SQL 方言编译验证

针对 `5min`、`15min`、`1h`、`6h`、`1d` 逐一用 SQLAlchemy PostgreSQL dialect 编译 `time_bucket` 表达式，结果：

```text
Verified PostgreSQL time_bucket SQL for: 5min, 15min, 1h, 6h, 1d
```

每种粒度均包含 `time_bucket` 与预期间隔字符串，且不包含 `date_trunc`。

### 5.3 静态检查

```powershell
.\.venv\Scripts\python.exe -m compileall algorithms backend data tests
git diff --check
```

结果：**通过**。Python 源码可编译，`git diff --check` 未发现空白错误。

### 5.4 全量发现测试说明

此前执行 `python -m unittest discover -s tests -v` 时，受影响模块相关测试均通过；但全量发现仍有一个与本 PR 无关的既有导入错误：

```text
tests/agent/test_intent.py
ModuleNotFoundError: No module named 'agent.prompts'
```

该错误位于 Agent 意图识别测试的模块路径，未修改 `agent/` 目录；本 PR 的 45 项定向回归测试全部通过。

---

## 六、风险与验证边界

| 项目 | 状态 | 说明 |
|---|---|---|
| 真正的 TimescaleDB 执行 | 待集成验证 | 当前已验证 SQLAlchemy PostgreSQL SQL 构造；尚无本地 PostgreSQL/TimescaleDB 服务执行 `time_bucket`。 |
| 真实外键清理 | 待集成验证 | 已由 Mock Session 验证删除范围和顺序；需在实际数据库中验证外键约束及全量重跑幂等性。 |
| 旧 sklearn 模型 | 需要重训练 | 缺失 `feature_time_origin` 的历史模型会被拒绝加载，这是避免错误预测的有意兼容性策略。 |
| API 调用方 | 无 REST 变更 | HTTP 路由、请求字段和响应 JSON 未变；仅内部聚合 SQL 和 Mock 配置字段发生调整。 |

建议在具备数据库服务的环境追加执行：

```powershell
docker-compose up -d postgres
.\.venv\Scripts\python.exe data\mock\generate_data.py
.\.venv\Scripts\python.exe data\mock\generate_data.py
```

并验证：

1. 五种聚合粒度的 `time_bucket` 查询均可执行；
2. 两次 Mock 数据生成之间不存在外键错误或重复数据；
3. 非 Mock 设备的 `DiagnosisResult`、`AlarmRecord`、`TimeseriesData` 不会被清理。

---

## 七、审查结论

| 检查项 | 结果 | 说明 |
|---|---|---|
| sklearn 趋势外推 | ✅ | 训练、评估、预测及加载后预测共享连续时间原点。 |
| 旧模型安全性 | ✅ | 缺少新时间原点字段的旧 sklearn 模型会触发重训练路径。 |
| TimescaleDB 聚合语法 | ✅（SQL 编译） | 五种支持粒度均构造为 `time_bucket(INTERVAL, recorded_at)`。 |
| Mock 清理范围 | ✅（单元测试） | 仅按配置中的设备编码解析并清理对应设备。 |
| 外键删除顺序 | ✅（单元测试） | `DiagnosisResult → AlarmRecord → TimeseriesData`。 |
| 异常日历窗口 | ✅ | 非午夜、带秒数的采样起点不会使异常提前进入窗口。 |
| 回归测试 | ✅ | 定向测试 45/45 通过。 |
| 真实数据库联调 | ⏳ | 需在 PostgreSQL/TimescaleDB 环境完成最终验证。 |

**结论：代码级审查项和定向回归测试已完成；在具备 TimescaleDB 服务的环境补充集成验证后可合并。**