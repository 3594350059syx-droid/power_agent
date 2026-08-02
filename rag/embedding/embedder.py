import os
from sentence_transformers import SentenceTransformer


# 本地模型路径 (优先使用, 避免每次从 HuggingFace 下载)
_LOCAL_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "text2vec-base-chinese"
)

# 远程模型名 (本地不存在时回退到 HF 在线下载)
_REMOTE_MODEL_NAME = "shibing624/text2vec-base-chinese"


def _resolve_model_path():
    """优先返回本地模型路径, 本地不存在则返回远程模型名。"""
    if os.path.exists(_LOCAL_MODEL_DIR) and os.listdir(_LOCAL_MODEL_DIR):
        return _LOCAL_MODEL_DIR
    return _REMOTE_MODEL_NAME


class Embedder:
    """
    text2vec-base-chinese 向量生成器。

    采用懒加载: __init__ 不加载模型, 第一次 encode() 时才加载。
    优先从本地路径 rag/models/text2vec-base-chinese 加载,
    本地不存在时回退到 HuggingFace 在线下载。
    """

    def __init__(self):
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            model_path = _resolve_model_path()
            self._model = SentenceTransformer(model_path)
        return self._model

    def encode(self, texts):
        model = self._ensure_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        return embeddings.tolist()


embedder = Embedder()
