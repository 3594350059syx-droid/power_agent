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

MySQL

用途：

- 用户信息
- 设备信息
- 告警记录
- 诊断结果
- 系统日志


## 时序数据库

InfluxDB（可选）

用途：

- 温度
- 压力
- 转速
- 流量
- 电气参数

等连续变化数据。



---

# 3. 数据库结构


## 3.1 设备信息表 device


用途：

存储电厂设备基础信息。


字段：

|字段|类型|说明|
|-|-|-|
|id|int|设备ID|
|device_name|string|设备名称|
|device_type|string|设备类型|
|location|string|设备位置|
|status|string|运行状态|
|create_time|datetime|创建时间|



示例：
锅炉1号
汽轮机2号
发电机3号


---

## 3.2 设备运行数据表 device_data


用途：

存储设备实时运行参数。


字段：

|字段|类型|说明|
|-|-|-|
|id|int|数据ID|
|device_id|int|设备ID|
|temperature|float|温度|
|pressure|float|压力|
|speed|float|转速|
|value_time|datetime|采集时间|



数据来源：

传感器 / 模拟数据



---

## 3.3 告警信息表 alarm


用途：

保存异常检测产生的告警。


字段：

|字段|类型|说明|
|-|-|-|
|id|int|告警ID|
|device_id|int|设备ID|
|level|string|告警等级|
|message|string|告警内容|
|alarm_time|datetime|时间|
|status|string|处理状态|



告警等级：

- LOW
- MEDIUM
- HIGH



---

## 3.4 故障诊断结果表 diagnosis


用途：

保存 Agent 分析结果。


字段：

|字段|类型|说明|
|-|-|-|
|id|int|结果ID|
|alarm_id|int|关联告警|
|fault_type|string|故障类型|
|reason|string|原因分析|
|suggestion|string|处理建议|
|create_time|datetime|生成时间|



---

## 3.5 Agent任务记录表 agent_task


用途：

记录智能体执行过程。


字段：

|字段|类型|说明|
|-|-|-|
|id|int|任务ID|
|task_type|string|任务类型|
|input|string|输入内容|
|output|string|输出结果|
|status|string|执行状态|
|create_time|datetime|时间|



---
# 4. 数据关系



设备(device)

  |
  |

运行数据(device_data)

  |
  |

告警(alarm)

  |
  |

诊断结果(diagnosis)

设备

  |
  |

Agent任务(agent_task)



---

# 5. 数据流



传感器数据

  ↓

device_data

  ↓

异常检测模型

  ↓

alarm

  ↓

Agent诊断

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
