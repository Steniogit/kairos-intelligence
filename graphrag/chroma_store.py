"""
Kairós Intelligence v2.7.1 — ChromaDB Store
CRUD no ChromaDB para busca vetorial por similaridade semântica.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from graphrag.config import (
    CHROMA_HOST, CHROMA_PORT, CHROMA_AUTH_TOKEN,
    RETRIEVAL_TOP_K, RETRIEVAL_SIMILARITY_THRESHOLD,
)
from graphrag.embeddings import embedding_generator


class ChromaStore:
    """Armazenamento de vetores no ChromaDB."""

    def __init__(self):
        self._client = None

    @property
    def client(self) -> chromadb.HttpClient:
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=CHROMA_PORT,
                settings=ChromaSettings(
                    chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                    chroma_client_auth_credentials=CHROMA_AUTH_TOKEN,
                ),
            )
        return self._client

    def get_or_create_collection(self, name: str):
        """Obtém ou cria uma collection."""
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
    ):
        """Adiciona documentos com embeddings ao ChromaDB."""
        collection = self.get_or_create_collection(collection_name)
        embeddings = embedding_generator.embed_batch(documents)
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = RETRIEVAL_TOP_K,
    ) -> list[dict]:
        """Busca por similaridade semântica. Retorna top-K resultados."""
        collection = self.get_or_create_collection(collection_name)
        query_embedding = embedding_generator.embed_text(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        matches = []
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i]
            similarity = 1 - distance  # cosine distance → similarity
            if similarity >= RETRIEVAL_SIMILARITY_THRESHOLD:
                matches.append({
                    "document": doc,
                    "metadata": results["metadatas"][0][i],
                    "similarity": round(similarity, 4),
                })
        return matches

    def delete_collection(self, collection_name: str):
        """Remove uma collection inteira."""
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass


chroma_store = ChromaStore()
