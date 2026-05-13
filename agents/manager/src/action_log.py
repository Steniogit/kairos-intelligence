"""
Kairós Intelligence v2.7.1 — Manager: Action Logger
Log obrigatório de todas as ações no Ademed (LGPD compliance).
Formato JSON, retenção 90 dias, CPF mascarado.
"""

import json
import logging
import os
from datetime import datetime

from shared.config import settings

logger = logging.getLogger("manager.action_log")


class ActionLogger:
    """Logger de ações do Manager para auditoria e LGPD."""

    def __init__(self):
        self.log_file = os.path.join(settings.LOG_DIR, "agente3-actions.log")
        os.makedirs(settings.LOG_DIR, exist_ok=True)

    async def log(self, operation: str, params: dict, status: str, result: str):
        """Registra ação em log JSON.

        Formato:
        {
            "timestamp": "ISO 8601",
            "operation": "search_patient",
            "identifier": "***.456.***-**",  # CPF mascarado
            "status": "success|error",
            "detail": "resultado da operação"
        }
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "identifier": self._mask_identifier(params),
            "status": status,
            "detail": str(result)[:500],  # Limitar tamanho
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Erro ao escrever log de ação: {e}")

    def _mask_identifier(self, params: dict) -> str:
        """Mascara identificadores sensíveis (LGPD)."""
        cpf = params.get("cpf", "")
        if cpf:
            clean = cpf.replace(".", "").replace("-", "")
            if len(clean) >= 11:
                return f"***.{clean[3:6]}.***-**"

        phone = params.get("phone", "")
        if phone:
            return f"***{phone[-4:]}"

        return "anonymous"

    async def get_recent_actions(self, limit: int = 50) -> list[dict]:
        """Retorna últimas N ações do log."""
        if not os.path.exists(self.log_file):
            return []

        actions = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        actions.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        return actions


action_logger = ActionLogger()
