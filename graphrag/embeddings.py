"""
Kairós Intelligence v2.7.1 — Geração de Embeddings
Usa sentence-transformers para criar vetores de embedding.
"""

from sentence_transformers import SentenceTransformer
from graphrag.config import EMBEDDING_MODEL


class EmbeddingGenerator:
    """Gera embeddings vetoriais para busca semântica."""

    def __init__(self):
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(EMBEDDING_MODEL)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Gera embedding para um único texto."""
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Gera embeddings para um lote de textos."""
        return self.model.encode(texts).tolist()


embedding_generator = EmbeddingGenerator()
