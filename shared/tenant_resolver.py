"""
Kairós Intelligence v2.7.1 — Tenant Resolver
Resolve a qual clínica (tenant) pertence uma mensagem recebida.

Lógica:
1. Cada clínica tem sua própria instância Evolution Go (número WhatsApp separado)
2. Quando chega um webhook, ele traz o nome da instância
3. O Tenant Resolver consulta o Paperclip para descobrir qual tenant é
4. Retorna as configurações daquele tenant (regras, médicos, SOUL, etc.)

Resultado: UM ÚNICO agente no OpenClaw serve TODAS as clínicas.
"""

import logging
from typing import Optional

import httpx
from shared.config import settings

logger = logging.getLogger("tenant_resolver")


class TenantConfig:
    """Configuração carregada de um tenant (clínica) via Paperclip."""

    def __init__(self, data: dict):
        self.tenant_id: str = data.get("tenant_id", "")
        self.clinic_name: str = data.get("clinic_name", "")
        self.evolution_instance: str = data.get("evolution_instance", "")
        self.whatsapp_number: str = data.get("whatsapp_number", "")
        self.recepcionista_phone: str = data.get("recepcionista_phone", "")

        # Regras de negócio personalizadas
        self.business_rules: dict = data.get("business_rules", {})
        self.operating_hours: dict = data.get("operating_hours", {})
        self.specialties: list[str] = data.get("specialties", [])
        self.doctors: list[dict] = data.get("doctors", [])
        self.insurance_list: list[str] = data.get("insurance_list", [])

        # SOUL customizado (personalidade da recepcionista)
        self.custom_soul: str = data.get("custom_soul", "")
        self.clinic_greeting: str = data.get("clinic_greeting", "")
        self.clinic_address: str = data.get("clinic_address", "")
        self.google_maps_link: str = data.get("google_maps_link", "")

        # Budget
        self.monthly_budget_usd: float = data.get("monthly_budget_usd", 50.0)
        self.budget_alert_pct: int = data.get("budget_alert_pct", 80)

        # Ademed credentials (isoladas por tenant)
        self.ademed_url: str = data.get("ademed_url", "")
        self.ademed_user: str = data.get("ademed_user", "")
        self.ademed_pass: str = data.get("ademed_pass", "")

    def build_soul_prompt(self, base_soul: str) -> str:
        """Injeta dados da clínica no SOUL.md base, personalizando o agente.

        Isso é o que permite UM agente servir VÁRIAS clínicas:
        - O SOUL.md base define a personalidade genérica
        - O Paperclip injeta o contexto específico da clínica
        """
        clinic_context = f"""

--- CONTEXTO DA CLÍNICA (VIA PAPERCLIP) ---
🏥 Clínica: {self.clinic_name}
📍 Endereço: {self.clinic_address}
📱 WhatsApp: {self.whatsapp_number}
🗺️ Google Maps: {self.google_maps_link}

👨‍⚕️ Médicos Disponíveis:
"""
        for doc in self.doctors:
            specs = ", ".join(doc.get("specialties", []))
            schedule = doc.get("schedule", "")
            clinic_context += f"- Dr(a). {doc.get('name', '')} — {specs} ({schedule})\n"

        clinic_context += f"""
💳 Convênios Aceitos: {', '.join(self.insurance_list)}

🏢 Especialidades: {', '.join(self.specialties)}

⏰ Horário de Funcionamento:
"""
        for day, hours in self.operating_hours.items():
            clinic_context += f"- {day}: {hours}\n"

        if self.custom_soul:
            clinic_context += f"\n📝 Instruções Específicas:\n{self.custom_soul}\n"

        if self.clinic_greeting:
            clinic_context += f"\n👋 Saudação Padrão: {self.clinic_greeting}\n"

        return base_soul + clinic_context


class TenantResolver:
    """Resolve instância Evolution → tenant_id → TenantConfig.

    Mantém cache em memória para evitar chamadas repetidas ao Paperclip.
    Cache é invalidado a cada 5 minutos.
    """

    def __init__(self):
        self._cache: dict[str, TenantConfig] = {}
        self._instance_map: dict[str, str] = {}  # instance_name → tenant_id

    async def resolve_by_instance(self, instance_name: str) -> Optional[TenantConfig]:
        """Resolve tenant pela instância do Evolution Go.

        Cada clínica tem sua própria instância Evolution = número WhatsApp.
        Quando chega webhook, ele informa de qual instância veio.
        """
        # Verificar cache
        if instance_name in self._instance_map:
            tenant_id = self._instance_map[instance_name]
            if tenant_id in self._cache:
                return self._cache[tenant_id]

        # Consultar Paperclip
        config = await self._fetch_from_paperclip(instance_name)
        if config:
            self._instance_map[instance_name] = config.tenant_id
            self._cache[config.tenant_id] = config
            logger.info(
                f"Tenant resolvido: {instance_name} → "
                f"{config.tenant_id} ({config.clinic_name})"
            )
            return config

        logger.warning(f"Tenant não encontrado para instância: {instance_name}")
        return None

    async def resolve_by_tenant_id(self, tenant_id: str) -> Optional[TenantConfig]:
        """Resolve tenant diretamente pelo ID."""
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        config = await self._fetch_tenant_config(tenant_id)
        if config:
            self._cache[tenant_id] = config
            return config
        return None

    async def _fetch_from_paperclip(self, instance_name: str) -> Optional[TenantConfig]:
        """Consulta Paperclip para descobrir qual tenant pertence à instância."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.PAPERCLIP_URL}/api/tenants/resolve",
                    params={"evolution_instance": instance_name},
                    timeout=10,
                )
                if response.status_code == 200:
                    return TenantConfig(response.json())
                return None
        except Exception as e:
            logger.error(f"Erro ao consultar Paperclip: {e}")
            return None

    async def _fetch_tenant_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """Busca configuração completa do tenant no Paperclip."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.PAPERCLIP_URL}/api/companies/{tenant_id}/config",
                    timeout=10,
                )
                if response.status_code == 200:
                    return TenantConfig(response.json())
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar config do tenant: {e}")
            return None

    async def list_all_tenants(self) -> list[TenantConfig]:
        """Lista todos os tenants ativos no Paperclip."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.PAPERCLIP_URL}/api/companies",
                    timeout=10,
                )
                if response.status_code == 200:
                    return [TenantConfig(t) for t in response.json()]
                return []
        except Exception as e:
            logger.error(f"Erro ao listar tenants: {e}")
            return []

    def invalidate_cache(self, tenant_id: str = ""):
        """Invalida cache de um tenant ou de todos."""
        if tenant_id:
            self._cache.pop(tenant_id, None)
            # Remover do instance_map também
            self._instance_map = {
                k: v for k, v in self._instance_map.items() if v != tenant_id
            }
        else:
            self._cache.clear()
            self._instance_map.clear()
        logger.info(f"Cache invalidado: {tenant_id or 'ALL'}")


tenant_resolver = TenantResolver()
