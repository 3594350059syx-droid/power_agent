# RAG 模块接口规范（interface_rag.md）

**版本：v1.0**

负责人：D（知识库 / RAG）

更新时间：2026-07

---

# 1. 文档目的

本文档用于统一 RAG（Retrieval-Augmented Generation）模块接口规范，确保 A（Agent）、B（故障案例）、D（RAG）之间开发一致，避免接口不兼容。

RAG 模块负责：

- 电厂知识文档管理
- 文档切片（Chunk）
- Embedding 向量生成
- FAISS 向量检索
- 向 Agent 提供知识片段

**RAG 不负责：**

- Prompt 拼接
- LLM 推理
- 最终回答生成

以上功能由 Agent 模块负责。

---

# 2. 模块流程

```
用户问题
      │
      ▼
rag_tool(query)
      │
      ▼
Embedding(query)
      │
      ▼
FAISS 检索
      │
      ▼
返回 Top-K 知识片段
      │
      ▼
Agent 拼接 Prompt
      │
      ▼
LLM 输出诊断结果
```

---

# 3. 目录结构

```
rag/

├── documents/
│   ├── procedures/
│   ├── cases/
│   └── manuals/
│
├── embedding/
│   ├── chunker.py
│   ├── embedder.py
│   └── pipeline.py
│
├── retriever/
│   ├── index_builder.py
│   ├── searcher.py
│   └── index/
│
├── __init__.py
└── rag_tool.py
```

---

# 4. rag_tool() 接口规范

## 函数签名

```python
def rag_tool(
    query: str,
    top_k: int = 3
) -> list[dict]:
    ...
```

---

## 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| query | str | 用户问题 |
| top_k | int | 返回知识条数，默认 3 |

示例：

```python
rag_tool("主蒸汽温度过高原因")
```

---

## 输出

统一返回：

```python
[
    {
        "source": "case_01_主蒸汽温度异常升高.txt",
        "content": "...",
        "similarity": 0.94
    }
]
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| source | str | 来源文档 |
| content | str | 检索文本 |
| similarity | float | 相似度 |

**字段名称不得修改。**

---

# 5. Search 接口规范

```
search(query, top_k)
```

返回格式与 rag_tool 保持一致。

默认：

```
top_k = 3
```

---

# 6. 文档规范

知识文档存放：

```
rag/documents/
```

包含：

```
procedures/
cases/
manuals/
```

文件命名：

```
{类别}_{编号}_{标题}.txt
```

例如：

```
case_01_主蒸汽温度异常升高.txt
```

---

# 7. 知识文档内容规范

建议统一采用如下结构：

```
故障名称：

适用设备：

现象描述：

常见原因：

处理措施：

关联参数：
```

例如：

```
故障名称：
主蒸汽温度异常升高

适用设备：
锅炉

现象描述：
主蒸汽温度超过550℃

常见原因：
1. 减温水不足
2. 给煤量增加
3. 过热器积灰

处理措施：
1. 增大减温水流量
2. 检查给煤系统
3. 必要时降低负荷

关联参数：
主蒸汽温度
减温水流量
给煤量
```

每篇文档：

- 200~500 字
- 内容真实
- 包含可检索参数
- 避免空泛描述

---

# 8. Chunk 规范

Chunk 工具：

```
RecursiveCharacterTextSplitter
```

参数：

```
chunk_size = 300

chunk_overlap = 50
```

Chunk 数据结构：

```python
{
    "content": "...",
    "source": "...",
    "category": "...",
    "chunk_id": 0,
    "embedding": [...]
}
```

字段说明：

| 字段 | 说明 |
|------|------|
| content | Chunk 内容 |
| source | 来源文件 |
| category | procedures / cases / manuals |
| chunk_id | Chunk 编号 |
| embedding | 向量 |

---

# 9. Embedding 规范

默认模型：

```
text2vec-base-chinese
```

Embedding 维度：

```
768
```

统一使用同一模型，避免索引不兼容。

---

# 10. FAISS 索引规范

索引目录：

```
rag/retriever/index/
```

生成：

```
index.faiss

metadata.pkl
```

metadata 保存：

```
content

source

category

chunk_id
```

索引类型：

```
faiss.IndexFlatIP
```

---

# 11. Agent 调用规范（A）

Agent 调用方式：

```python
from rag.rag_tool import rag_tool
```

调用：

```python
knowledge = rag_tool(query)
```

Agent 负责：

- Prompt 拼接
- 调用 LLM
- 输出结果

RAG 不负责 Prompt 构造。

---

# 12. 与 B 的数据规范

B 提供故障案例时：

- 使用 UTF-8 编码
- txt 或 md 文件
- 按统一模板编写
- 放入：

```
rag/documents/cases/
```

无需修改代码即可加入知识库。

---

# 13. 索引更新流程

新增知识文档：

```
documents
    │
    ▼
chunk
    │
    ▼
embedding
    │
    ▼
build index
    │
    ▼
完成
```

每次新增文档后需要重新构建索引。

---

# 14. MVP 验收标准

调用：

```python
from rag.rag_tool import rag_tool

results = rag_tool(
    "主蒸汽温度过高原因",
    top_k=3
)
```

要求：

- 返回不少于 2 条知识
- 返回字段完整
- source/content/similarity 三个字段均存在
- 第一条结果应包含主蒸汽温度相关知识

---

# 15. 后续扩展

后续可扩展：

- BM25 + FAISS 混合检索
- Reranker 重排序
- 多路召回
- 图片/表格知识库
- DeepSeek Embedding API
- Milvus / Chroma 向量数据库

---

# 16. 待确认事项（与团队）

## A（Agent）

- [ ] rag_tool() 接口签名确认
- [ ] Agent Prompt 拼接方式确认

## B（故障案例）

- [ ] 故障案例模板确认
- [ ] 参数命名规范确认

## D（RAG）

- [ ] Embedding 模型最终确认
- [ ] FAISS 索引更新流程确认