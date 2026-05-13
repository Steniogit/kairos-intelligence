"""
Kairós Intelligence v2.7.1 — Agente 3: Manager (Clínico)
Único ponto de contato com o sistema Ademed.
Orquestrador lógico por clínica: leitura (Crawl4AI) + escrita (Playwright).
"""

import asyncio
import logging
from datetime import datetime

from shared.config import settings
from shared.redis_client import redis_client
from agents.manager.src.crawl4ai_reader import ademed_reader
from agents.manager.src.playwright_writer import ademed_writer
from agents.manager.src.session_manager import session_manager
from agents.manager.src.action_log import action_logger

logger = logging.getLogger("manager")


class ManagerAgent:
    """Orquestrador de operações no Ademed — fila sequencial."""

    def __init__(self):
        self._processing = False
        self._queue_name = "manager_tasks"

    async def enqueue(self, operation: str, params: dict) -> str:
        """Enfileira operação para processamento sequencial."""
        task = {
            "operation": operation,
            "params": params,
            "timestamp": datetime.now().isoformat(),
        }
        await redis_client.enqueue_task(self._queue_name, task)
        logger.info(f"Tarefa enfileirada: {operation}")
        return f"Operação '{operation}' adicionada à fila."

    async def process_queue(self):
        """Loop principal: processa tarefas da fila uma por vez."""
        logger.info("Manager: processador de fila iniciado")
        while True:
            task = await redis_client.dequeue_task(self._queue_name, timeout=5)
            if task is None:
                continue

            self._processing = True
            operation = task.get("operation", "")
            params = task.get("params", {})

            try:
                result = await self._execute(operation, params)
                await action_logger.log(operation, params, "success", result)
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Erro na operação {operation}: {error_msg}")
                await action_logger.log(operation, params, "error", error_msg)
                await self._handle_failure(operation, params, error_msg)
            finally:
                self._processing = False

    async def _execute(self, operation: str, params: dict) -> str:
        """Executa operação no Ademed."""
        # Garantir sessão ativa
        await session_manager.ensure_session()

        operations_map = {
            # Leitura (Crawl4AI)
            "search_patient": ademed_reader.search_patient,
            "check_availability": ademed_reader.check_availability,
            "get_appointments_today": ademed_reader.get_appointments_today,
            "get_doctors": ademed_reader.get_doctors,
            "get_insurance_list": ademed_reader.get_insurance_list,
            # Escrita (Playwright)
            "register_patient": ademed_writer.register_patient,
            "create_appointment": ademed_writer.create_appointment,
            "cancel_appointment": ademed_writer.cancel_appointment,
            "upload_document": ademed_writer.upload_document,
            "update_status": ademed_writer.update_status,
            "create_consultation_guide": ademed_writer.create_consultation_guide,
        }

        handler = operations_map.get(operation)
        if not handler:
            raise ValueError(f"Operação desconhecida: {operation}")

        return await handler(params)

    async def _handle_failure(self, operation: str, params: dict, error: str):
        """Fallback quando Ademed está fora do ar."""
        import json
        import os

        pending_file = os.path.join(settings.LOG_DIR, "agendamentos-pendentes.json")

        pending = {
            "operation": operation,
            "params": params,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

        # Salvar em fila pendente
        try:
            existing = []
            if os.path.exists(pending_file):
                with open(pending_file, "r") as f:
                    existing = json.load(f)
            existing.append(pending)
            with open(pending_file, "w") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        logger.warning(f"Operação {operation} salva em fila pendente")


manager = ManagerAgent()
