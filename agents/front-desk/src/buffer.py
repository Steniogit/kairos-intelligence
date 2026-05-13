"""
Kairós Intelligence v2.7.1 — Front-Desk: Buffer de Mensagens (8 segundos)
Agrupa mensagens fragmentadas do paciente em uma única requisição ao LLM.
"""

import asyncio
import logging
from shared.redis_client import redis_client
from shared.config import settings

logger = logging.getLogger("front-desk.buffer")


class MessageBuffer:
    """Buffer de 8 segundos no Redis para consolidar mensagens fragmentadas."""

    def __init__(self):
        self.buffer_seconds = settings.REDIS_BUFFER_SECONDS

    async def add_message(self, phone: str, message: str) -> bool:
        """Adiciona mensagem ao buffer. Retorna True se deve processar."""
        return await redis_client.buffer_message(phone, message)

    async def wait_and_collect(self, phone: str) -> str:
        """Aguarda buffer e coleta todas as mensagens consolidadas."""
        await asyncio.sleep(self.buffer_seconds)
        messages = await redis_client.get_buffered_messages(phone)

        if not messages:
            return ""

        # Consolidar mensagens fragmentadas
        consolidated = self._consolidate(messages)
        logger.info(
            f"Buffer: {len(messages)} mensagens consolidadas para ***{phone[-4:]}"
        )
        return consolidated

    def _consolidate(self, messages: list[str]) -> str:
        """Consolida múltiplas mensagens em uma única string.

        Exemplo:
            ["oi", "quero marcar", "consulta com Dr. Carlos"]
            → "oi quero marcar consulta com Dr. Carlos"
        """
        # Remove duplicatas mantendo ordem
        seen = set()
        unique = []
        for msg in messages:
            normalized = msg.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(msg.strip())

        return " ".join(unique)


message_buffer = MessageBuffer()
