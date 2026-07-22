# D 成员 — Week 2 开发任务

## 上周回顾

| 任务 | 状态 | 说明 |
|------|------|------|
| 环境准备 | ✅ 完成 | FAISS / sentence-transformers / langchain 等依赖已就绪 |
| 与 A 确认 rag_tool 签名 | ✅ 完成 | `rag_tool(query: str, top_k: int) -> list[dict]` 签名已锁定 |

## 本周目标

**构建 RAG 知识库全链路——从文档到检索，让 A 的 Agent 能查到知识。**

```
15 篇知识文档 → 切片 → Embedding → FAISS 索引 → rag_tool 可检索
```

---

## 任务 1：P0-1 — 知识文档整理

**截止**：Week 2 周二

### 要做什么

编写 15 篇电厂领域知识文档（纯文本 .txt），分 3 类：

```
rag/documents/
├── procedures/                 ← 运行规程（5 篇）
│   ├── proc_01_锅炉正常运行参数.txt
│   ├── proc_02_汽轮机启停规程.txt
│   ├── proc_03_发电机运行维护.txt
│   ├── proc_04_主蒸汽温度控制规程.txt
│   └── proc_05_减温水系统操作规程.txt
├── cases/                      ← 故障案例（5 篇，最重要）
│   ├── case_01_主蒸汽温度异常升高.txt
│   ├── case_02_锅炉炉膛压力波动.txt
│   ├── case_03_汽轮机轴承振动超标.txt
│   ├── case_04_发电机定子温度过高.txt
│   └── case_05_减温水调节阀故障.txt
└── manuals/                    ← 设备说明（5 篇）
    ├── equip_01_锅炉本体说明书.txt
    ├── equip_02_汽轮机结构说明.txt
    ├── equip_03_发电机技术参数.txt
    ├── equip_04_温度传感器说明.txt
    └── equip_05_DCS系统简介.txt
```

### 文档质量要求

- 每篇 **200-500 字**，内容具体可操作
- 包含**数字**（参数值、阈值、温度范围等），方便检索命中
- **故障案例优先级最高**——直接支撑 RAG 诊断
- 避免泛泛而谈（如"要注意安全"），需要可执行的操作指令

### 文档示例

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
3. 如温度持续上升，降低机组负荷至 80%
4. 当主蒸汽温度超过 565℃ 时，触发紧急停炉

关联参数：主蒸汽温度、减温水流量、给煤量、机组负荷
```

### 验收标准

```bash
ls rag/documents/procedures/ | wc -l  # ≥ 5
ls rag/documents/cases/ | wc -l       # ≥ 5
ls rag/documents/manuals/ | wc -l     # ≥ 5
```

---

## 任务 2：P0-2 — 文档切片 + Embedding

**截止**：Week 2 周四

### 要做什么

1. **文档切片** (`rag/embedding/chunker.py`)：
   - 使用 `langchain.text_splitter.RecursiveCharacterTextSplitter`
   - `chunk_size=300`, `chunk_overlap=50`
   - 每个 chunk 保留元数据：来源文件、类别（procedure/case/manual）

2. **向量生成** (`rag/embedding/embedder.py`)：
   - 模型：`text2vec-base-chinese`（本地，无需 API）
   - 输出 768 维向量
   - 支持批量处理

3. **处理流水线** (`rag/embedding/pipeline.py`)：
   - 一键执行：读取目录 → 切片 → embedding → 输出 chunks 列表

### 产出文件

```
rag/embedding/
├── __init__.py
├── chunker.py            ← 文档切片逻辑
├── embedder.py           ← 向量生成（text2vec-base-chinese）
└── pipeline.py           ← 完整流水线（run_all）
```

### 验收标准

```python
from rag.embedding.pipeline import process_documents

chunks = process_documents("rag/documents/")
assert len(chunks) >= 30                              # 至少 30 个切片
assert all(len(c["embedding"]) == 768 for c in chunks) # 向量维度正确
assert all("source" in c["metadata"] for c in chunks)  # 元数据完整
```

---

## 任务 3：P0-3 — FAISS 索引构建 + 检索

**截止**：Week 2 周五

### 要做什么

1. **索引构建** (`rag/retriever/index_builder.py`)：
   - 使用 `faiss.IndexFlatIP`（内积搜索，配合 L2 归一化等价于余弦相似度）
   - 构建索引并持久化到 `rag/retriever/index/`
   - 保存 chunk 元数据（.pkl）

2. **检索实现** (`rag/retriever/searcher.py`)：
   - `search(query: str, top_k: int = 3) -> list[dict]`
   - query → embedding → FAISS search → 返回 top_k 结果
   - 返回格式：
     ```python
     [
         {
             "source": "case_01_主蒸汽温度异常升高.txt",
             "content": "主蒸汽温度持续升高...处理措施：增大减温水流量...",
             "similarity": 0.94
         },
         ...
     ]
     ```

### 产出文件

```
rag/retriever/
├── __init__.py
├── index_builder.py      ← FAISS 索引构建 + 持久化
├── searcher.py           ← 检索接口
└── index/                ← 索引文件（运行时生成）
    ├── knowledge.index    ← FAISS 索引
    └── metadata.pkl       ← chunk 元数据
```

### 验收标准

```python
from rag.retriever.searcher import search

# 查询 1：应命中故障案例
results = search("主蒸汽温度过高怎么处理", top_k=3)
assert len(results) == 3
assert results[0]["similarity"] > 0.5
assert "减温水" in results[0]["content"] or "温度" in results[0]["content"]

# 查询 2：应命中设备说明
results = search("发电机定子温度正常范围是多少", top_k=2)
assert any("定子" in r["content"] for r in results)
```

---

## 任务 4：为 A 提供意图识别测试用例

**截止**：Week 2 周三

### 要做什么

编写 `tests/agent/intent_test_cases.json`，包含 10 条测试指令：

```json
[
  {"input": "分析2号机组过去24小时主蒸汽温度异常", "expected_intent": "anomaly_detection", "expected_params": {"device_id": "generator_002", "parameter": "steam_temp"}},
  {"input": "预测3号汽轮机未来6小时振动趋势", "expected_intent": "prediction", "expected_params": {"device_id": "turbine_003", "parameter": "vibration"}},
  {"input": "查询4号发电机当前功率", "expected_intent": "data_query", "expected_params": {"device_id": "generator_004", "parameter": "active_power"}},
  {"input": "2号锅炉主蒸汽温度过高是什么原因，怎么处理", "expected_intent": "diagnosis", "expected_params": {"device_id": "generator_002", "parameter": "steam_temp"}},
  {"input": "你好，你能做什么", "expected_intent": "chat", "expected_params": {}}
  // ... 至少 10 条
]
```

> A 本周用这 10 条用例验证 DeepSeek 意图识别准确率，目标 ≥ 8/10。

---

## 本周沟通要点

- **周二前**：完成 P0-1 知识文档，与 B 核对故障案例的工业合理性
- **周三前**：提供意图识别测试用例给 A
- **周四前**：完成 P0-2 切片 + Embedding 流水线，确保可重复运行
- **周五前**：完成 P0-3 FAISS 检索，A 可通过 `rag_tool` mock 调用
- **周五**：提交 RAG 模块 PR（分支 `feature/rag-module`）
