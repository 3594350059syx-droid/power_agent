# PR P0-4: RAG 知识检索模块

**提交者**：D  
**PR 编号**：#24  
**目标分支**：develop（⚠️ 当前指向 main，需修改）  
**审查人**：A  
**审查日期**：2026-07-12

---

## 一、背景

P0-4 任务：落地 RAG（Retrieval-Augmented Generation）知识检索模块，为 Agent 提供电厂故障诊断知识库支持。包含文档切分、向量化、FAISS 索引构建、语义搜索四大核心能力，以及 15 篇结构化知识文档（案例/规程/设备说明三类）。

---

## 二、变更摘要

| 维度 | 内容 |
|------|------|
| 代码 | +1,171 行 / -4 行，9 个 Python 文件 |
| 文档 | 15 篇 .txt（案例 5 + 规程 5 + 设备 5） |
| 接口 | `rag_tool(query, top_k=3) -> list[dict]`，匹配 A.md 契约 |
| 配置 | requirements.txt 新增 4 个 RAG 依赖 |

---

## 三、文件清单

### 核心代码

| 文件 | 行数 | 说明 |
|------|------|------|
| `rag/rag_tool.py` | 5 | 入口函数，Agent 直接调用 |
| `rag/embedding/chunker.py` | 24 | 文本切分（langchain RecursiveCharacterTextSplitter） |
| `rag/embedding/embedder.py` | 25 | 向量化（text2vec-base-chinese，768 维） |
| `rag/embedding/pipeline.py` | 73 | 建索引流水线：加载 → 切分 → 向量化 → 建索引 |
| `rag/retriever/index_builder.py` | 54 | FAISS IndexFlatIP 构建 + pickle 元数据 |
| `rag/retriever/searcher.py` | 38 | 语义搜索，返回 source/content/similarity |

### 知识文档

| 类别 | 文件 | 篇数 |
|------|------|------|
| `rag/documents/cases/` | case_01 ~ case_05 | 5 篇故障案例 |
| `rag/documents/procedures/` | proc_01 ~ proc_05 | 5 篇运行规程 |
| `rag/documents/manuals/` | equip_01 ~ equip_05 | 5 篇设备说明书 |

### 配置变更

| 文件 | 变更 |
|------|------|
| `requirements.txt` | 启用 faiss-cpu、sentence-transformers、langchain-text-splitters、numpy |
| `.gitignore` | 新增 `rag/retriever/index/` 排除规则 |

---

## 四、接口契约

### `rag_tool()` 签名

```python
def rag_tool(query: str, top_k: int = 3) -> list[dict]:
```

### 返回值格式

```python
[
    {
        "source": "case_01_主蒸汽温度异常升高.txt",
        "content": "主蒸汽温度异常升高...",
        "similarity": 0.9412
    }
]
```

✅ 与 A.md 定义的契约完全一致。

---

## 五、验收标准

| 标准 | 结果 |
|------|------|
| 33 个 chunk 生成 | ✅ 通过 |
| 返回 ≥ 2 条检索结果 | ✅ 通过（top_k=3，满足 MVP） |
| 结果含 source/content/similarity | ✅ 三个字段完整 |
| 中文语义匹配有效 | ✅ text2vec-base-chinese 模型 |

---

## 六、审查结论

| 类别 | 数量 | 说明 |
|------|------|------|
| ✅ 代码质量 | — | 模块分工清晰，与 D.md 规格一致 |
| ✅ 文档质量 | — | 15 篇文档格式统一，内容专业 |
| ✅ 接口契约 | — | 签名与返回值完全匹配 A.md |
| 🔴 必须修 | 3 | 见下方 |
| 🟡 建议修 | 2 | 见下方 |

### 🔴 必须修

| # | 问题 | 位置 | 修复方式 |
|---|------|------|----------|
| 1 | `.txt.txt` 双扩展名 | 全部 15 个文档文件 | 重命名为 `.txt` |
| 2 | `requirements.txt` 未更新 | 项目根 | 取消注释 RAG 依赖，补充 `langchain-text-splitters` 和 `numpy` |
| 3 | PR target 为 main | PR #24 | 改为 `develop` |

### 🟡 建议修

| # | 问题 | 修复建议 |
|---|------|----------|
| 1 | `pipeline.py` 中有 `sys.path` hack | 改为 `PYTHONPATH` 方式或 `pip install -e .` |
| 2 | 索引文件提交到了 git | `.gitignore` 已加 `rag/retriever/index/` 排除 |

---

## 七、本地落盘（已由 A 完成）

上述 🔴 必须修的三项已在本地修复后落盘：

- 文档扩展名：全部统一为 `.txt`
- 依赖：`requirements.txt` 已启用 RAG 四项依赖
- `.gitignore`：已排除运行时索引文件

D 需要在 PR 分支上同步执行上述修复后重新推送。
