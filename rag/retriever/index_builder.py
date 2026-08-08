import os
import pickle
import numpy as np
import faiss

INDEX_DIR = os.path.join(os.path.dirname(__file__), "index")


def build_faiss_index(chunks):
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)

    embeddings = np.array([chunk["embedding"] for chunk in chunks], dtype=np.float32)
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    index_path = os.path.join(INDEX_DIR, "index.faiss")
    faiss.write_index(index, index_path)

    metadata = []
    for chunk in chunks:
        metadata.append({
            "content": chunk["content"],
            "source": chunk["source"],
            "category": chunk["category"],
            "chunk_id": chunk.get("chunk_id", 0)
        })

    metadata_path = os.path.join(INDEX_DIR, "metadata.pkl")
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)

    print(f"索引构建完成，共{len(chunks)}个chunk")
    print(f"索引路径: {index_path}")
    print(f"元数据路径: {metadata_path}")

    return index, metadata


def load_faiss_index():
    index_path = os.path.join(INDEX_DIR, "index.faiss")
    metadata_path = os.path.join(INDEX_DIR, "metadata.pkl")

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        return None, None

    index = faiss.read_index(index_path)

    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)

    return index, metadata