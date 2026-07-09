# 电厂智能预警与故障诊断 Agent 系统 — 完整设计文档

> **赛题**: A15 · 和利时 | **定位**: 工业设备智能辅助诊断助手  
> **核心原则**: 弱工业知识 + 强AI能力 — 把工程师解决问题的流程数字化  
> **Demo 主线**: 报警 → 分析 → 诊断 → 建议 → 模型迭代 → 全场景追溯

---

## 一、项目定位与核心闭环

### 1.1 一句话定位

> 系统模拟电厂锅炉现场异常场景，通过 Agent 自主调用数据分析、趋势预测和知识检索工具，辅助值班工程师快速定位故障原因并生成维护建议，同时具备工况自适应模型迭代能力。

### 1.2 核心闭环（扩展版）

```
                    ┌──────────────────────────────┐
                    │     模型自适应迭代（后台）       │
                    │  工况感知 → 数据选取 → 重训练    │
                    └──────────┬───────────────────┘
                               │ 模型更新
                               ▼
  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
  │  报警    │───→│  分析    │───→│  诊断    │───→│  建议    │───→│ 全场景   │
  │ 5类预警  │    │ 趋势+钻取 │    │ RAG推理  │    │ 操作指导 │    │ 问答追溯  │
  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └──────────┘
       │              │               │               │              │
       └──────────────┴───────────────┴───────────────┴──────────────┘
                                    │
                            ┌───────┴───────┐
                            │   历史预警统计  │
                            │ 频次/时长/报告  │
                            └───────────────┘
```

### 1.3 角色定义

| 角色 | 职责 | Demo 中体现 |
|------|------|------------|
| 值班工程师 | 监控设备状态、处理报警、查询历史、判断原因、执行操作 | 交互输入方 |
| 监盘 Agent | 自动解析指令、调度工具、分析数据、推理诊断 | 系统核心 |
| 知识库 | 提供运行规程、故障案例、操作指导 | RAG 源 |
| 时序模型 | 趋势预测、异常检测、工况识别 | 后台服务 |

---

## 二、系统整体架构

### 2.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| Agent 编排 | LangGraph (Python) | 有状态工作流，工具调用，human-in-the-loop |
| LLM | DeepSeek API (deepseek-chat) | 自然语言理解、指令解析、RAG推理、报告生成 |
| 语音识别 | OpenAI Whisper (本地) | 语音转文字，离线可用 |
| 时序建模 | Darts (LSTM/ARIMA) + scikit-learn | 预测+异常检测+工况分类 |
| 知识库/RAG | LangChain RAG + ChromaDB | 文档解析、向量检索、上下文增强 |
| 后端 API | FastAPI (Python) | RESTful 接口，WebSocket 推送 |
| 前端 | React + ECharts | SPA，趋势图/仪表盘/统计面板 |
| 数据存储 | SQLite（模拟） + ChromaDB（向量） | 结构化数据 + 向量知识 |
| 运行环境 | Python 原生（开发期）/ Docker（展示期） | 快速原型 → 稳定交付 |

### 2.2 架构分层图

```
┌──────────────────────────────────────────────────────────┐
│                    前端界面 (React)                       │
│  指令输入区 │ 数据展示区 │ 预警提示区 │ 报告查看区 │ 日志追溯区  │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────┴─────────────────────────────────┐
│                  FastAPI 后端服务                         │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ 指令解析  │ 数据服务  │ 预警服务  │ 诊断服务  │ 问答追溯     │
│ 路由      │ 路由      │ 路由      │ 路由      │ 路由        │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴──────┬──────┘
     │          │          │          │            │
┌────┴──────────┴──────────┴──────────┴────────────┴──────┐
│              LangGraph Agent 编排层                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ StateGraph:                                      │   │
│  │  parse_cmd → query_data → trend_analysis         │   │
│  │  → alert_judge → fault_diagnosis → gen_report    │   │
│  │  → (condition) → model_retrain → qa_session       │   │
│  └──────────────────────────────────────────────────┘   │
└────┬──────────┬──────────┬──────────┬───────────────────┘
     │          │          │          │
┌────┴────┐ ┌──┴───┐ ┌───┴───┐ ┌───┴──────┐
│ SQLite  │ │Darts │ │ChromaDB│ │ Whisper  │
│ 模拟数据 │ │ 时序 │ │ 知识库 │ │ 语音识别  │
└─────────┘ └──────┘ └────────┘ └──────────┘
```

---

## 三、模块一：语音 + 快捷键 + 自然语言三模态交互

### 3.1 设计目标

| 指标 | 要求 |
|------|------|
| 自然语言解析准确率 | ≥ 90% |
| 语音识别准确率 | ≥ 85% |
| 指令响应延迟 | ≤ 2 秒 |

### 3.2 三模态交互方案

```
┌─────────────────────────────────────────────────────────┐
│                    输入层                                │
├───────────────┬───────────────┬─────────────────────────┤
│  语音输入      │  快捷键输入     │  自然语言文本输入          │
│  (麦克风)      │  (键盘组合键)   │  (文本框)                │
└───────┬───────┴───────┬───────┴─────────────┬───────────┘
        │               │                     │
        ▼               ▼                     ▼
  ┌──────────┐   ┌────────────┐    ┌──────────────────┐
  │ Whisper  │   │ 快捷键映射表 │    │  直接文本         │
  │ 语音→文字 │   │ Ctrl+1..9  │    │                  │
  └────┬─────┘   └──────┬─────┘    └────────┬─────────┘
       │                │                    │
       └────────────────┼────────────────────┘
                        │ 统一文本
                        ▼
              ┌─────────────────────┐
              │  LLM 指令解析器      │
              │  (DeepSeek)         │
              │  提取结构化参数：     │
              │  · 机组/设备         │
              │  · 参数名称          │
              │  · 时间范围          │
              │  · 阈值/条件         │
              │  · 意图分类          │
              └──────────┬──────────┘
                         ▼
                  ┌──────────────┐
                  │  Agent 调度   │
                  └──────────────┘
```

### 3.3 语音模块实现路径

```python
# 技术方案：Whisper 本地模型 + 流式处理
# 依赖：openai-whisper

# 伪代码结构
class VoiceService:
    def __init__(self):
        self.model = whisper.load_model("base")  # 或 small，平衡速度与精度
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        # 1. 音频预处理：降噪、重采样至 16kHz
        # 2. Whisper 推理
        # 3. 返回文本
        result = self.model.transcribe(audio_buffer)
        return result["text"]
```

**关键注意**：
- 电厂术语（如"省煤器""过热器""炉膛负压"）需在 Whisper 词表基础上，通过 prompt 注入专业词汇表提升准确率
- 备选方案：百度语音 API（联网环境更稳定，但需费用）

### 3.4 快捷键映射方案

| 快捷键 | 功能 | 预设指令 |
|--------|------|---------|
| `Ctrl+1` | 查询当前温度 | "查询A锅炉出口温度当前值" |
| `Ctrl+2` | 查看温度趋势 | "显示A锅炉过去6小时温度趋势" |
| `Ctrl+3` | 预测温度走势 | "预测A锅炉未来3小时温度" |
| `Ctrl+4` | 查看最新预警 | "显示最近5条预警信息" |
| `Ctrl+5` | 故障诊断 | "诊断当前异常原因" |
| `Ctrl+6` | 查看安全规程 | "A锅炉温度异常的安全操作规程" |
| `Ctrl+7` | 预警统计 | "生成本月预警统计报告" |
| `Ctrl+8` | 查看监盘日志 | "显示今日监盘操作日志" |
| `Ctrl+9` | 自由输入 | 聚焦到文本输入框 |

### 3.5 指令解析 Prompt 设计

```
你是一个电厂监盘指令解析器。用户输入可能包含设备、参数、时间和阈值信息。

请从用户输入中提取以下结构化信息（JSON格式）：
{
  "intent": "query_data | trend_analysis | alert_check | fault_diagnosis | knowledge_qa | prediction | report",
  "equipment": "设备名称，如A锅炉、B汽轮机",
  "parameters": ["参数列表，如出口温度、主蒸汽压力"],
  "time_range": {"start": "...", "end": "..."},
  "threshold_condition": "阈值条件，如 超过75℃",
  "original_query": "原始用户输入"
}

示例输入："A锅炉出口温度突然升高到85度，帮我分析原因"
示例输出：{
  "intent": "fault_diagnosis",
  "equipment": "A锅炉",
  "parameters": ["出口温度"],
  "time_range": {"start": "auto_recent_6h", "end": "now"},
  "threshold_condition": "超过75℃",
  "original_query": "A锅炉出口温度突然升高到85度，帮我分析原因"
}
```

---

## 四、模块二：五类预警体系与关联分析

### 4.1 设计目标

| 指标 | 要求 |
|------|------|
| 预警识别覆盖率 | ≥ 95% |
| 预警趋势研判准确率 | ≥ 85% |

### 4.2 五类预警定义与检测逻辑

```
┌─────────────────────────────────────────────────────────────────┐
│                      五类预警体系                                 │
├──────────┬──────────────────────┬───────────────────────────────┤
│ 预警类型   │ 定义                  │ 检测方法                        │
├──────────┼──────────────────────┼───────────────────────────────┤
│ 1.阈值预警 │ 参数超出正常范围        │ 实时值 > 上限 OR 实时值 < 下限    │
│          │ 例：温度 > 75℃         │ rule_engine: simple_threshold    │
├──────────┼──────────────────────┼───────────────────────────────┤
│ 2.变化速率 │ 参数变化速度异常        │ |Δvalue/Δtime| > rate_limit     │
│   预警    │ 例：温度上升 > 2℃/min   │ rule_engine: rate_of_change      │
├──────────┼──────────────────────┼───────────────────────────────┤
│ 3.波动预警 │ 参数在短时间内剧烈振荡    │ rolling_std > threshold          │
│          │ 例：压力波动 > ±5%       │ statistical: rolling_window_std   │
├──────────┼──────────────────────┼───────────────────────────────┤
│ 4.残差预警 │ 实测值与模型预测值偏差过大  │ |actual - predicted| > 3σ      │
│          │ 例：实际值偏离预测值 15%   │ model_based: residual_analysis   │
├──────────┼──────────────────────┼───────────────────────────────┤
│ 5.故障预警 │ 设备停机信号或组合异常    │ 离散信号 = FAULT                 │
│          │ 例：锅炉熄火信号触发       │ rule_engine: discrete_signal     │
└──────────┴──────────────────────┴───────────────────────────────┘
```

### 4.3 预警关联分析：实时值 / 预测值 / 设定值 三角分析

这是 A15 明确要求的核心分析逻辑：

```
                    设定值（额定值）
                    e.g. 70℃ (目标工况)
                       │
                       │ 偏差分析
                       ▼
    ┌──────────────────┬──────────────────┐
    │   实时值         │   预测值           │
    │   (当前传感器)    │   (模型输出)       │
    │   e.g. 85℃      │   e.g. 82℃       │
    └────────┬─────────┴────────┬─────────┘
             │                  │
             └────────┬─────────┘
                      │
                  残差 = |实时值 - 预测值|
                  e.g. |85 - 82| = 3℃
                      │
                      ▼
              ┌────────────────┐
              │ 残差 > 3σ ?    │
              │ → 模型失效预警  │
              │ → 触发模型迭代  │
              └────────────────┘
```

**实现方式**：

```python
class AlertCorrelationAnalyzer:
    """
    对每条预警，同时提取三个维度分析：
    1. 实时值 vs 设定值 → 偏差程度
    2. 实时值 vs 预测值 → 残差分析（判断模型是否失效）
    3. 预测值 vs 设定值 → 趋势风险（预测未来是否会超标）
    """
    
    def analyze(self, param_name: str, 
                realtime_value: float,
                predicted_value: float,
                setpoint: float,
                threshold_upper: float,
                threshold_lower: float) -> AlertAnalysis:
        
        analysis = AlertAnalysis()
        
        # 维度1：实时值偏离设定值
        analysis.deviation_from_setpoint = (realtime_value - setpoint) / setpoint
        
        # 维度2：残差 = |实际 - 预测|
        analysis.residual = abs(realtime_value - predicted_value)
        
        # 维度3：预测趋势风险
        analysis.future_risk = (predicted_value - setpoint) / setpoint
        
        # 综合研判
        analysis.severity = self._assess_severity(analysis)
        analysis.recommend_action = self._recommend(analysis)
        
        return analysis
```

### 4.4 预警流程：从检测到推送

```
模拟传感器数据 (SQLite，每秒更新) 
        │
        ▼
┌───────────────────┐
│  预警检测引擎       │  ← 每 5 秒轮询
│  (5 类规则并行)     │
└────────┬──────────┘
         │ 触发预警
         ▼
┌───────────────────┐
│  预警去重 + 分级    │  ← 同参数 10 分钟内不重复
│  (严重/警告/提示)   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  关联分析           │  ← 实时值/预测值/设定值三角
│  + 趋势研判         │
└────────┬──────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│前端推送│ │存入DB │
│WebSocket│ │预警表 │
└───────┘ └───────┘
```

### 4.5 模拟数据设计（SQLite）

```sql
-- 设备实时数据表
CREATE TABLE realtime_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT NOT NULL,      -- 'boiler_A', 'boiler_B', 'turbine_1'
    parameter_name TEXT NOT NULL,    -- 'outlet_temp', 'steam_pressure', 'feed_water_flow'
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 预警记录表
CREATE TABLE alert_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT NOT NULL,
    parameter_name TEXT NOT NULL,
    alert_type TEXT NOT NULL,        -- 'threshold', 'rate_change', 'fluctuation', 'residual', 'fault'
    severity TEXT NOT NULL,          -- 'critical', 'warning', 'info'
    realtime_value REAL,
    predicted_value REAL,
    setpoint_value REAL,
    threshold_upper REAL,
    threshold_lower REAL,
    alert_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    acknowledged INTEGER DEFAULT 0,  -- 是否已确认
    resolved INTEGER DEFAULT 0       -- 是否已解决
);

-- 模拟数据生成：正常范围 + 随机噪声 + 注入异常
-- 温度正常范围 60-75℃，偶尔注入 80-90℃ 的异常值
-- 正常时波动 ±2℃，异常时持续上升
```

---

## 五、模块三：模型自适应迭代

### 5.1 设计目标

| 指标 | 要求 |
|------|------|
| 工况识别准确率 | ≥ 90% |
| 迭代后模型准确率提升 | ≥ 10% |

### 5.2 什么是"工况变化"？（电厂锅炉场景）

在大赛中，可以简化定义为三种典型工况：

| 工况类型 | 特征 | 触发条件示例 |
|---------|------|-------------|
| **稳态运行** | 参数稳定在设定值附近，波动小 | 负荷不变，温度波动 < ±3% |
| **负荷调整** | 参数有序升降，跟随负荷指令 | 负荷指令变化 > 10%，各参数同步变化 |
| **异常状态** | 参数偏离正常范围，模型预测失准 | 残差连续 > 3σ，或触发阈值预警 |

### 5.3 工况感知方案

```python
class OperatingConditionDetector:
    """
    工况感知器：基于滑动窗口统计特征 + 简单规则 → 识别三种工况
    
    技术路线：
    - 对过去 30 分钟数据，计算：均值、标准差、变化趋势（线性回归斜率）
    - 规则分类：
        · |斜率| < 0.1 且 std < 阈值  → 稳态
        · |斜率| ≥ 0.1 且残差 < 3σ    → 负荷调整
        · 残差 ≥ 3σ 或 触发阈值预警    → 异常
    
    1.0 版本：规则分类（简单可靠，满足 90% 准确率）
    2.0 版本（可选）：LSTM 分类器（加分项）
    """
    
    def __init__(self, window_size=30):  # 30分钟窗口
        self.window_size = window_size
    
    def detect(self, history_data: pd.DataFrame) -> str:
        # 计算统计特征
        stats = self._compute_stats(history_data)
        
        # 规则判断
        if stats['residual_ratio'] > 0.15:  # 残差超标
            return 'abnormal'
        elif abs(stats['trend_slope']) > 0.1:
            return 'load_change'
        else:
            return 'steady'
    
    def _compute_stats(self, data):
        return {
            'mean': data['value'].mean(),
            'std': data['value'].std(),
            'trend_slope': np.polyfit(range(len(data)), data['value'], 1)[0],
            'residual_ratio': abs(data['value'].iloc[-1] - data['predicted'].iloc[-1]) / data['value'].std()
        }
```

### 5.4 自动重训练方案

```
┌──────────────────────────────────────────────────────────┐
│              模型自适应迭代流程                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐                                        │
│  │  工况感知器    │ ← 每 5 分钟运行一次                      │
│  └──────┬───────┘                                        │
│         │ 检测到工况变化 OR 残差持续超标                     │
│         ▼                                                │
│  ┌──────────────┐     ┌─────────────────┐                │
│  │  触发条件判断  │────→│ 满足重训练条件？  │──否──→ 跳过     │
│  └──────┬───────┘     └────────┬────────┘                │
│         │ 是                   │                         │
│         ▼                      ▼                         │
│  ┌──────────────────────────────────────┐                │
│  │  自动选取训练数据                      │                │
│  │  · 选取最近 7 天相似工况的数据          │                │
│  │  · 数据清洗：去异常点、插值缺失值        │                │
│  │  · 特征工程：滞后特征、滚动统计          │                │
│  └────────────────┬─────────────────────┘                │
│                   │                                      │
│                   ▼                                      │
│  ┌──────────────────────────────────────┐                │
│  │  模型重训练                            │                │
│  │  · LSTM：定长序列预测（滑动窗口构造）    │                │
│  │  · ARIMA：趋势+季节性分解               │                │
│  │  · 超参：自动网格搜索（简化版）           │                │
│  └────────────────┬─────────────────────┘                │
│                   │                                      │
│                   ▼                                      │
│  ┌──────────────────────────────────────┐                │
│  │  准确率验证                            │                │
│  │  · 测试集 MAE/MAPE 对比                │                │
│  │  · 新模型 MAE vs 旧模型 MAE            │                │
│  │  · 提升 ≥ 10% → 替换模型               │                │
│  │  · 提升 < 10% → 保留旧模型 + 日志记录    │                │
│  └────────────────┬─────────────────────┘                │
│                   │                                      │
│                   ▼                                      │
│  ┌──────────────┐                                        │
│  │  模型版本管理  │ ← 保存为新版本，旧版本归档               │
│  └──────────────┘                                        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 5.5 LSTM/ARIMA 实现路径

```python
# ============= LSTM 方案 =============
# 适用场景：多变量、复杂非线性关系
# 框架：PyTorch + Darts

from darts.models import RNNModel
from darts import TimeSeries

class LSTMPredictor:
    def __init__(self, seq_length=60):  # 用过去 60 个时间步预测未来
        self.seq_length = seq_length
        self.model = None
    
    def train(self, series: TimeSeries):
        """初始训练 or 重训练"""
        self.model = RNNModel(
            model='LSTM',
            hidden_dim=20,
            n_rnn_layers=2,
            output_length=12,  # 预测未来 12 步（1小时）
            n_epochs=50,
            batch_size=32
        )
        self.model.fit(series)
    
    def predict(self, series: TimeSeries, n_steps: int = 12):
        return self.model.predict(n=n_steps, series=series)
    
    def evaluate(self, test_series: TimeSeries) -> float:
        """返回 MAE，用于 10% 提升验证"""
        forecast = self.model.predict(n=len(test_series), series=test_series)
        from darts.metrics import mae
        return mae(test_series, forecast)


# ============= ARIMA 方案（备用/对比） =============
# 适用场景：单变量、线性趋势、快速训练

from darts.models import ARIMA

class ARIMAPredictor:
    def __init__(self):
        self.model = None
    
    def train(self, series: TimeSeries):
        self.model = ARIMA(p=5, d=1, q=0)  # 简化版自动定阶
        self.model.fit(series)
    
    def predict(self, series: TimeSeries, n_steps: int = 12):
        return self.model.predict(n=n_steps)


# ============= 准确率 10% 提升验证 =============
def verify_improvement(old_model, new_model, test_data) -> dict:
    """
    验证重训练后模型准确率提升是否 ≥ 10%
    返回验证报告，用于前端展示 + 日志记录
    """
    old_forecast = old_model.predict(test_data)
    new_forecast = new_model.predict(test_data)
    
    from darts.metrics import mae, mape
    
    old_mae = mae(test_data, old_forecast)
    new_mae = mae(test_data, new_forecast)
    
    improvement = (old_mae - new_mae) / old_mae * 100
    
    return {
        "old_mae": round(old_mae, 4),
        "new_mae": round(new_mae, 4),
        "improvement_pct": round(improvement, 2),
        "pass_threshold": improvement >= 10.0,
        "model_replaced": improvement >= 10.0
    }
```

### 5.6 模型版本管理（SQLite）

```sql
CREATE TABLE model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT NOT NULL,
    parameter_name TEXT NOT NULL,
    model_type TEXT NOT NULL,          -- 'LSTM' or 'ARIMA'
    version_number INTEGER NOT NULL,
    model_path TEXT NOT NULL,          -- 模型文件路径
    train_data_start DATETIME,
    train_data_end DATETIME,
    mae_score REAL,
    operating_condition TEXT,          -- 训练时工况
    is_active INTEGER DEFAULT 0,       -- 是否当前生效
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retrain_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT,
    trigger_reason TEXT,               -- 'condition_change' or 'residual_over_threshold'
    old_model_version INTEGER,
    new_model_version INTEGER,
    old_mae REAL,
    new_mae REAL,
    improvement_pct REAL,
    replaced INTEGER,                  -- 是否替换
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 六、模块四：历史预警统计报告

### 6.1 设计目标

> 自动归集历史预警数据，完成预警频次、持续时长的量化统计与对比分析，生成统计报告。

### 6.2 统计维度

| 统计维度 | 说明 | 示例输出 |
|---------|------|---------|
| **按预警类型分布** | 各类预警占比 | 阈值预警 45%，变化速率预警 20%，波动预警 15% |
| **按设备分布** | 各设备预警数量排名 | A锅炉 23次，B汽轮机 15次 |
| **按时间段分布** | 日/周/月预警趋势 | 本周预警数较上周下降 12% |
| **按严重程度分布** | 严重/警告/提示 占比 | 严重 5%，警告 45%，提示 50% |
| **预警持续时间** | 从触发到解决的平均时间 | 平均处理时长 23 分钟 |
| **高频预警 TOP5** | 最频繁触发的预警 | A锅炉出口温度超限（本月 18 次） |
| **趋势对比** | 本月 vs 上月对比 | 预警总数：本月 87 次 vs 上月 102 次 ↓14.7% |

### 6.3 数据流

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ alert_records │────→│ AlertStatsService│────→│  统计报告     │
│   (SQLite)    │     │  (Python 聚合)    │     │  (JSON/PDF)  │
└──────────────┘     └────────┬────────┘     └──────┬───────┘
                              │                      │
                              ▼                      ▼
                     ┌────────────────┐    ┌────────────────┐
                     │  ECharts 图表   │    │  自然语言摘要    │
                     │  饼图/柱状图/   │    │  (LLM 生成)     │
                     │  折线图/热力图  │    │  "本月预警总数   │
                     └────────────────┘    │   87次，较上月  │
                                           │   下降14.7%..." │
                                           └────────────────┘
```

### 6.4 报告生成 — LLM 自然语言摘要

```python
class AlertReportGenerator:
    """
    统计数据 → LLM 生成自然语言报告摘要
    """
    
    REPORT_PROMPT = """你是一个电厂监盘数据分析师。根据以下统计数据，生成一份简洁的预警月报摘要（200字以内）。

统计数据：
- 总预警次数：{total_alerts}
- 按类型分布：{type_distribution}
- 按设备分布：{equipment_distribution}
- 严重预警次数：{critical_count}
- 平均处理时长：{avg_duration}分钟
- 与上月对比：{month_over_month_change}

请用自然、专业的语气，包含：
1. 本月总体情况一句话
2. 最值得关注的异常（高频预警或严重预警）
3. 与上月对比的趋势判断
4. 一条简短建议
"""
    
    async def generate_summary(self, stats: dict, llm) -> str:
        prompt = self.REPORT_PROMPT.format(**stats)
        response = await llm.ainvoke(prompt)
        return response.content
```

### 6.5 前端展示设计

```
┌────────────────────────────────────────────────────────┐
│  预警统计报告 — 2026年7月                                │
├────────────────────┬───────────────────────────────────┤
│                    │                                   │
│   [饼图]           │   [柱状图]                         │
│   预警类型分布      │   每日预警数量趋势                   │
│                    │                                   │
├────────────────────┴───────────────────────────────────┤
│                                                       │
│   [水平柱状图]                                          │
│   各设备预警数量排名                                      │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│   📊 AI 摘要：                                          │
│   本月共触发预警87次，较上月（102次）下降14.7%。           │
│   A锅炉出口温度超限预警最为频繁（18次），建议重点关注       │
│   冷却系统运行状态。严重预警占比5%，均已在30分钟内处理。    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 七、模块五：全场景问答

### 7.1 设计目标

> 覆盖监盘操作、设备参数、安全规程、系统逻辑四类场景，自动记录问答历史，与监盘日志联动追溯。

### 7.2 四类场景定义

| 场景分类 | 典型问题示例 | 数据来源 | 技术方式 |
|---------|-------------|---------|---------|
| **监盘操作** | "怎么查看A锅炉的实时温度？""如何确认预警？" | 操作手册、系统介绍文档 | RAG 检索 |
| **设备参数** | "A锅炉的正常运行温度范围是多少？""主蒸汽压力额定值？" | 设备参数表、运行规程 | RAG 检索 + 结构化查询 |
| **安全规程** | "温度超标的三级处置流程是什么？""紧急停炉的条件？" | 安全规程文档、应急预案 | RAG 检索 |
| **系统逻辑** | "预警检测多久运行一次？""模型什么时候会自动重训练？" | 系统设计文档、技术说明 | RAG 检索 + 系统元信息 |

### 7.3 知识库构建

```
knowledge/
├── equipment/
│   ├── boiler_spec.txt          # 锅炉规格参数
│   ├── boiler_operation.txt     # 锅炉运行规程
│   └── boiler_fault_cases.txt   # 锅炉典型故障案例
├── safety/
│   ├── emergency_procedure.txt  # 应急处置规程
│   └── safety_limits.txt        # 安全限值表
├── monitoring/
│   ├── monitoring_guide.txt     # 监盘操作指南
│   └── parameter_reference.txt  # 参数参考表
└── system/
    ├── system_architecture.txt  # 系统架构说明
    └── model_description.txt   # 模型说明
```

**知识条目示例（boiler_fault_cases.txt）**：

```
## 故障案例 1：锅炉出口温度异常升高

**故障现象**：
锅炉出口温度持续升高，超过正常范围（60-75℃），升温速率 > 2℃/min。

**可能原因（按概率排序）**：
1. 冷却水循环系统故障（概率 60%）
   - 冷却水泵停机或效率下降
   - 冷却水管道堵塞
2. 燃烧系统异常（概率 25%）
   - 燃料供给过量
   - 风煤比失调
3. 温度传感器故障（概率 10%）
   - 传感器漂移或损坏
4. 炉膛结焦（概率 5%）
   - 长期高负荷运行导致

**排查步骤**：
1. 确认温度传感器读数是否正常（对比相邻测点）
2. 检查冷却水循环泵运行状态和进出口压差
3. 检查燃料供给量和风量配比
4. 检查炉膛负压和烟气温度

**处理措施**：
1. 若冷却系统故障：切换备用泵，通知检修
2. 若燃烧异常：调整风煤比，降低负荷
3. 若传感器故障：切换备用测点，标记故障传感器
4. 若炉膛结焦：安排吹灰操作

**参考依据**：
《火电厂集控运行规程》第5.3节
```

### 7.4 RAG 问答技术方案

```
用户问题："A锅炉温度超标应该怎么处理？"
        │
        ▼
┌───────────────────┐
│  Query 重写        │  ← LLM 将口语化问题改写为检索友好形式
│  "锅炉出口温度异常  │
│   升高处理措施"      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  向量检索           │  ← ChromaDB 检索 top-k 相关文档
│  embedding:        │
│  text2vec-large-   │
│  chinese           │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Rerank + 过滤     │  ← 根据场景标签过滤，优先返回匹配场景的文档
│  (场景标签匹配)     │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  LLM 生成回答      │  ← DeepSeek 基于检索上下文生成答案
│  + 引用来源标注     │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  存入问答历史表     │  ← 与监盘日志联动
│  qa_history        │
└───────────────────┘
```

### 7.5 问答追溯：与监盘日志联动

```sql
-- 问答历史表
CREATE TABLE qa_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_query TEXT NOT NULL,
    intent_category TEXT,             -- 'monitoring', 'equipment', 'safety', 'system'
    retrieved_docs TEXT,              -- 检索到的知识文档 ID 列表
    llm_response TEXT NOT NULL,
    related_alert_id INTEGER,         -- 关联的预警 ID（如果有）
    related_log_id INTEGER,           -- 关联的监盘日志 ID（如果有）
    session_id TEXT,                  -- 会话 ID，用于追溯完整对话链
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 监盘操作日志表
CREATE TABLE monitoring_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator TEXT NOT NULL,           -- 操作者（人 or Agent）
    action_type TEXT NOT NULL,        -- 'query_data', 'acknowledge_alert', 'diagnose', 'export_report'
    action_detail TEXT,               -- 操作详情 JSON
    equipment_id TEXT,
    related_alert_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**追溯逻辑**：
- 用户在查看某条预警时发起问答 → `qa_history.related_alert_id` 关联该预警
- Agent 自动执行数据查询 → 写入 `monitoring_log`
- 回放时：按时间线串联 `monitoring_log` + `qa_history` + `alert_records`，形成完整操作链

---

## 八、模块六：前端界面五大分区设计

### 8.1 布局方案

```
┌──────────────────────────────────────────────────────────────┐
│  🏭 电厂智能预警与故障诊断 Agent 系统          [🔊语音] [⚙设置] │
├────────────┬─────────────────────────┬──────────────────────┤
│            │                         │                      │
│  ①         │  ②                      │  ③                   │
│  指令输入区 │  数据展示区               │  预警提示区            │
│            │                         │                      │
│  ┌───────┐ │  ┌───────────────────┐  │  🔴 A锅炉温度超限     │
│  │文本输入│ │  │                   │  │     当前85℃ > 75℃   │
│  │.......│ │  │   趋势曲线图        │  │  🟡 B汽轮机振动警告   │
│  └───────┘ │  │   (ECharts)       │  │  🟢 C水泵流量偏低     │
│            │  │                   │  │                      │
│  快捷键:    │  └───────────────────┘  │  [查看全部预警 →]     │
│  Ctrl+1 查 │                         │                      │
│  Ctrl+2 看 │  ┌───────────────────┐  │                      │
│  Ctrl+3 预 │  │  预测 vs 实际      │  │                      │
│  ...       │  │  (ECharts 双线)    │  │                      │
│            │  └───────────────────┘  │                      │
│  [发送]    │                         │                      │
│  [🎤语音]  │                         │                      │
│            │                         │                      │
├────────────┴─────────────────────────┴──────────────────────┤
│                                                             │
│  ④  报告查看区                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  [故障诊断报告] [预警统计报告] [模型迭代报告] [操作日志]      ││
│  │                                                         ││
│  │  当前展示：故障诊断报告                                     ││
│  │  ┌───────────────────────────────────────────────────┐  ││
│  │  │ AI 诊断结果...                                     │  ││
│  │  └───────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⑤  日志追溯区                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 时间线：                                                 ││
│  │ 14:23  用户查询 A锅炉温度                                 ││
│  │ 14:23  Agent 调用数据查询工具                             ││
│  │ 14:24  系统触发阈值预警                                    ││
│  │ 14:24  用户请求故障诊断                                    ││
│  │ 14:25  Agent RAG检索 → 生成诊断建议                       ││
│  │ 14:26  用户确认预警 + 查看操作指导                          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 五大分区功能详述

**① 指令输入区**（左侧栏，固定 280px 宽）

| 组件 | 说明 |
|------|------|
| 文本输入框 | 多行输入，支持 Enter 发送，Shift+Enter 换行 |
| 语音按钮 | 点击开始录音，Whisper 实时转写，再次点击停止并发送 |
| 快捷键面板 | 展示 9 个预设快捷键 + 功能说明，可自定义 |
| 历史指令 | 最近 5 条输入的快捷回填 |
| 意图指示灯 | LLM 解析完成后，显示识别到的意图（查询/诊断/预测/问答） |

**② 数据展示区**（中间主区域，弹性宽度）

| 组件 | 说明 |
|------|------|
| 实时数据卡片 | 温度、压力、流量、振动 4 个核心参数，当前值 + 设定值 + 状态标识 |
| 趋势曲线图 | ECharts 折线图，默认展示过去 6 小时，支持拖拽缩放时间范围 |
| 预测对比图 | 双线图：实际值（实线）vs 模型预测值（虚线），标注残差异常区间 |
| 数据钻取 | 点击曲线上的点 → 弹出浮层展示该时刻的明细数据 |
| 时段对比 | 选择两个时间段 → 双图并排对比 |

**③ 预警提示区**（右侧栏，固定 300px 宽）

| 组件 | 说明 |
|------|------|
| 预警列表 | 按严重程度排序（🔴严重 → 🟡警告 → 🟢提示），每条预警显示：设备、参数、当前值、阈值、触发时间 |
| 预警详情 | 点击某条预警 → 展开关联分析（实时值/预测值/设定值三角） |
| 确认/解决按钮 | 每条预警可点击确认，确认后记录操作日志 |
| 预警统计入口 | 链接跳转到报告查看区 → 预警统计报告 |

**④ 报告查看区**（下方左半部分）

| Tab 页签 | 内容 |
|---------|------|
| 故障诊断报告 | Agent 诊断结果：可能原因（概率排序）、排查步骤、操作指导、知识库引用 |
| 预警统计报告 | 图表 + AI 摘要，支持按日/周/月切换，支持导出 PDF |
| 模型迭代报告 | 最近一次重训练详情：触发原因、旧模型 MAE、新模型 MAE、提升比例、是否替换 |
| 操作日志 | 按时间倒序展示所有操作记录 |

**⑤ 日志追溯区**（下方右半部分）

| 功能 | 说明 |
|------|------|
| 时间线视图 | 垂直时间线，串联用户操作 + Agent 动作 + 预警事件 |
| 联动高亮 | 点击时间线中的事件 → 对应的预警/报告/数据图联动高亮 |
| 筛选 | 按操作类型、设备、时间段筛选 |
| 导出 | 导出为 PDF/Excel 供复盘 |

### 8.3 前端技术选型

| 需求 | 选型 | 原因 |
|------|------|------|
| 框架 | React 18 + TypeScript | 生态丰富，组件库成熟 |
| UI 组件库 | Ant Design 5 | 适合后台管理系统，表格/表单/Tabs 完善 |
| 图表 | ECharts 5 + echarts-for-react | 时序图、仪表盘、饼图、柱状图均支持 |
| 实时通信 | WebSocket (socket.io) | 预警推送、实时数据更新 |
| 语音录音 | MediaRecorder API | 浏览器原生，无需额外依赖 |
| 快捷键 | react-hotkeys-hook | 轻量级快捷键绑定 |
| 状态管理 | Zustand | 轻量，适合中等复杂度应用 |

---

## 九、完整数据流

### 9.1 一次典型交互的完整数据流

```
时间线：值班工程师处理一次锅炉温度异常

T=0s   用户点击🎤语音："A锅炉出口温度突然升高到85度，帮我分析原因"
        │
T=0.5s 前端 MediaRecorder 录音 → 发送音频到后端
        │
T=1.5s Whisper 语音转文字 → "A锅炉出口温度突然升高到85度，帮我分析原因"
        │
T=2.0s LLM 指令解析 → {"intent":"fault_diagnosis","equipment":"A锅炉","parameters":["出口温度"]}
        │
T=2.0s Agent 开始执行 StateGraph 流程：
        │
T=2.1s ├─ 节点1: query_realtime_data
        │    → SQLite 查询 A锅炉出口温度 = 85℃
        │    → WebSocket 推送到前端 ②数据展示区
        │
T=2.5s ├─ 节点2: trend_analysis  
        │    → SQLite 查询过去 6h 历史数据
        │    → 计算趋势：持续上升，斜率 = +3.2℃/h
        │    → ECharts 渲染 ②趋势曲线
        │
T=3.0s ├─ 节点3: predict_future  
        │    → 调用活跃 LSTM 模型预测未来 3h
        │    → 预测值：88→91→95℃
        │    → ECharts 渲染 ②预测对比图
        │
T=3.2s ├─ 节点4: alert_judge  
        │    → 5类预警引擎检测：
        │    → ✅ 阈值预警触发（85 > 75）
        │    → ✅ 变化速率预警触发（上升过快）
        │    → 写入 alert_records 表
        │    → WebSocket 推送 ③预警提示区
        │
T=3.5s ├─ 节点5: fault_diagnosis  
        │    → RAG 检索 boiler_fault_cases.txt
        │    → 检索到匹配案例："锅炉出口温度异常升高"
        │    → LLM 推理：冷却系统故障概率60%，建议...
        │    → 写入 qa_history 表
        │    → 渲染 ④故障诊断报告
        │
T=4.0s ├─ 节点6: gen_action_guide  
        │    → LLM 生成标准化操作指导
        │    → "1.检查冷却循环泵 2.确认传感器状态 3.降低负荷至70%"
        │    → 渲染 ④报告查看区
        │
T=4.2s └─ 节点7: log_operation  
             → 全流程写入 monitoring_log
             → 渲染 ⑤日志追溯区时间线

T=4.5s 整体响应完成，用户看到完整诊断结果 + 操作建议
```

### 9.2 模型自适应迭代的独立数据流（后台异步）

```
T=每5分钟  后台定时任务触发
        │
        ▼
┌────────────────────┐
│ 工况感知器运行       │
│ 检测最近30min数据    │
└───────┬────────────┘
        │
    ┌───┴───┐
    ▼       ▼
  稳态    非稳态
  (跳过)    │
           ▼
  ┌─────────────────┐
  │ 残差是否连续超标?  │
  │ 连续5个点 > 3σ    │
  └────┬───────┬────┘
       │是      │否
       ▼        ▼
  ┌────────┐  跳过
  │触发重训练│
  └───┬────┘
      │
      ▼
  ┌─────────────────────┐
  │ 1. 选取最近7天相似    │
  │    工况数据           │
  │ 2. 清洗 + 特征工程    │
  │ 3. LSTM/ARIMA 重训练 │
  │ 4. 测试集验证        │
  │ 5. 提升 ≥ 10%?      │
  └──────┬──────┬───────┘
         │是    │否
         ▼      ▼
    替换模型   保留旧模型
         │      │
         └──────┘
            │
            ▼
    ┌──────────────┐
    │ 记录 retrain_logs │
    │ 推送通知给前端    │
    └──────────────┘
```

---

## 十、开发阶段规划（3人团队 × 8周）

### 10.1 阶段划分

```
第1周：需求对齐 + 知识准备
├── 确定 Demo 脚本（精确到秒的演示流程）
├── 构建 knowledge/ 知识库（至少 6 个文档文件）
├── 设计 SQLite 数据库表结构
└── 生成模拟数据（至少覆盖 3 种工况 × 7 天）

第2-3周：核心后端
├── FastAPI 项目骨架搭建
├── LLM 指令解析器（Prompt + DeepSeek API）
├── 数据查询服务（SQLite CRUD）
├── 预警检测引擎（5类预警规则）
└── LangGraph Agent 流程编排（主流程 StateGraph）

第4周：时序模型
├── Darts LSTM 模型训练（初始模型）
├── ARIMA 模型训练（备用）
├── 工况感知器实现
└── 模型重训练 + 10% 提升验证流程

第5周：RAG 知识库 + 问答
├── ChromaDB 知识库初始化 + 文档向量化
├── RAG 问答链路（检索 → Rerank → 生成）
├── 问答历史 + 追溯联动
└── LLM 报告生成（预警统计摘要、故障诊断报告）

第6周：语音 + 前端
├── Whisper 集成 + 音频接口
├── React 项目初始化 + 五大分区布局
├── ECharts 图表组件开发
├── WebSocket 实时推送
└── 快捷键绑定

第7周：联调 + 优化
├── 端到端流程联调
├── 性能优化（响应时间达标）
├── 异常场景处理
└── UI/UX 打磨

第8周：文档 + 演示
├── 演示视频录制（按 Demo 脚本）
├── 项目文档编写（方案文档 + 使用手册）
├── PPT 制作
└── 最终测试 + Bug 修复
```

### 10.2 三人分工建议

| 成员 | 职责 | 关键技术 |
|------|------|---------|
| **成员A（后端+Agent）** | FastAPI、LangGraph 编排、预警引擎、模型迭代 | Python, LangGraph, Darts, SQLite |
| **成员B（AI+知识库）** | LLM 指令解析、RAG 知识库、问答系统、报告生成 | DeepSeek API, ChromaDB, LangChain RAG, Prompt Engineering |
| **成员C（前端+语音）** | React 前端、ECharts 图表、Whisper 语音、UI/UX | React, TypeScript, ECharts, Whisper, WebSocket |

---

## 十一、Demo 演示脚本（1.5 分钟版）

```
[0:00-0:08]  开场：展示系统主界面五大分区布局
[0:08-0:15]  语音输入："A锅炉出口温度突然升高到85度，帮我分析原因"
[0:15-0:25]  Agent 自动执行：数据查询 → 趋势曲线展示 → 实时温度卡片更新
[0:25-0:35]  预警触发：🔴阈值预警 + 🟡变化速率预警，预警区高亮
[0:35-0:45]  趋势预测：LSTM 预测未来3小时温度走势，预测 vs 实际对比图
[0:45-0:55]  故障诊断：RAG 检索知识库 → LLM 推理 → 诊断报告（可能原因+概率）
[0:55-1:05]  操作指导：生成标准化处理建议，展示操作步骤
[1:05-1:15]  历史追溯：时间线展示完整操作链，联动高亮
[1:15-1:22]  模型迭代演示：展示后台自动重训练日志，MAE 从 1.8→1.4，提升 22%
[1:22-1:30]  全场景问答：快捷键调出安全规程问答，"紧急停炉条件是什么？"
```

---

## 十二、风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|---------|
| DeepSeek API 不稳定 | 指令解析/诊断失败 | 本地备选 Qwen2.5-7B（Ollama），降级方案 |
| Whisper 对电厂术语识别不准 | 语音准确率 < 85% | prompt 注入术语表；备选百度语音 API |
| LSTM 训练耗时过长 | 模型迭代演示卡顿 | 预训练多个工况的模型，演示时只做增量更新 |
| 模拟数据不够真实 | 评委质疑工业真实性 | 参考《火电厂集控运行规程》设定参数范围；文档中明确标注"模拟数据" |
| 时间不够 | 功能无法全部完成 | 优先级：核心闭环 > 语音 > 模型迭代 > 前端美化 |

---

> **文档版本**: v1.0 | **最后更新**: 2026-07-09 | **面向团队**: 3人 × 8周
