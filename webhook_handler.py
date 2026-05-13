"""
Kairós Intelligence v2.7.1 — Webhook Handler (Entry Point)
Recebe webhooks do Evolution Go e roteia para o agente correto.

Este é o ponto de entrada de TODAS as mensagens de TODAS as clínicas.
O instance_name vindo no webhook identifica a clínica.

Fluxo:
1. Evolution Go recebe WhatsApp de um paciente
2. Dispara webhook para este handler
3. O handler extrai instance_name do webhook
4. Resolve qual clínica (tenant) é via Paperclip
5. Roteia para o agente correto (Front-Desk ou Prometheus)
"""

import logging
from fastapi import FastAPI, Request

from agents.front_desk.src.main import front_desk
from agents.prometheus.src.main import prometheus
from shared.config import settings
from shared.tenant_resolver import tenant_resolver

logger = logging.getLogger("webhook")

app = FastAPI(title="Kairós Intelligence v2.7.1 — Webhook Handler")


@app.post("/webhook/evolution")
async def evolution_webhook(request: Request):
    """Processa webhook do Evolution Go.

    Payload contém:
    - instance: nome da instância Evolution (identifica a clínica)
    - data.key.remoteJid: número do remetente
    - data.message.conversation: texto da mensagem
    """
    payload = await request.json()

    # Extrair dados do webhook
    instance_name = payload.get("instance", "")
    event_type = payload.get("event", "")

    # Ignorar eventos que não são mensagens
    if event_type not in ("messages.upsert",):
        return {"status": "ignored", "event": event_type}

    data = payload.get("data", {})
    key = data.get("key", {})
    message = data.get("message", {})

    # Ignorar mensagens enviadas pelo próprio bot
    if key.get("fromMe", False):
        return {"status": "ignored", "reason": "fromMe"}

    phone = key.get("remoteJid", "").replace("@s.whatsapp.net", "")
    text = (
        message.get("conversation", "")
        or message.get("extendedTextMessage", {}).get("text", "")
    )

    if not phone or not text:
        return {"status": "ignored", "reason": "empty"}

    # ── ROTEAMENTO ──────────────────────────────────────
    # Verificar se é o gestor (Prometheus)
    if phone == settings.GESTOR_WHATSAPP:
        response = await prometheus.process_message(phone, text)
        if response:
            from shared.evolution_client import evolution_client
            await evolution_client.send_text(phone, response)
        return {"status": "ok", "agent": "prometheus"}

    # Para todos os outros → Front-Desk (multi-tenant)
    response = await front_desk.process_message(
        phone=phone,
        message=text,
        instance_name=instance_name,
    )

    if response:
        from shared.evolution_client import evolution_client
        await evolution_client.send_text(phone, response)

    return {"status": "ok", "agent": "front-desk", "instance": instance_name}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.7.1"}
