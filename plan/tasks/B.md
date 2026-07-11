# B 成员开发任务文档

## 1. 角色定位

**工业数据与算法负责人**

你是项目的"工业灵魂"。你需要让这个系统不只是"聊天机器人"，而是一个真正能分析工业数据的智能系统。你负责：
- PostgreSQL + TimescaleDB 数据库设计与实现
- 电厂模拟数据生成（正常 + 异常场景）
- 多策略异常检测算法
- 时序预测模型（LSTM / Prophet）
- 模型自适应优化 Demo

## 2. MVP 目标

实现以下数据链路：

```
模拟工业数据生成
  → 写入 TimescaleDB
  → 数据查询接口（供 A 的 Agent 调用）
  → 异常检测算法（阈值 + 趋势）
  → 返回异常结果给 A
```

MVP 验收标准：**A 的 Agent 能通过 data_tool 查到你的数据库数据，通过 alarm_tool 获得异常检测结果。**

## 3. 具体开发任务

---

### P0-1: 设计并创建 PostgreSQL + TimescaleDB 数据库

**技术方案**：
- PostgreSQL 15+ 数据库
- TimescaleDB 扩展用于时序数据
- 5 张表：`device`, `sensor_point`, `timeseries_data`（超表）, `alarm_record`, `diagnosis_result`
- 使用 `init.sql` 脚本一键初始化

**涉及目录**：
```
data/database/
├── init.sql              ← 数据库建表脚本
├── seed_data.sql         ← 初始数据（设备、测点定义）
└── schema_design.md      ← 表结构说明（可选）
backend/database/
├── connection.py         ← 数据库连接池
└── models.py             ← SQLAlchemy ORM 模型
```

**输入依赖**：无（基础搭建）

**输出结果**：

`init.sql` 核心内容：
```sql
-- 设备表
CREATE TABLE device (
    id SERIAL PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    location VARCHAR(200),
    status VARCHAR(20) DEFAULT 'running',
    create_time TIMESTAMPTZ DEFAULT NOW()
);

-- 测点定义表
CREATE TABLE sensor_point (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES device(id),
    point_name VARCHAR(100) NOT NULL,
    unit VARCHAR(20),
    normal_min DOUBLE PRECISION,
    normal_max DOUBLE PRECISION,
    threshold_high DOUBLE PRECISION,
    threshold_low DOUBLE PRECISION
);

-- 时序数据超表
CREATE TABLE timeseries_data (
    id BIGSERIAL,
    device_id INTEGER REFERENCES device(id),
    sensor_id INTEGER REFERENCES sensor_point(id),
    value DOUBLE PRECISION NOT NULL,
    quality VARCHAR(10) DEFAULT 'good',
    recorded_at TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('timeseries_data', 'recorded_at');

-- 告警记录表
CREATE TABLE alarm_record (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES device(id),
    sensor_id INTEGER REFERENCES sensor_point(id),
    alarm_type VARCHAR(50),
    severity VARCHAR(10),
    current_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    triggered_at TIMESTAMPTZ DEFAULT NOW()
);
```

**验收标准**：
```bash
docker-compose up -d postgres
psql -h localhost -U postgres -d power_agent -f data/database/init.sql
# 5 张表创建成功，timeseries_data 确认为超表
```

---

### P0-2: 生成电厂模拟数据

**技术方案**：
- Python 脚本生成 CSV / 直接写库
- 至少 3 台设备：2号锅炉、3号汽轮机、4号发电机
- 每台设备 3-4 个测点：
  - 锅炉：主蒸汽温度(540±15℃)、主蒸汽压力(16.7±0.5MPa)、炉膛温度(1200±50℃)
  - 汽轮机：转速(3000±50rpm)、轴承温度(85±10℃)、振动(0.03±0.02mm)
  - 发电机：有功功率(300±50MW)、定子温度(105±15℃)
- 数据时长：至少 7 天，1 分钟采样间隔（约 10080 条/测点）
- 必须包含异常场景（供 P0-3 验证）：
  - 某天下午主蒸汽温度从 540℃ 逐步升至 575℃（减温水故障模拟）
  - 某天凌晨轴承振动突然从 0.03mm 升至 0.12mm
  - 正常日作为对比基线

**涉及目录**：
```
data/mock/
├── generate_data.py      ← 模拟数据生成脚本
├── normal_pattern.py     ← 正常数据模式
├── anomaly_scenarios.py  ← 异常场景定义
└── output/               ← 生成的 CSV 文件
```

**输入依赖**：数据库已就绪（P0-1）

**输出结果**：
- `data/mock/output/` 下生成 CSV 文件
- 或在 `generate_data.py` 中直接写入 TimescaleDB

**验收标准**：
```python
python data/mock/generate_data.py
# 执行后：
# SELECT count(*) FROM timeseries_data; → >= 100000 条
# SELECT count(*) FROM alarm_record; → >= 5 条异常记录
```

---

### P0-3: 实现数据查询服务 + data_tool 函数

**技术方案**：
- 实现 A 定义的 `data_tool()` 函数签名
- 支持：按设备+参数+时间区间查询
- 支持：聚合查询（5min/15min/1h 窗口）
- 支持：多设备对比查询

**涉及目录**：
```
backend/services/
├── data_service.py       ← 数据查询业务逻辑
└── query_builder.py      ← 动态 SQL 查询构建
```

**输入依赖**：
- 数据库（P0-1）已建表
- 模拟数据（P0-2）已入库
- A 的 Tool 接口规范（`agent/tools/base.py`）

**输出结果**：
```python
# data_tool(params) 函数
def data_tool(params: dict) -> dict:
    # params = {"device_id": "generator_002", "parameter": "steam_temp",
    #           "start_time": "2026-07-10T00:00:00", "end_time": "2026-07-11T00:00:00"}
    # 查询 TimescaleDB，返回结构化数据
    return {
        "device_id": "generator_002",
        "parameter": "steam_temp",
        "unit": "℃",
        "data": [{"time": "...", "value": 540.5}, ...],
        "stats": {"min": 535.0, "max": 575.0, "avg": 548.3, "count": 1440}
    }
```

**验收标准**：
```python
from backend.services.data_service import data_tool
result = data_tool({
    "device_id": "generator_002",
    "parameter": "steam_temp",
    "start_time": "2026-07-10T00:00:00",
    "end_time": "2026-07-11T00:00:00"
})
assert len(result["data"]) > 0
assert "stats" in result
```

---

### P0-4: 实现异常检测算法 + alarm_tool 函数

**技术方案**：
- 至少实现 **阈值异常** + **趋势异常** 两种检测
- 阈值异常：实际值 > threshold_high 或 < threshold_low
- 趋势异常：滑动窗口内线性回归斜率 > 阈值（如 10 分钟内温度上涨 > 10℃）
- 综合风险评分：`risk = 0.5 * threshold_score + 0.5 * trend_score`
- 实现 A 定义的 `alarm_tool()` 函数签名

**涉及目录**：
```
algorithms/anomaly_detection/
├── __init__.py
├── threshold_detector.py   ← 阈值异常检测
├── trend_detector.py       ← 趋势异常检测
└── risk_scorer.py          ← 综合风险评分
backend/services/
└── alarm_service.py        ← 告警服务封装（内部调用 algorithms/）
```

**输入依赖**：
- 数据查询（P0-3）可用
- 模拟数据包含异常场景

**输出结果**：
```python
def alarm_tool(device_id: str, hours: int = 24) -> dict:
    return {
        "device_id": "generator_002",
        "risk_score": 0.85,
        "alarms": [
            {
                "type": "threshold",
                "parameter": "steam_temp",
                "current_value": 565.0,
                "threshold": 550.0,
                "severity": "high",
                "triggered_at": "2026-07-10T14:30:00"
            },
            {
                "type": "trend",
                "parameter": "steam_temp",
                "trend_desc": "过去30分钟上升15.2℃",
                "slope": 0.51,
                "severity": "medium"
            }
        ]
    }
```

**验收标准**：
```python
result = alarm_tool("generator_002", hours=24)
assert result["risk_score"] > 0.5  # 模型中预设了异常场景
assert len(result["alarms"]) >= 1
```

---

### P1-1: 实现时序预测模型 + predict_tool 函数

**技术方案**：
- MVP 阶段优先使用 **Prophet**（轻量，易集成）
- P2 阶段可选 LSTM
- 输入历史 N 小时数据，输出未来 M 小时预测
- 实现 A 定义的 `predict_tool()` 函数签名

**涉及目录**：
```
algorithms/prediction/
├── __init__.py
├── prophet_model.py      ← Prophet 预测封装
└── model_utils.py        ← 数据预处理工具
```

**输入依赖**：
- 数据查询（P0-3）可用
- requirements.txt 添加 `prophet`

**输出结果**：
```python
def predict_tool(device_id: str, parameter: str, hours: int = 6) -> dict:
    return {
        "predictions": [
            {"time": "2026-07-11T01:00:00", "value": 545.2},
            {"time": "2026-07-11T02:00:00", "value": 548.1},
            ...
        ],
        "trend": "rising",
        "confidence": 0.92
    }
```

**验收标准**：
```python
result = predict_tool("generator_002", "steam_temp", hours=6)
assert len(result["predictions"]) == 6
assert result["trend"] in ["rising", "falling", "stable"]
```

---

### P1-2: 实现模型自适应优化 Demo

**技术方案**：
- 模拟两个工况：高负荷(>280MW) / 低负荷(<280MW)
- 分别训练两个 Prophet 模型
- 根据当前工况自动切换模型
- 简单 RMSE 对比

**涉及目录**：
```
algorithms/evaluation/
├── __init__.py
├── model_selector.py     ← 工况识别 + 模型切换
└── metrics.py            ← RMSE/MAE 计算
```

**输入依赖**：预测模型（P1-1）可用

**输出结果**：
```python
# 模型选择器
model = select_model_by_condition(device_id="generator_002")
# 返回 model_high.pkl 或 model_low.pkl
# 给出 RMSE 评价
```

**验收标准**：演示不同工况下自动选择不同模型文件，输出 RMSE 对比

---

### P2-1: 扩展异常检测类型

**技术方案**：
- 增加波动异常检测（标准差超阈值）
- 增加预测残差异常（预测值 vs 实际值偏差）
- 风险评分升级为 4 因子加权

**涉及目录**：
```
algorithms/anomaly_detection/
├── volatility_detector.py
└── residual_detector.py
```

**验收标准**：4 种检测类型全部可用，综合风险评分输出正确

---

## 4. 开发流程

### 阶段 1：环境准备（Week 1 前两天）
- **做什么**：安装 PostgreSQL + TimescaleDB，创建数据库，安装 Python 依赖
- **沟通对象**：无
- **产出文件**：数据库就绪，`requirements.txt` 补充 `psycopg2`, `sqlalchemy`, `prophet`, `pandas`, `numpy`, `scikit-learn`

### 阶段 2：接口确认（Week 1 后三天）
- **做什么**：与 A 确认 `data_tool()`, `alarm_tool()`, `predict_tool()` 函数签名
- **沟通对象**：A（Tool 接口规范）
- **产出文件**：确认的接口文档

### 阶段 3：模块开发（Week 2-4）
- **做什么**：P0-1 → P0-2 → P0-3 → P0-4 顺序执行
- **沟通对象**：A（对接测试）、D（数据格式对齐）
- **产出文件**：数据库 + 数据 + 查询 + 检测全部代码

### 阶段 4：本地测试（Week 4 末尾）
- **做什么**：确认 A 能成功调用 data_tool 和 alarm_tool
- **沟通对象**：A（调用方测试）
- **产出文件**：测试通过确认

### 阶段 5：提交 GitHub（持续）
- **做什么**：每完成一个 P0 任务 commit + push
- **沟通对象**：A（Code Review）
- **产出文件**：feature 分支 + PR

### 阶段 6：联调（Week 5-6）
- **做什么**：确保 A 的 Agent 能正确调用所有 Tool，数据返回到前端
- **沟通对象**：A + C
- **产出文件**：联调通过记录

---

## 5. 与 D 协作的数据格式约定

故障案例库中每条案例需包含（D 负责整理，B 确认工业合理性）：

```json
{
  "case_id": "F001",
  "device_type": "boiler",
  "fault_type": "steam_temp_high",
  "symptoms": "主蒸汽温度持续升高，超过550℃",
  "causes": ["减温水流量不足", "调节阀异常"],
  "suggestions": ["检查减温水系统", "调整阀门开度"],
  "related_parameters": ["steam_temp", "water_flow"],
  "severity": "high"
}
```
