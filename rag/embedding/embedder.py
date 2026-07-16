from sentence_transformers import SentenceTransformer


class Embedder:

    def __init__(self):

        # 中文语义模型
        self.model = SentenceTransformer(
            "shibing624/text2vec-base-chinese"
        )


    def encode(self, texts):

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        return embeddings.tolist()


embedder = Embedder()