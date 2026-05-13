"""
Kairós Intelligence v2.7.1 — Agente 2: Front-Desk (Atendimento)
Recepcionista virtual MULTI-TENANT.

ARQUITETURA:
- UM ÚNICO agente no OpenClaw
- Serve TODAS as clínicas registradas no Paperclip
- Cada clínica tem: regras, médicos, convênios, SOUL personalizado
- O Tenant Resolver identifica qual clínica é (via instância Evolution)
- O Paperclip fornece o contexto específico daquela clínica
- O GraphRAG busca dados no namespace da clínica (isolamento)
"""

import asyncio
import logging
from datetime import datetime

import httpx
from shared.config import settings
from shared.redis_client import redis_client
from shared.evolution_client import evolution_client
from shared.paperclip_client import paperclip_client
from shared.tenant_resolver import tenant_resolver, TenantConfig
from graphrag.retriever import retriever

logger = logging.getLogger("front-desk")


class FrontDeskAgent:
    """Agente de atendimento multi-tenant.

    UM agente → VÁRIAS clínicas.
    O comportamento muda de acordo com o tenant (via Paperclip).
    """

    def __init__(self):
        self.model = settings.DEEPSEEK_MODEL
        self._base_soul = self._load_base_soul()
        self.timeout_seconds = 1800  # 30 minutos
        self.max_off_topic = 3

    def _load_base_soul(self) -> str:
        """Carrega SOUL.md base (genérico, sem dados de clínica específica).

        Este SOUL é enriquecido em runtime com dados do Paperclip
        para cada clínica diferente.
        """
        try:
            with open("agents/front-desk/SOUL.md", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Você é a recepcionista virtual da clínica."

    async def process_message(
        self, phone: str, message: str, instance_name: str
    ) -> str:
        """Processa mensagem do paciente.

        Args:
            phone: Número do paciente
            message: Texto da mensagem
            instance_name: Nome da instância Evolution (identifica a clínica)

        Fluxo multi-tenant:
        1. Resolve instance_name → tenant (via Paperclip)
        2. Carrega config da clínica (médicos, convênios, SOUL)
        3. Injeta contexto no SOUL base → SOUL personalizado
        4. Busca contexto do paciente no GraphRAG (namespace da clínica)
        5. Chama LLM com SOUL personalizado + contexto
        """
        # ── 1. RESOLVER TENANT ──────────────────────────────
        tenant = await tenant_resolver.resolve_by_instance(instance_name)
        if not tenant:
            logger.error(f"Tenant não encontrado para instância: {instance_name}")
            return "Desculpe, estamos com uma instabilidade. Tente novamente em breve! 😊"

        clinic_id = tenant.tenant_id

        # ── 2. BUFFER 8 SEGUNDOS ───────────────────────────
        is_first = await redis_client.buffer_message(phone, message)
        if is_first:
            await asyncio.sleep(settings.REDIS_BUFFER_SECONDS)
            messages = await redis_client.get_buffered_messages(phone)
            consolidated = " ".join(messages)
        else:
            return ""  # Já está sendo processada

        # ── 3. CHECK BUDGET (PAPERCLIP) ─────────────────────
        budget = await paperclip_client.check_budget(clinic_id)
        if not budget.get("budget_ok", True):
            logger.warning(f"Budget excedido para clínica {tenant.clinic_name}")
            return ("Estamos com muita demanda agora. "
                    "Por favor, tente novamente em breve! 😊")

        # ── 4. CONTEXTO GRAPHRAG (namespace da clínica) ─────
        context = retriever.get_full_context(clinic_id, phone, consolidated)

        # ── 5. ESTADO DA CONVERSA (Redis) ───────────────────
        state = await redis_client.get_conversation_state(phone)
        history = state.get("history", []) if state else []
        off_topic_count = state.get("off_topic_count", 0) if state else 0

        # ── 6. MONTAR SOUL PERSONALIZADO ────────────────────
        # SOUL base + dados do Paperclip (clínica) + dados do GraphRAG (paciente)
        personalized_soul = tenant.build_soul_prompt(self._base_soul)
        context_prompt = self._build_context_prompt(context)

        history.append({"role": "user", "content": consolidated})

        # ── 7. CHAMAR LLM ──────────────────────────────────
        response = await self._call_llm(history, personalized_soul, context_prompt)

        # ── 8. SALVAR ESTADO ────────────────────────────────
        history.append({"role": "assistant", "content": response})
        await redis_client.set_conversation_state(
            phone,
            {
                "history": history[-20:],
                "off_topic_count": off_topic_count,
                "clinic_id": clinic_id,
                "instance_name": instance_name,
                "last_activity": datetime.now().isoformat(),
            },
            ttl=self.timeout_seconds,
        )

        # ── 9. JANELA META ─────────────────────────────────
        await redis_client.update_window(phone)

        # ── 10. REGISTRAR CONSUMO NO PAPERCLIP ─────────────
        await paperclip_client.register_token_usage(
            tenant_id=clinic_id,
            agent_name="front-desk",
            tokens_used=len(response.split()) * 2,
            cost_usd=0.0005,
        )

        return response

    def _build_context_prompt(self, context: dict) -> str:
        """Monta prompt contextual com dados do GraphRAG (paciente)."""
        parts = []

        if context.get("has_patient"):
            p = context["patient"]
            parts.append(f"PACIENTE IDENTIFICADO: {p.get('name', 'N/A')}")
            if p.get("doctors"):
                docs = ", ".join([d["doctor"] for d in p["doctors"]])
                parts.append(f"Médicos anteriores: {docs}")
            if p.get("insurances"):
                parts.append(f"Convênio: {', '.join(p['insurances'])}")

        if context.get("faq_matches"):
            parts.append("\nFAQ RELEVANTE:")
            for faq in context["faq_matches"][:3]:
                parts.append(
                    f"- {faq['metadata'].get('question', '')}: "
                    f"{faq['metadata'].get('answer', '')}"
                )

        return "\n".join(parts) if parts else ""

    async def _call_llm(
        self, history: list[dict], soul: str, context: str = ""
    ) -> str:
        """Chama DeepSeek-V4 Flash com SOUL personalizado."""
        system = soul
        if context:
            system += f"\n\n--- CONTEXTO DO PACIENTE ---\n{context}"

        messages = [{"role": "system", "content": system}] + history

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
                        "temperature": 0.8,
                        "max_tokens": 1024,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erro DeepSeek: {e}")
            return ("Desculpe, estou com uma instabilidade técnica momentânea. "
                    "Pode tentar novamente em alguns segundos? 😊")

    async def handle_timeout(self, phone: str):
        """Encerra conversa por inatividade (30 min)."""
        await evolution_client.send_text(
            phone,
            "Parece que você ficou um tempinho sem responder! 😊 "
            "Tudo bem, quando precisar é só mandar uma mensagem. "
            "Estarei aqui! 💙",
        )
        await redis_client.clear_conversation(phone)
        logger.info(f"Conversa encerrada por timeout: ***{phone[-4:]}")


# Instância única — serve TODAS as clínicas
front_desk = FrontDeskAgent()
