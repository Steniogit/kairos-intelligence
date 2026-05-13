"""
Kairós Intelligence v2.7.1 — Manager: Gerenciamento de Sessão PHP
Login, renovação e detecção de expiração da sessão do Ademed.
"""

import logging
from datetime import datetime, timedelta

from shared.config import settings

logger = logging.getLogger("manager.session")


class SessionManager:
    """Gerencia sessão PHP do Ademed (PHPSESSID)."""

    def __init__(self):
        self.session_cookie: str | None = None
        self.last_login: datetime | None = None
        self.session_timeout = timedelta(minutes=30)

    async def ensure_session(self):
        """Garante que a sessão está ativa. Faz login se necessário."""
        if self._is_expired():
            await self.login()

    def _is_expired(self) -> bool:
        """Verifica se a sessão expirou."""
        if not self.session_cookie or not self.last_login:
            return True
        return datetime.now() - self.last_login > self.session_timeout

    async def login(self):
        """Faz login no Ademed e obtém PHPSESSID.

        Seletores esperados (VALIDAR):
        - Input usuário: #txtUsuario or input[name="usuario"]
        - Input senha: #txtSenha or input[name="senha"]
        - Botão entrar: #btnEntrar or button[type="submit"]
        """
        logger.info("Iniciando login no Ademed")

        # TODO: Implementar com Playwright
        # async with async_playwright() as p:
        #     browser = await p.chromium.connect_over_cdp("ws://chromium:3000")
        #     page = browser.contexts[0].pages[0]
        #     await page.goto(settings.ADEMED_URL)
        #     await page.fill("#txtUsuario", settings.ADEMED_USER)
        #     await page.fill("#txtSenha", settings.ADEMED_PASS)
        #     await page.click("#btnEntrar")
        #     await page.wait_for_load_state("networkidle")
        #
        #     cookies = await page.context.cookies()
        #     for c in cookies:
        #         if c["name"] == "PHPSESSID":
        #             self.session_cookie = c["value"]
        #             break

        self.last_login = datetime.now()
        logger.info("Login no Ademed realizado com sucesso")

    async def detect_expiration(self, page_content: str) -> bool:
        """Detecta se a sessão expirou pelo conteúdo da página."""
        expiration_indicators = [
            "login", "sessão expirada", "faça login",
            "session expired", "acesso negado",
        ]
        content_lower = page_content.lower()
        return any(indicator in content_lower for indicator in expiration_indicators)

    async def refresh_session(self):
        """Renova sessão via re-login."""
        logger.info("Renovando sessão do Ademed")
        self.session_cookie = None
        self.last_login = None
        await self.login()


session_manager = SessionManager()
