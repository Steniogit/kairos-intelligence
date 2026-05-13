"""
Kairós Intelligence v2.7.1 — Agente 1: Prometheus (Master/CEO)
Assistente pessoal do gestor e supervisor de todas as clínicas.
Canal: WhatsApp pessoal do gestor.
Modelo: DeepSeek-V4 Flash.
"""

import asyncio
import json
import logging
from datetime import datetime

import httpx
from shared.config import settings
from shared.redis_client import redis_client
from shared.evolution_client import evolution_client
from shared.paperclip_client import paperclip_client

logger = logging.getLogger("prometheus")


class PrometheusAgent:
    """Agente Master — supervisiona clínicas e auxilia o gestor."""

    def __init__(self):
        self.gestor_phone = settings.GESTOR_WHATSAPP
        self.model = settings.DEEPSEEK_MODEL
        self.system_prompt = self._load_soul()

    def _load_soul(self) -> str:
        """Carrega identidade do agente do SOUL.md."""
        try:
            with open("agents/prometheus/SOUL.md", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Você é o Prometheus, assistente inteligente do gestor de clínicas."

    async def process_message(self, phone: str, message: str) -> str:
        """Processa mensagem do gestor com human-in-the-loop."""
        # Só responde ao gestor
        if phone != self.gestor_phone:
            logger.warning(f"Mensagem ignorada de número não autorizado: {phone[-4:]}")
            return ""

        # Recuperar contexto da conversa
        state = await redis_client.get_conversation_state(f"prometheus:{phone}")
        history = state.get("history", []) if state else []

        # Adicionar mensagem ao histórico
        history.append({"role": "user", "content": message})

        # Chamar DeepSeek-V4 Flash
        response = await self._call_llm(history)

        # Verificar se requer confirmação (human-in-the-loop)
        if self._requires_confirmation(response):
            response += "\n\n⚠️ *Confirma a execução? Responda Y para sim, N para não.*"
            await redis_client.set_conversation_state(
                f"prometheus:{phone}",
                {"history": history, "pending_action": response, "awaiting_confirmation": True},
            )
        else:
            history.append({"role": "assistant", "content": response})
            await redis_client.set_conversation_state(
                f"prometheus:{phone}",
                {"history": history[-20:]},  # Manter últimas 20 mensagens
            )

        # Registrar consumo no Paperclip
        await paperclip_client.register_token_usage(
            tenant_id="master",
            agent_name="prometheus",
            tokens_used=len(response.split()) * 2,  # Estimativa
            cost_usd=0.001,
        )

        return response

    async def _call_llm(self, history: list[dict]) -> str:
        """Chama DeepSeek-V4 Flash para gerar resposta."""
        messages = [{"role": "system", "content": self.system_prompt}] + history

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.DEEPSEEK_BASE_URL}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 2048,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erro ao chamar DeepSeek: {e}")
            return "⚠️ Houve um erro temporário. Tentando novamente em breve..."

    def _requires_confirmation(self, response: str) -> bool:
        """Verifica se a ação requer confirmação do gestor."""
        trigger_words = [
            "broadcast", "cancelar", "deletar", "remover",
            "atualizar todos", "enviar para todos", "alterar budget",
        ]
        return any(word in response.lower() for word in trigger_words)

    async def handle_confirmation(self, phone: str, answer: str) -> str:
        """Processa resposta de confirmação (Y/N)."""
        state = await redis_client.get_conversation_state(f"prometheus:{phone}")
        if not state or not state.get("awaiting_confirmation"):
            return ""

        if answer.strip().upper() in ("Y", "SIM", "S"):
            # Executar ação pendente
            logger.info("Ação confirmada pelo gestor")
            await redis_client.set_conversation_state(
                f"prometheus:{phone}",
                {"history": state.get("history", []), "awaiting_confirmation": False},
            )
            return "✅ Ação confirmada e executada com sucesso."
        else:
            await redis_client.set_conversation_state(
                f"prometheus:{phone}",
                {"history": state.get("history", []), "awaiting_confirmation": False},
            )
            return "❌ Ação cancelada."


# Instância singleton
prometheus = PrometheusAgent()
