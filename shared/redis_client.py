"""
Kairós Intelligence v2.7.1 — Cliente Redis
Buffer de mensagens, estado de conversas, filas de tarefas.
"""

import json
import asyncio
import redis.asyncio as aioredis
from shared.config import settings


class RedisClient:
    """Cliente Redis assíncrono para buffer, cache e filas."""

    def __init__(self):
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self):
        await self.redis.close()

    # --- Buffer de Mensagens (8 segundos) ---
    async def buffer_message(self, phone: str, message: str) -> bool:
        """Adiciona mensagem ao buffer. Retorna True se é a primeira do ciclo."""
        key = f"buffer:{phone}"
        is_first = not await self.redis.exists(key)
        await self.redis.rpush(key, message)
        await self.redis.expire(key, settings.REDIS_BUFFER_SECONDS + 2)
        return is_first

    async def get_buffered_messages(self, phone: str) -> list[str]:
        """Recupera e limpa todas as mensagens bufferizadas."""
        key = f"buffer:{phone}"
        messages = await self.redis.lrange(key, 0, -1)
        await self.redis.delete(key)
        return messages

    # --- Estado da Conversa ---
    async def set_conversation_state(self, phone: str, state: dict, ttl: int = 1800):
        """Salva estado da conversa (TTL padrão: 30 minutos)."""
        key = f"conv:{phone}"
        await self.redis.setex(key, ttl, json.dumps(state, ensure_ascii=False))

    async def get_conversation_state(self, phone: str) -> dict | None:
        """Recupera estado da conversa."""
        key = f"conv:{phone}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def clear_conversation(self, phone: str):
        """Limpa estado da conversa (timeout ou finalização)."""
        await self.redis.delete(f"conv:{phone}")

    # --- Fila de Tarefas (Manager) ---
    async def enqueue_task(self, queue: str, task: dict):
        """Enfileira tarefa para processamento."""
        await self.redis.rpush(f"queue:{queue}", json.dumps(task, ensure_ascii=False))

    async def dequeue_task(self, queue: str, timeout: int = 0) -> dict | None:
        """Desenfileira tarefa (bloqueante com timeout)."""
        result = await self.redis.blpop(f"queue:{queue}", timeout=timeout)
        if result:
            _, data = result
            return json.loads(data)
        return None

    # --- Janela Meta (24h) ---
    async def update_window(self, phone: str):
        """Registra última interação do paciente (renova janela 24h)."""
        key = f"window:{phone}"
        await self.redis.setex(key, 86400, "1")  # 24h TTL

    async def is_window_open(self, phone: str) -> bool:
        """Verifica se a janela de 24h está aberta."""
        return await self.redis.exists(f"window:{phone}") > 0


redis_client = RedisClient()
