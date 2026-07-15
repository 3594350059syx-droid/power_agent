import numpy as np
from rag.retriever.index_builder import load_faiss_index
from rag.embedding.embedder import embedder


class Searcher:
    def __init__(self):
        self.index, self.metadata = load_faiss_index()

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if self.index is None or self.metadata is None:
            return []

        query_vector = embedder.encode([query])[0]
        query_np = np.array(query_vector, dtype=np.float32).reshape(1, -1)

        distances, indices = self.index.search(query_np, top_k)

        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            similarity = distances[0][i]

            if idx >= 0 and idx < len(self.metadata):
                results.append({
                    "source": self.metadata[idx]["source"],
                    "content": self.metadata[idx]["content"],
                    "similarity": round(float(similarity), 4)
                })

        return results


searcher = Searcher()


def search(query: str, top_k: int = 3) -> list[dict]:
    return searcher.search(query, top_k)