from rag.retriever.searcher import search


def rag_tool(query: str, top_k: int = 3) -> list[dict]:
    return search(query, top_k)