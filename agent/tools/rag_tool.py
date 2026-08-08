"""
RAG 知识检索 Tool — Mock 实现
P0-2: D 的 rag_tool 未到位前使用此 mock

D 完成真实实现后，将 workflow 中的 mock 调用替换为:
    from rag.retriever.rag_tool import rag_tool
"""


def rag_tool_mock(query: str, top_k: int = 3) -> list[dict]:
    """
    Mock: RAG 知识检索

    生成符合 rag_tool 签名的模拟返回值。
    """
    mock_knowledge = [
        {
            "source": "\u9505\u7089\u8fd0\u884c\u89c4\u7a0b \u00a73.2",
            "content": "\u4e3b\u84b8\u6c7d\u6e29\u5ea6\u8fc7\u9ad8\u65f6\uff0c\u5e94\u7acb\u5373\u68c0\u67e5\u51cf\u6e29\u6c34\u7cfb\u7edf\uff0c"
                       "\u786e\u8ba4\u51cf\u6e29\u6c34\u9600\u95e8\u5f00\u5ea6\u662f\u5426\u6b63\u5e38\uff0c"
                       "\u5fc5\u8981\u65f6\u624b\u52a8\u8c03\u6574\u9600\u95e8\u5f00\u5ea6\u3002",
            "similarity": 0.94,
        },
        {
            "source": "\u8bbe\u5907\u6545\u969c\u6848\u4f8b\u5e93 F001",
            "content": "\u51cf\u6e29\u6c34\u9600\u95e8\u5361\u6b7b\u5bfc\u81f4\u4e3b\u84b8\u6c7d\u6e29\u5ea6\u6301\u7eed\u5347\u9ad8\uff0c"
                       "\u5efa\u8bae\u68c0\u67e5\u9600\u95e8\u6267\u884c\u673a\u6784\u5e76\u6e05\u7406\u9600\u95e8\u5361\u6b7b\u3002",
            "similarity": 0.88,
        },
        {
            "source": "\u6c7d\u8f6e\u673a\u8fd0\u884c\u7ef4\u62a4\u624b\u518c \u00a75.4",
            "content": "\u8f74\u627f\u632f\u52a8\u7a81\u589e\u901a\u5e38\u8868\u660e\u8f74\u627f\u78e8\u635f\u52a0\u5267\uff0c"
                       "\u5e94\u5b89\u6392\u505c\u673a\u68c0\u67e5\uff0c\u907f\u514d\u53d1\u5c55\u4e3a\u8f74\u627f\u635f\u574f\u3002",
            "similarity": 0.82,
        },
    ]

    return mock_knowledge[:top_k]
