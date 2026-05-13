"""
Kairós Intelligence v2.7.1 — Cliente Paperclip (Control Plane)
Governança multi-tenant: budget, consumo, audit, configuração de clínicas.

O Paperclip é onde você registra cada clínica e configura:
- Regras de negócio específicas
- Lista de médicos e convênios
- Budget mensal de tokens
- Credenciais do Ademed
- Personalização do SOUL (saudação, tom, etc.)
"""

import logging
import httpx
from shared.config import settings

logger = logging.getLogger("paperclip")


class PaperclipClient:
    """Cliente HTTP para a API do Paperclip (Control Plane multi-tenant)."""

    def __init__(self):
        self.base_url = settings.PAPERCLIP_URL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.PAPERCLIP_AUTH_SECRET}",
        }

    # =========================================================
    # TENANT MANAGEMENT — Gerenciar clínicas
    # =========================================================

    async def create_tenant(self, tenant_data: dict) -> dict:
        """Registra nova clínica no Paperclip.

        tenant_data = {
            "tenant_id": "clinica-abc",
            "clinic_name": "Clínica ABC",
            "evolution_instance": "evolution-clinica-abc",
            "whatsapp_number": "5511999990000",
            "recepcionista_phone": "5511999991111",
            "monthly_budget_usd": 50.0,
            "ademed_url": "https://app.ademed.com.br/clinica-abc",
            "ademed_user": "user",
            "ademed_pass": "pass",
            "specialties": ["Cardiologia", "Ortopedia"],
            "operating_hours": {"Seg-Sex": "08:00-18:00", "Sáb": "08:00-12:00"},
            "clinic_address": "Rua XYZ, 123",
            "google_maps_link": "https://maps.google.com/...",
            "custom_soul": "Sempre pergunte se o paciente já tem convênio.",
            "clinic_greeting": "Olá! Bem-vindo à Clínica ABC! 😊",
        }
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/companies",
                    headers=self.headers,
                    json=tenant_data,
                    timeout=15,
                )
                response.raise_for_status()
                logger.info(f"Tenant criado: {tenant_data.get('clinic_name')}")
                return response.json()
        except Exception as e:
            logger.error(f"Erro ao criar tenant: {e}")
            return {"error": str(e)}

    async def update_tenant(self, tenant_id: str, updates: dict) -> dict:
        """Atualiza configuração de uma clínica no Paperclip."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/api/companies/{tenant_id}",
                    headers=self.headers,
                    json=updates,
                    timeout=15,
                )
                response.raise_for_status()
                logger.info(f"Tenant atualizado: {tenant_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Erro ao atualizar tenant: {e}")
            return {"error": str(e)}

    async def get_tenant_config(self, tenant_id: str) -> dict:
        """Busca configuração completa de uma clínica.

        Retorna tudo: médicos, convênios, regras, SOUL customizado, etc.
        É isso que permite UM agente servir VÁRIAS clínicas.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/companies/{tenant_id}/config",
                    headers=self.headers,
                    timeout=10,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Erro ao buscar config: {e}")
            return {"error": str(e)}

    async def list_tenants(self) -> list[dict]:
        """Lista todas as clínicas registradas no Paperclip."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/companies",
                    headers=self.headers,
                    timeout=10,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Erro ao listar tenants: {e}")
            return []

    # =========================================================
    # BUDGET — Controle de gastos
    # =========================================================

    async def check_budget(self, tenant_id: str) -> dict:
        """Verifica budget de tokens disponível para o tenant."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/companies/{tenant_id}/budget",
                    headers=self.headers,
                    timeout=10,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e), "budget_ok": True}  # Fail-open

    async def register_token_usage(
        self, tenant_id: str, agent_name: str, tokens_used: int, cost_usd: float
    ):
        """Registra consumo de tokens no Paperclip."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/api/companies/{tenant_id}/usage",
                    headers=self.headers,
                    json={
                        "agent": agent_name,
                        "tokens": tokens_used,
                        "cost_usd": cost_usd,
                    },
                    timeout=10,
                )
        except Exception:
            pass  # Non-blocking

    # =========================================================
    # AUDIT LOG — Conformidade e rastreabilidade
    # =========================================================

    async def audit_log(self, tenant_id: str, action: str, details: dict):
        """Registra ação no audit log do Paperclip."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/api/companies/{tenant_id}/audit",
                    headers=self.headers,
                    json={"action": action, **details},
                    timeout=10,
                )
        except Exception:
            pass  # Non-blocking

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    async def health_check(self) -> bool:
        """Verifica se o Paperclip está respondendo."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/health",
                    timeout=10,
                )
                return response.status_code == 200
        except Exception:
            return False


paperclip_client = PaperclipClient()
