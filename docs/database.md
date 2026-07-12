
# Database Design

## 1. 数据库说明

本系统用于存储电厂设备运行数据、告警信息、故障诊断结果以及系统运行日志。

数据库设计遵循：

- 数据采集与业务数据分离
- 支持历史数据查询
- 支持模型训练与故障分析
- 支持 Agent 智能推理


---

# 2. 数据库选型


## 业务数据库

PostgreSQL

用途：

- 用户信息
- 设备信息
- 告警记录
- 诊断结果
- 系统日志


## 时序数据库

TimescaleDB（基于 PostgreSQL 扩展）

用途：

- 温度
- 压力
- 转速
- 流量
- 电气参数

等连续变化数据。

利用 TimescaleDB 的超表（Hypertable）特性实现自动分区和高效时序查询。

## 向量数据库

FAISS（Demo阶段）/ Milvus（扩展）

用途：

- 故障知识库向量存储
- RAG 检索



---

# 3. 数据库结构


## 3.1 设备信息表 device


用途：

存储电厂设备基础信息。


字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | SERIAL PRIMARY KEY | 设备ID |
| device_name | VARCHAR(100) | 设备名称 |
| device_type | VARCHAR(50) | 设备类型 |
| location | VARCHAR(200) | 设备位置 |
| status | VARCHAR(20) | 运行状态 |
| create_time | TIMESTAMP DEFAULT NOW() | 创建时间 |



示例：
锅炉1号
汽轮机2号
发电机3号


---

## 3.2 设备运行数据表 device_data（TimescaleDB 超表）

用途：

存储设备实时运行参数，使用 TimescaleDB Hypertable。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGSERIAL | 数据ID |
| device_id | INTEGER REFERENCES device(id) | 设备ID |
| temperature | DOUBLE PRECISION | 温度 |
| pressure | DOUBLE PRECISION | 压力 |
| speed | DOUBLE PRECISION | 转速 |
| value_time | TIMESTAMPTZ NOT NULL | 采集时间 |

超表创建：

SELECT create_hypertable('device_data', 'value_time');

数据来源：

传感器 / 模拟数据 / MQTT 实时推送


---


## 3.3 告警信息表 alarm

用途：

保存异常检测产生的告警。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | SERIAL PRIMARY KEY | 告警ID |
| device_id | INTEGER REFERENCES device(id) | 设备ID |
| level | VARCHAR(10) | 告警等级 |
| message | TEXT | 告警内容 |
| alarm_time | TIMESTAMPTZ DEFAULT NOW() | 时间 |
| status | VARCHAR(20) DEFAULT 'pending' | 处理状态 |

告警等级：

- LOW
- MEDIUM
- HIGH


---


## 3.4 故障诊断结果表 diagnosis

用途：

保存 Agent 分析结果。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | SERIAL PRIMARY KEY | 结果ID |
| alarm_id | INTEGER REFERENCES alarm(id) | 关联告警 |
| fault_type | VARCHAR(100) | 故障类型 |
| reason | TEXT | 原因分析 |
| suggestion | TEXT | 处理建议 |
| create_time | TIMESTAMPTZ DEFAULT NOW() | 生成时间 |


---


## 3.5 Agent任务记录表 agent_task

用途：

记录智能体执行过程。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | SERIAL PRIMARY KEY | 任务ID |
| task_type | VARCHAR(50) | 任务类型 |
| input | TEXT | 输入内容 |
| output | TEXT | 输出结果 |
| status | VARCHAR(20) | 执行状态 |
| create_time | TIMESTAMPTZ DEFAULT NOW() | 时间 |


---


# 4. 数据关系

device (设备)
|
|
device_data (运行数据)
|
|
alarm (告警)
|
|
diagnosis (诊断结果)

device
|
|
agent_task (Agent任务)


---


# 5. 数据流

传感器 / MQTT

↓

device_data (TimescaleDB超表)

↓

异常检测模型

↓

alarm

↓

Agent诊断 + FAISS 知识检索

↓

diagnosis

↓

前端展示


---


# 6. 后续扩展

未来可以增加：

- 用户权限表
- 模型版本表
- 知识库表
- 维修记录表
- 历史案例库
- Milvus 向量库迁移
=======
# Database Design

## 1. 数据库说明

本系统用于存储电厂设备运行数据、告警信息、故障诊断结果以及系统运行日志。

数据库设计遵循：

- 数据采集与业务数据分离
- 支持历史数据查询
- 支持模型训练与故障分析
- 支持 Agent 智能推理


---

# 2. 数据库选型


## 业务数据库

PostgreSQL

用途：

- 用户信息
- 设备信息
- 告警记录
- 诊断结果
- 系统日志


## 时序数据库

TimescaleDB（基于 PostgreSQL 扩展）

用途：

- 温度
- 压力
- 转速
- 流量
- 电气参数

等连续变化数据。

利用 TimescaleDB 的超表（Hypertable）特性实现自动分区和高效时序查询。

## 向量数据库

FAISS（Demo阶段）/ Milvus（扩展）

用途：

- 故障知识库向量存储
- RAG 检索



---

# 3. 数据库结构


## 3.1 设备信息表 device


用途：

存储电厂设备基础信息。


字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | SERIAL PRIMARY KEY | 设备ID |
| device_name | VARCHAR(100) | 设备名称 |
| device_type | VARCHAR(50) | 设备类型 |
| location | VARCHAR(200) | 设备位置 |
| status | VARCHAR(20) | 运行状态 |
| create_time | TIMESTAMP DEFAULT NOW() | 创建时间 |



示例：
锅炉1号
汽轮机2号
发电机3号


---

## 3.2 设备运行数据表 device_data（TimescaleDB 超表）

用途：

存储设备实时运行参数，使用 TimescaleDB Hypertable。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGSERIAL | 数据ID |
| device_id | INTEGER REFERENCES device(id) | 设备ID |
| temperature | DOUBLE PRECISION | 温度 |
| pressure | DOUBLE PRECISION | 压力 |
| speed | DOUBLE PRECISION | 转速 |
| value_time | TIMESTAMPTZ NOT NULL | 采集时间 |

超表创建：

SELECT create_hypertable('device_data', 'value_time');

数据来源：

传感器 / 模拟数据 / MQTT 实时推送


---


## 3.3 告警信息表 alarm

用途：

保存异常检测产生的告警。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | SERIAL PRIMARY KEY | 告警ID |
| device_id | INTEGER REFERENCES device(id) | 设备ID |
| level | VARCHAR(10) | 告警等级 |
| message | TEXT | 告警内容 |
| alarm_time | TIMESTAMPTZ DEFAULT NOW() | 时间 |
| status | VARCHAR(20) DEFAULT 'pending' | 处理状态 |

告警等级：

- LOW
- MEDIUM
- HIGH


---


## 3.4 故障诊断结果表 diagnosis

用途：

保存 Agent 分析结果。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | SERIAL PRIMARY KEY | 结果ID |
| alarm_id | INTEGER REFERENCES alarm(id) | 关联告警 |
| fault_type | VARCHAR(100) | 故障类型 |
| reason | TEXT | 原因分析 |
| suggestion | TEXT | 处理建议 |
| create_time | TIMESTAMPTZ DEFAULT NOW() | 生成时间 |


---


## 3.5 Agent任务记录表 agent_task

用途：

记录智能体执行过程。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | SERIAL PRIMARY KEY | 任务ID |
| task_type | VARCHAR(50) | 任务类型 |
| input | TEXT | 输入内容 |
| output | TEXT | 输出结果 |
| status | VARCHAR(20) | 执行状态 |
| create_time | TIMESTAMPTZ DEFAULT NOW() | 时间 |


---


# 4. 数据关系

device (设备)
|
|
device_data (运行数据)
|
|
alarm (告警)
|
|
diagnosis (诊断结果)

device
|
|
agent_task (Agent任务)


---


# 5. 数据流

传感器 / MQTT

↓

device_data (TimescaleDB超表)

↓

异常检测模型

↓

alarm

↓

Agent诊断 + FAISS 知识检索

↓

diagnosis

↓

前端展示


---


# 6. 后续扩展

未来可以增加：

- 用户权限表
- 模型版本表
- 知识库表
- 维修记录表
- 历史案例库
- Milvus 向量库迁移

