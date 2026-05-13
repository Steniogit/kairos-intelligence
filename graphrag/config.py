"""
Kairós Intelligence v2.7.1 — GraphRAG Config
Configuração centralizada do pipeline GraphRAG.
"""

import os

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dims, leve e rápido
EMBEDDING_DIMENSIONS = 384

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_AUTH_TOKEN = os.getenv("CHROMA_AUTH_TOKEN", "")

# Collections ChromaDB por tenant
COLLECTION_FAQ = "{clinic_id}_faq"
COLLECTION_PATIENTS = "{clinic_id}_patients"
COLLECTION_HEALTH_TIPS = "{clinic_id}_health_tips"
COLLECTION_PROTOCOLS = "{clinic_id}_protocols"

# Top-K para retrieval
RETRIEVAL_TOP_K = 5
RETRIEVAL_SIMILARITY_THRESHOLD = 0.7
