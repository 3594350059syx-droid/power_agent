# D 成员开发任务文档

## 1. 角色定位

**知识库、测试与交付负责人**

你是项目的"质量保障"和"知识引擎"。你负责：
- 电厂知识文档整理与 RAG 知识库构建
- FAISS 向量检索实现
- 全模块测试用例设计与执行
- 比赛 PPT、演示脚本、视频等材料
- 与 B 协同维护故障案例库

## 2. MVP 目标

实现以下 RAG 链路：

```
用户问题 → embedding → FAISS 检索 → 返回相关知识片段
                                          ↓
                              A 的 Agent 将知识注入 LLM Prompt
                                          ↓
                              LLM 生成带知识支撑的诊断结论
```

MVP 验收标准：**A 的 Agent 调用 rag_tool("主蒸汽温度过高原因") → 返回至少 2 条相关知识片段。**

## 3. 具体开发任务

---

### P0-1: 知识文档整理

**技术方案**：
- 收集/编写电厂领域知识文档（.txt 或 .md 格式）
- 至少 3 类：运行规程、故障案例、设备说明
- 每类至少 5 篇文档
- 文档命名规范：`{类别}_{编号}_{标题}.txt`

**涉及目录**：
```
rag/documents/
├── procedures/            ← 运行规程
│   ├── proc_01_锅炉正常运行参数.txt
│   ├── proc_02_汽轮机启停规程.txt
│   ├── proc_03_发电机运行维护.txt
│   ├── proc_04_主蒸汽温度控制规程.txt
│   └── proc_05_减温水系统操作规程.txt
├── cases/                 ← 故障案例
│   ├── case_01_主蒸汽温度异常升高.txt
│   ├── case_02_锅炉炉膛压力波动.txt
│   ├── case_03_汽轮机轴承振动超标.txt
│   ├── case_04_发电机定子温度过高.txt
│   └── case_05_减温水调节阀故障.txt
└── manuals/               ← 设备说明
    ├── equip_01_锅炉本体说明书.txt
    ├── equip_02_汽轮机结构说明.txt
    ├── equip_03_发电机技术参数.txt
    ├── equip_04_温度传感器说明.txt
    └── equip_05_DCS系统简介.txt
```

**输入依赖**：无

**输出结果**：`rag/documents/` 下 15 篇知识文档

**验收标准**：
- 每篇文档 200-500 字，内容真实（参考真实电厂规程编写）
- 至少 5 篇包含可直接用于故障诊断的知识

**文档示例** (`case_01_主蒸汽温度异常升高.txt`)：
```
故障名称：主蒸汽温度异常升高
适用设备：锅炉
现象描述：主蒸汽温度持续升高，超过额定值 550℃
常见原因：
1. 减温水流量不足——可能由调节阀卡涩、减温水管道堵塞引起
2. 燃料量异常增加——煤量突增导致炉膛热负荷升高
3. 过热器积灰——换热效率下降，出口汽温升高
处理措施：
1. 增大减温水流量，观察温度变化
2. 检查燃料供给系统，确认煤量是否正常
3. 如温度持续上升，降低机组负荷
4. 严重时手动紧急停炉
关联参数：主蒸汽温度、减温水流量、给煤量、机组负荷
```

---

### P0-2: 实现文档切片与 Embedding

**技术方案**：
- 使用 `langchain.text_splitter.RecursiveCharacterTextSplitter` 切片
- chunk_size=300, chunk_overlap=50
- 使用 `text2vec-base-chinese` 或 DeepSeek Embedding API 生成向量
- 每个 chunk 保留元数据（来源文档、类别）

**涉及目录**：
```
rag/embedding/
├── __init__.py
├── chunker.py            ← 文档切片
├── embedder.py           ← 向量生成
└── pipeline.py           ← 完整处理流水线
```

**输入依赖**：
- 知识文档（P0-1）已完成
- requirements.txt 添加 `langchain`, `langchain-community`, `sentence-transformers`, `faiss-cpu`

**输出结果**：
- `rag/embedding/pipeline.py` 可运行：
```bash
python rag/embedding/pipeline.py
# 输出：处理 15 篇文档 → 生成约 50-80 个 chunks → 每个 chunk 768 维向量
```

**验收标准**：
```python
from rag.embedding.pipeline import process_documents
chunks = process_documents("rag/documents/")
assert len(chunks) >= 30
assert all(len(c["embedding"]) == 768 for c in chunks)  # 向量维度正确
```

---

### P0-3: 构建 FAISS 索引 + 检索接口

**技术方案**：
- 使用 `faiss.IndexFlatIP`（内积搜索）
- 建立向量索引并持久化到磁盘
- 实现检索函数：输入 query → embedding → FAISS search → 返回 top_k 结果

**涉及目录**：
```
rag/retriever/
├── __init__.py
├── index_builder.py      ← FAISS 索引构建
├── searcher.py           ← 检索实现
└── index/                ← 持久化索引文件（.faiss + .pkl）
```

**输入依赖**：
- 文档切片与 Embedding（P0-2）已完成

**输出结果**：
- FAISS 索引文件存储在 `rag/retriever/index/`
- 检索函数可独立调用

**验收标准**：
```python
from rag.retriever.searcher import search
results = search("主蒸汽温度过高怎么处理", top_k=3)
assert len(results) == 3
assert results[0]["similarity"] > 0.5
print(results[0]["content"])  # 应包含减温水相关建议
```

---

### P0-4: 实现 rag_tool 函数（供 A 调用）

**技术方案**：
- 封装为 A 定义的 `rag_tool()` 函数签名
- 输入 query 字符串 → 调用 FAISS 检索 → 返回格式化结果
- 可选：将检索结果拼接为 LLM Prompt 上下文

**涉及目录**：
```
rag/
├── __init__.py
└── rag_tool.py           ← A 调用的主入口
agent/tools/
└── rag_tool.py           ← Agent 侧的 Tool 封装（此文件由 A 维护，D 只需确保 rag/rag_tool.py 可被 import）
```

**输入依赖**：
- FAISS 索引（P0-3）已构建
- A 的接口规范 `agent/tools/base.py`

**输出结果**：
```python
# rag/rag_tool.py
def rag_tool(query: str, top_k: int = 3) -> list[dict]:
    """供 Agent 调用的 RAG 检索接口"""
    return [
        {
            "source": "case_01_主蒸汽温度异常升高.txt",
            "content": "主蒸汽温度持续升高...处理措施：增大减温水流量...",
            "similarity": 0.94
        },
        ...
    ]
```

**验收标准**：
```python
from rag.rag_tool import rag_tool
results = rag_tool("主蒸汽温度过高原因", top_k=3)
assert len(results) >= 2
assert all("source" in r and "content" in r and "similarity" in r for r in results)
```

---

### P1-1: 测试用例设计与执行

**技术方案**：
- 为每个模块设计测试用例（Agent 解析、数据查询、异常检测、RAG 检索）
- 重点测试 A↔B、A↔D 接口
- 编写端到端测试脚本

**涉及目录**：
```
tests/
├── agent/
│   ├── test_intent.py       ← Agent 意图识别测试
│   └── test_cases.json      ← 测试用例集
├── algorithm/
│   ├── test_anomaly.py      ← 异常检测测试
│   └── test_prediction.py   ← 预测模型测试
├── api/
│   ├── test_chat.py         ← /chat 接口测试
│   └── test_telemetry.py    ← 数据接口测试
└── integration/
    └── test_e2e.py          ← 端到端测试
```

**输入依赖**：各模块基本完成

**输出结果**：
- 20+ 测试用例
- 测试报告（Markdown）

**验收标准**：
```bash
pytest tests/  # 所有 P0 测试用例通过
```

**测试用例示例** (`test_cases.json`)：
```json
[
  {
    "input": "分析2号机组过去24小时主蒸汽温度异常",
    "expected_intent": "anomaly_detection",
    "expected_params": {"device_id": "generator_002", "parameter": "steam_temp"}
  },
  {
    "input": "预测3号汽轮机未来6小时振动趋势",
    "expected_intent": "prediction",
    "expected_params": {"device_id": "turbine_003", "parameter": "vibration"}
  },
  {
    "input": "查询4号发电机当前功率",
    "expected_intent": "data_query",
    "expected_params": {"device_id": "generator_004", "parameter": "active_power"}
  }
]
```

---

### P1-2: 比赛材料准备

**技术方案**：
- 基于 `docs/demo_case.md` 编写演示脚本
- 制作比赛 PPT（项目背景 → 技术方案 → Demo → 创新点）
- 录制系统演示视频（3-5 分钟）

**涉及目录**：
```
output/
├── presentation.pptx     ← 比赛 PPT
├── demo_script.md        ← 演示脚本
└── demo_video.mp4        ← 演示视频
```

**输入依赖**：系统基本可运行

**验收标准**：PPT 包含所有核心模块展示，视频能完整演示场景 5

---

### P2-1: 知识库扩展

**技术方案**：
- 增加文档数量到 30+ 篇
- 增加图片/表格类知识（如果有）
- 优化检索效果（调整 chunk_size, 增加 reranker）

**验收标准**：检索准确率提升 10%+

---

## 4. 开发流程

### 阶段 1：环境准备（Week 1 前两天）
- **做什么**：安装 FAISS、sentence-transformers 等依赖
- **沟通对象**：无
- **产出文件**：`requirements.txt` 补充 RAG 相关依赖

### 阶段 2：接口确认（Week 1 后三天）
- **做什么**：与 A 确认 `rag_tool()` 函数签名；与 B 确认故障案例数据格式
- **沟通对象**：A（接口规范）、B（案例格式）
- **产出文件**：确认的接口文档

### 阶段 3：模块开发（Week 2-4）
- **做什么**：P0-1 → P0-2 → P0-3 → P0-4 顺序执行
- **沟通对象**：A（对接测试）、B（案例数据）
- **产出文件**：知识文档 + FAISS 索引 + rag_tool 可用

### 阶段 4：本地测试（Week 4 末尾）
- **做什么**：确认 A 能成功 import 并调用 rag_tool
- **沟通对象**：A
- **产出文件**：调用测试通过

### 阶段 5：提交 GitHub（持续）
- **做什么**：每完成一个 P0 任务 commit + push
- **沟通对象**：A（Code Review）
- **产出文件**：feature 分支 + PR

### 阶段 6：联调（Week 5-6）+ 测试
- **做什么**：编写并执行测试用例，配合全员联调
- **沟通对象**：A、B、C 全员
- **产出文件**：测试报告 + bug 列表

---

## 5. 知识文档编写指南

### 格式要求

```
文件名：{类别}_{编号}_{标题}.txt

内容结构：
---
第一行：文档标题
第二行：空行
后续：正文内容（纯文本，不需要 Markdown 格式）
---

注意：
- 每篇文档 200-500 字
- 内容要具体、可操作
- 包含数字、参数名、阈值等可检索的关键信息
- 避免泛泛而谈（如"需要注意安全"这种无信息量内容）
```

### 优先级顺序

1. **先写故障案例**（最重要，直接支撑 RAG 诊断）
2. **再写运行规程**（提供参数正常范围参考）
3. **最后写设备说明**（补充背景知识）
