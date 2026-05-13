"""
Kairós Intelligence v2.7.1 — Configuração Centralizada
Carrega variáveis de ambiente e conecta serviços compartilhados.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configurações centralizadas carregadas de variáveis de ambiente."""

    # --- DeepSeek ---
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # --- Gemini ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_PRO: str = os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    GEMINI_MODEL_FLASH: str = os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")

    # --- Evolution Go ---
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
    EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "http://evolution-go:8080")
    EVOLUTION_INSTANCE: str = os.getenv("EVOLUTION_INSTANCE_NAME", "kairos-clinica")

    # --- Redis ---
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    REDIS_BUFFER_SECONDS: int = int(os.getenv("REDIS_BUFFER_SECONDS", "8"))

    # --- Ademed ---
    ADEMED_URL: str = os.getenv("ADEMED_URL", "")
    ADEMED_USER: str = os.getenv("ADEMED_USER", "")
    ADEMED_PASS: str = os.getenv("ADEMED_PASS", "")

    # --- Neo4j ---
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

    # --- ChromaDB ---
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "chromadb")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_AUTH_TOKEN: str = os.getenv("CHROMA_AUTH_TOKEN", "")

    # --- Paperclip ---
    PAPERCLIP_URL: str = os.getenv("PAPERCLIP_URL", "http://paperclip:3000")

    # --- TTS ---
    GOOGLE_TTS_API_KEY: str = os.getenv("GOOGLE_TTS_API_KEY", "")
    GOOGLE_TTS_VOICE: str = os.getenv("GOOGLE_TTS_VOICE", "pt-BR-Journey-F")
    GOOGLE_TTS_SPEED: float = float(os.getenv("GOOGLE_TTS_SPEED", "1.0"))

    # --- Clínica ---
    CLINICA_NOME: str = os.getenv("CLINICA_NOME", "")
    GESTOR_WHATSAPP: str = os.getenv("GESTOR_WHATSAPP", "")
    GESTOR_NOME: str = os.getenv("GESTOR_NOME", "")
    RECEPCIONISTA_WHATSAPP: str = os.getenv("RECEPCIONISTA_WHATSAPP", "")

    # --- Logs ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "/home/openclaw/logs")


settings = Settings()
