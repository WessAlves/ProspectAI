"""
Classe base para scrapers.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.services.scraping.models import ScrapeResult

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Classe base para todos os scrapers."""
    
    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        user_agent: Optional[str] = None,
    ):
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Inicia o browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--ignore-certificate-errors",
            ]
        )
        self._context = await self._browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            ignore_https_errors=True,
        )
        self._context.set_default_timeout(self.timeout)
        logger.info(f"{self.__class__.__name__}: Browser iniciado")
    
    async def close(self):
        """Fecha o browser."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info(f"{self.__class__.__name__}: Browser fechado")
    
    async def new_page(self) -> Page:
        """Cria uma nova página."""
        if not self._context:
            raise RuntimeError("Browser não iniciado. Use 'async with' ou chame start()")
        return await self._context.new_page()
    
    async def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Delay aleatório para simular comportamento humano."""
        import random
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    @abstractmethod
    async def scrape(self, query: str, location: str, limit: int = 100) -> ScrapeResult:
        """
        Executa o scraping.
        
        Args:
            query: Termo de busca
            location: Localização
            limit: Limite de resultados
            
        Returns:
            ScrapeResult com os dados extraídos
        """
        pass
