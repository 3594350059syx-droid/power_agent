# B 成员 — Week 2 开发任务

## 上周回顾

| 任务 | 状态 | 说明 |
|------|------|------|
| P0-1 数据库设计 | ✅ 完成 | `init.sql` 五张表（device / sensor_point / timeseries_data / alarm_record / diagnosis_result），TimescaleDB 超表就绪 |
| 与 A 确认 Tool 签名 | ✅ 完成 | data_tool / alarm_tool / predict_tool 函数签名已锁定 |

## 本周目标

**让数据库里有"工业级"数据——生成 7 天模拟电厂运行数据 + 实现数据查询服务。**

```
模拟数据生成 → 写入 TimescaleDB → data_tool 可查询 → A 的 Agent 可调用
```

---

## 任务 1：P0-2 — 生成电厂模拟数据

**截止**：Week 2 周三

### 要做什么

编写 `data/mock/generate_data.py`，一键生成并写入数据库：

**数据规模：**

| 设备 | 测点 | 正常范围 | 采样间隔 | 时长 |
|------|------|---------|---------|------|
| 2号锅炉 (generator_002) | 主蒸汽温度 | 540±15℃ | 1 分钟 | 7 天 |
| | 主蒸汽压力 | 16.7±0.5 MPa | 1 分钟 | 7 天 |
| | 炉膛温度 | 1200±50℃ | 1 分钟 | 7 天 |
| 3号汽轮机 (turbine_003) | 转速 | 3000±50 rpm | 1 分钟 | 7 天 |
| | 轴承温度 | 85±10℃ | 1 分钟 | 7 天 |
| | 振动 | 0.03±0.02 mm | 1 分钟 | 7 天 |
| 4号发电机 (generator_004) | 有功功率 | 300±50 MW | 1 分钟 | 7 天 |
| | 定子温度 | 105±15℃ | 1 分钟 | 7 天 |
| | 无功功率 | 50±20 Mvar | 1 分钟 | 7 天 |

> 预计总数据量：3 设备 × 3 测点 × 7 天 × 1440 点/天 ≈ **90,720 条**

### ⚠️ 必须包含的异常场景

| 场景 | 设备 | 参数 | 时间 | 模拟方式 |
|------|------|------|------|---------|
| 减温水阀故障 | 2号锅炉 | 主蒸汽温度 | 第 4 天 14:00-16:00 | 温度从 540℃ 线性升至 575℃，触发 HIGH 告警 |
| 轴承磨损加剧 | 3号汽轮机 | 振动 | 第 5 天 02:00-06:00 | 振动从 0.03mm 跳变至 0.12mm，持续升高 |
| 正常对比基线 | 全部 | 全部 | 第 1-3 天 | 正常波动数据，供算法对比 |

### 数据生成要点

- 加入随机噪声（正态分布 ± 正常波动范围）
- 时间戳精确到分钟，从 7 天前到当前
- 自动写入 `alarm_record` 表（超过阈值的记录）
- 脚本支持**幂等**：重复运行先清空旧数据再插入

### 产出文件

```
data/mock/
├── generate_data.py      ← 主脚本（一键生成 + 写库）
├── normal_pattern.py     ← 正常数据生成器
├── anomaly_scenarios.py  ← 异常场景注入
└── config.py             ← 设备/测点/阈值配置常量
```

### 验收标准

```bash
python data/mock/generate_data.py
```

```sql
-- 验证 1：数据量
SELECT count(*) FROM timeseries_data;  -- ≥ 90,000 条

-- 验证 2：异常记录
SELECT count(*) FROM alarm_record;     -- ≥ 5 条

-- 验证 3：异常温度确实超过阈值
SELECT max(value) FROM timeseries_data
WHERE sensor_id = (SELECT id FROM sensor_point WHERE point_name = '主蒸汽温度');
-- 应 >= 565℃
```

---

## 任务 2：P0-3 — 实现 data_tool 数据查询服务

**截止**：Week 2 周五

### 要做什么

实现 A 定义的 `data_tool()` 函数——这是 Agent 调用数据库的唯一入口。

```python
def data_tool(params: dict) -> dict:
    """
    输入：
    {
        "device_id": "generator_002",
        "parameter": "steam_temp",
        "start_time": "2026-07-10T00:00:00",
        "end_time": "2026-07-11T00:00:00"
    }

    输出：
    {
        "device_id": "generator_002",
        "parameter": "steam_temp",
        "unit": "℃",
        "data": [
            {"time": "2026-07-10T00:00:00", "value": 540.5},
            {"time": "2026-07-10T00:01:00", "value": 540.8},
            ...
        ],
        "stats": {"min": 535.0, "max": 575.0, "avg": 548.3, "count": 1440}
    }
    """
```

### 技术要求

- 从 PostgreSQL / TimescaleDB 查询
- device_id → 查 device 表 → 关联 sensor_point → 关联 timeseries_data
- 支持时间范围、聚合窗口（可选，本周不强求）
- 无匹配数据时返回空数组而非异常

### 产出文件

```
backend/services/
├── data_service.py       ← data_tool() 主函数
└── query_builder.py      ← SQL 查询构建（可选，直接写 SQL 也行）
```

### 验收标准

```python
from backend.services.data_service import data_tool

# 查询正常数据
result = data_tool({
    "device_id": "generator_002",
    "parameter": "steam_temp",
    "start_time": "2026-07-10T00:00:00",
    "end_time": "2026-07-11T00:00:00"
})

assert len(result["data"]) > 0
assert "stats" in result
assert result["stats"]["max"] >= result["stats"]["min"]

# 查询无数据的时间段
result = data_tool({
    "device_id": "generator_002",
    "parameter": "steam_temp",
    "start_time": "2020-01-01T00:00:00",
    "end_time": "2020-01-02T00:00:00"
})
assert result["data"] == []
```

---

## 本周沟通要点

- **周三前**：完成 P0-2 数据生成，通知 A 数据已就绪
- **周三**：与 A 确认 data_tool mock 返回值格式（A 的 Agent 本周先用 mock 跑通）
- **周五前**：完成 P0-3 data_tool 实现，A 的 Agent 可以真实查库
- **注意**：alarm_tool（P0-4）本周不强求，但如果 P0-2 和 P0-3 提前完成可以开始
