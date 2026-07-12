
# API Specification

## 1. 基本规则

系统模块之间通过 HTTP API 通信。

统一规范：

- 协议：HTTP
- 数据格式：JSON
- URL格式：

/api/v1/{模块}/{功能}


示例：

/api/v1/agent/diagnose


---

## 2. 请求规范

请求格式：

{
    "参数名": "参数值"
}


示例：

{
    "device_id": "A001",
    "time": "2026-01-01"
}


---

## 3. 返回规范

统一返回：

{
    "success": true,
    "message": "说明信息",
    "data": {}
}


---

## 4. 接口定义模板


## 接口名称：

xxx接口


## 功能：

描述接口作用


## 请求：

METHOD:

GET / POST


URL:

/api/v1/xxx


输入：

|参数|类型|说明|
|-|-|-|
| | | |


## 输出：

|参数|类型|说明|
|-|-|-|
| | | |


## 调用方：

xxx模块


## 负责人：

xxx



---

# 5. 接口列表

|接口|功能|负责人|状态|
|-|-|-|-|
| | | | |
=======
# API Specification

## 1. 基本规则

系统模块之间通过 HTTP API 通信。

统一规范：

- 协议：HTTP
- 数据格式：JSON
- URL格式：

/api/v1/{模块}/{功能}


示例：

/api/v1/agent/diagnose


---

## 2. 请求规范

请求格式：

{
    "参数名": "参数值"
}


示例：

{
    "device_id": "A001",
    "time": "2026-01-01"
}


---

## 3. 返回规范

统一返回：

{
    "success": true,
    "message": "说明信息",
    "data": {}
}


---

## 4. 接口定义模板


## 接口名称：

xxx接口


## 功能：

描述接口作用


## 请求：

METHOD:

GET / POST


URL:

/api/v1/xxx


输入：

|参数|类型|说明|
|-|-|-|
| | | |


## 输出：

|参数|类型|说明|
|-|-|-|
| | | |


## 调用方：

xxx模块


## 负责人：

xxx



---

# 5. 接口列表

|接口|功能|负责人|状态|
|-|-|-|-|
| | | | |

| 接口 | Method | URL | 功能 | 负责人 | 状态 |
|------|--------|-----|------|--------|------|
| 健康检查 | GET | `/api/v1/health` | 服务存活检测 | A | ✅ 已完成 |
| Agent 对话 | POST | `/api/v1/agent/chat` | 用户自然语言输入 → Agent 返回诊断结果 | A | 🔨 Week 2 |
| 实时遥测 | GET | `/api/v1/telemetry/live` | 获取设备实时参数 | A（封装 B 的 data_tool） | ⏳ Week 3 |
| 告警列表 | GET | `/api/v1/alarm/list` | 查询告警记录 | A（封装 B 的 alarm_tool） | ⏳ Week 3 |
| 诊断报告 | GET | `/api/v1/report/latest` | 获取最新诊断报告 | A | ⏳ Week 5 |