"""
Kairós Intelligence v2.7.1 — Cliente Paperclip
Verificação de budget, registro de consumo de tokens, audit log.
"""

import httpx
from shared.config import settings


class PaperclipClient:
    """Cliente HTTP para a API do Paperclip (Control Plane)."""

    def __init__(self):
        self.base_url = settings.PAPERCLIP_URL
        self.headers = {"Content-Type": "application/json"}

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
