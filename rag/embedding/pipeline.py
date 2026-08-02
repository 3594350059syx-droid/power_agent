import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rag.embedding.chunker import split_text


def load_documents(folder):
    documents = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".txt"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                category = os.path.basename(root)
                documents.append({
                    "content": text,
                    "source": file,
                    "category": category
                })
    return documents


def process_documents(folder):
    """
    完整处理流水线: 读取目录 → 切片 → embedding → 输出 chunks 列表

    返回结构 (满足 D_week2.md 验收标准):
        [
            {
                "content": "...",
                "metadata": {
                    "source": "case_01_xxx.txt",
                    "category": "cases",
                    "chunk_id": 0
                },
                "embedding": [768 floats]
            },
            ...
        ]

    验收:
        chunks = process_documents("rag/documents/")
        assert len(chunks) >= 30
        assert all(len(c["embedding"]) == 768 for c in chunks)
        assert all("source" in c["metadata"] for c in chunks)
    """
    docs = load_documents(folder)

    # 1. 切片
    raw_chunks = []
    chunk_id_counter = 0
    for doc in docs:
        texts = split_text(doc["content"])
        for text in texts:
            raw_chunks.append({
                "content": text,
                "source": doc["source"],
                "category": doc["category"],
                "chunk_id": chunk_id_counter
            })
            chunk_id_counter += 1

    print(f"生成chunk数量: {len(raw_chunks)}")
    if not raw_chunks:
        return []

    # 2. 生成 embedding (懒加载, 不会在 import 时拖慢)
    from rag.embedding.embedder import embedder
    texts = [c["content"] for c in raw_chunks]
    vectors = embedder.encode(texts)

    # 3. 组装最终结构 (满足验收: c["embedding"] + c["metadata"]["source"])
    chunks = []
    for i, c in enumerate(raw_chunks):
        chunks.append({
            "content": c["content"],
            "metadata": {
                "source": c["source"],
                "category": c["category"],
                "chunk_id": c["chunk_id"]
            },
            "embedding": vectors[i]
        })

    return chunks


def build_index():
    """
    构建完整 FAISS 索引: process_documents → 持久化索引文件

    process_documents 返回嵌套 metadata 结构,
    而 index_builder/searcher 历史使用平铺字段 (兼容 interface_rag.md),
    这里转换回平铺结构再交给 index_builder。
    """
    documents_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents")
    chunks = process_documents(documents_folder)

    if not chunks:
        print("未找到文档，跳过索引构建")
        return []

    from rag.retriever.index_builder import build_faiss_index

    flat_chunks = []
    for c in chunks:
        flat_chunks.append({
            "content": c["content"],
            "source": c["metadata"]["source"],
            "category": c["metadata"]["category"],
            "chunk_id": c["metadata"]["chunk_id"],
            "embedding": c["embedding"]
        })
    build_faiss_index(flat_chunks)
    return chunks


if __name__ == "__main__":
    result = build_index()
    print("最终chunk:", len(result))
    if result:
        print("向量维度:", len(result[0]["embedding"]))
