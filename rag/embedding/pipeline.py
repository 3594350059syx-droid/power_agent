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
    docs = load_documents(folder)

    chunks = []
    chunk_id_counter = 0

    for doc in docs:
        texts = split_text(doc["content"])
        for text in texts:
            chunks.append({
                "content": text,
                "source": doc["source"],
                "category": doc["category"],
                "chunk_id": chunk_id_counter
            })
            chunk_id_counter += 1

    print(f"生成chunk数量: {len(chunks)}")

    return chunks


def build_index():
    documents_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents")
    chunks = process_documents(documents_folder)

    if chunks:
        from rag.embedding.embedder import embedder
        from rag.retriever.index_builder import build_faiss_index

        texts = [c["content"] for c in chunks]
        vectors = embedder.encode(texts)

        for i, c in enumerate(chunks):
            c["embedding"] = vectors[i]

        build_faiss_index(chunks)
        return chunks
    else:
        print("未找到文档，跳过索引构建")
        return []


if __name__ == "__main__":
    result = build_index()
    print("最终chunk:", len(result))
    if result:
        print("向量维度:", len(result[0]["embedding"]))