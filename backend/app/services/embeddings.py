import threading


EMBEDDING_DIMENSION = 384


class EmbeddingService:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        vectors = model.encode(texts, normalize_embeddings=True)
        results = [vector.tolist() for vector in vectors]
        for result in results:
            if len(result) != EMBEDDING_DIMENSION:
                raise RuntimeError(
                    f"Embedding model returned {len(result)} dimensions; "
                    f"the database schema requires {EMBEDDING_DIMENSION}."
                )
        return results

    def _get_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(self.model_name)
        return self._model
