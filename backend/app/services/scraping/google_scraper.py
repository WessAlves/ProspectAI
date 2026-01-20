"""
Scraper para Google Search.

Extrai informações de empresas/sites dos resultados de busca do Google.
"""

import re
import time
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urlparse

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from app.services.scraping.base import BaseScraper
from app.services.scraping.models import ScrapedBusiness, ScrapedContact, ScrapeResult

logger = logging.getLogger(__name__)


class GoogleScraper(BaseScraper):
    """
    Scraper para extrair dados do Google Search.
    
    Extrai URLs, snippets e informações de contato de sites.
    
    Exemplo de uso:
        async with GoogleScraper() as scraper:
            result = await scraper.scrape("empresas de TI", "São Paulo", limit=30)
            for business in result.businesses:
                print(business.name, business.website)
    """
    
    BASE_URL = "https://www.google.com/search"
    
    async def scrape(
        self,
        query: str,
        location: str,
        limit: int = 100,
    ) -> ScrapeResult:
        """
        Executa scraping no Google Search.
        
        Args:
            query: Termo de busca
            location: Localização para contextualizar busca
            limit: Número máximo de resultados
            
        Returns:
            ScrapeResult com os negócios encontrados
        """
        start_time = time.time()
        businesses: List[ScrapedBusiness] = []
        
        try:
            page = await self.new_page()
            
            # Construir query com localização
            search_query = f"{query} {location}"
            url = f"{self.BASE_URL}?q={quote_plus(search_query)}&num=100"
            
            logger.info(f"GoogleScraper: Acessando {url}")
            await page.goto(url, wait_until="networkidle")
            
            # Aceitar cookies se necessário
            await self._accept_cookies(page)
            
            # Extrair resultados
            page_num = 1
            while len(businesses) < limit:
                page_results = await self._extract_search_results(page)
                
                for result in page_results:
                    if len(businesses) >= limit:
                        break
                    businesses.append(result)
                
                # Tentar ir para próxima página
                if len(businesses) < limit:
                    has_next = await self._go_to_next_page(page)
                    if not has_next:
                        break
                    page_num += 1
                    await self.random_delay(2, 4)
            
            await page.close()
            
            duration = time.time() - start_time
            
            return ScrapeResult(
                success=True,
                businesses=businesses,
                total_found=len(businesses),
                query=query,
                location=location,
                duration_seconds=round(duration, 2),
            )
            
        except Exception as e:
            logger.error(f"GoogleScraper: Erro - {str(e)}")
            duration = time.time() - start_time
            return ScrapeResult(
                success=False,
                businesses=businesses,
                total_found=len(businesses),
                query=query,
                location=location,
                error=str(e),
                duration_seconds=round(duration, 2),
            )
    
    async def _accept_cookies(self, page: Page):
        """Aceita cookies se o banner aparecer."""
        try:
            accept_button = page.locator('button:has-text("Aceitar tudo")')
            if await accept_button.count() > 0:
                await accept_button.first.click()
                await self.random_delay(1, 2)
        except Exception:
            pass
    
    async def _extract_search_results(self, page: Page) -> List[ScrapedBusiness]:
        """Extrai resultados da página atual de busca."""
        businesses: List[ScrapedBusiness] = []
        
        # Seletores para resultados orgânicos do Google
        result_selectors = [
            'div.g',  # Resultado padrão
            'div[data-hveid]',  # Resultado com data attribute
        ]
        
        for selector in result_selectors:
            results = await page.query_selector_all(selector)
            
            for result in results:
                try:
                    business = await self._extract_from_result(result)
                    if business:
                        businesses.append(business)
                except Exception as e:
                    logger.debug(f"Erro ao extrair resultado: {e}")
                    continue
        
        # Remover duplicatas por website
        seen = set()
        unique_businesses = []
        for b in businesses:
            if b.website and b.website not in seen:
                seen.add(b.website)
                unique_businesses.append(b)
        
        logger.info(f"GoogleScraper: Extraídos {len(unique_businesses)} resultados da página")
        return unique_businesses
    
    async def _extract_from_result(self, result) -> Optional[ScrapedBusiness]:
        """Extrai dados de um resultado de busca."""
        try:
            # Título/Nome
            title_el = await result.query_selector('h3')
            if not title_el:
                return None
            name = await title_el.inner_text()
            
            # Link
            link_el = await result.query_selector('a')
            website = None
            if link_el:
                href = await link_el.get_attribute('href')
                if href and href.startswith('http'):
                    website = href
            
            if not website:
                return None
            
            # Descrição/Snippet
            snippet_el = await result.query_selector('div[data-sncf]')
            if not snippet_el:
                snippet_el = await result.query_selector('span:not([class])')
            
            description = ""
            if snippet_el:
                description = await snippet_el.inner_text()
            
            # Extrair domínio como categoria
            domain = urlparse(website).netloc
            
            business = ScrapedBusiness(
                name=name.strip(),
                website=website,
                source="google_search",
                extra_data={
                    "description": description[:500] if description else None,
                    "domain": domain,
                },
            )
            
            return business
            
        except Exception as e:
            logger.debug(f"Erro ao extrair resultado: {e}")
            return None
    
    async def _go_to_next_page(self, page: Page) -> bool:
        """Navega para a próxima página de resultados."""
        try:
            next_button = await page.query_selector('a#pnnext')
            if next_button:
                await next_button.click()
                await page.wait_for_load_state('networkidle')
                return True
            return False
        except Exception:
            return False
    
    async def extract_contact_from_website(
        self,
        url: str,
    ) -> Optional[ScrapedContact]:
        """
        Extrai informações de contato de um website.
        
        Args:
            url: URL do website
            
        Returns:
            ScrapedContact com emails, telefones e redes sociais
        """
        try:
            page = await self.new_page()
            await page.goto(url, wait_until="networkidle", timeout=15000)
            
            # Extrair HTML da página
            html_content = await page.content()
            
            contact = ScrapedContact(source_url=url)
            
            # Extrair emails usando regex
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = list(set(re.findall(email_pattern, html_content)))
            # Filtrar emails inválidos comuns
            contact.emails = [
                e for e in emails
                if not any(x in e.lower() for x in ['example', 'test', 'domain', '.png', '.jpg', '.gif'])
            ][:5]  # Limitar a 5 emails
            
            # Extrair telefones brasileiros
            phone_patterns = [
                r'\(?\d{2}\)?\s*\d{4,5}[-.\s]?\d{4}',  # (11) 99999-9999
                r'\d{2}\s*\d{4,5}\s*\d{4}',  # 11 99999 9999
            ]
            phones = []
            for pattern in phone_patterns:
                found = re.findall(pattern, html_content)
                phones.extend(found)
            contact.phones = list(set(phones))[:5]
            
            # Extrair redes sociais
            social_patterns = {
                'facebook': r'(?:facebook\.com|fb\.com)/([a-zA-Z0-9.]+)',
                'instagram': r'instagram\.com/([a-zA-Z0-9_.]+)',
                'linkedin': r'linkedin\.com/(?:company|in)/([a-zA-Z0-9-]+)',
                'twitter': r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)',
                'youtube': r'youtube\.com/(?:c/|channel/|user/)?([a-zA-Z0-9_-]+)',
                'whatsapp': r'(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d+)',
            }
            
            for platform, pattern in social_patterns.items():
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    contact.social_media[platform] = matches[0]
            
            # Tentar encontrar página de contato
            contact_links = await page.query_selector_all('a[href*="contato"], a[href*="contact"], a[href*="fale"]')
            for link in contact_links[:3]:
                href = await link.get_attribute('href')
                if href:
                    contact.contact_forms.append(href)
            
            await page.close()
            return contact
            
        except Exception as e:
            logger.error(f"Erro ao extrair contato de {url}: {e}")
            return None
    
    async def search_with_contact_extraction(
        self,
        query: str,
        location: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Busca no Google e extrai contatos de cada resultado.
        
        Args:
            query: Termo de busca
            location: Localização
            limit: Limite de resultados
            
        Returns:
            Lista de dicts com business + contact
        """
        results = []
        
        # Primeiro, buscar no Google
        search_result = await self.scrape(query, location, limit)
        
        if not search_result.success:
            return results
        
        # Para cada resultado, extrair contatos
        for business in search_result.businesses:
            if business.website:
                contact = await self.extract_contact_from_website(business.website)
                
                result = {
                    "business": business.to_dict(),
                    "contact": contact.to_dict() if contact else None,
                }
                results.append(result)
                
                # Delay entre requisições
                await self.random_delay(2, 4)
        
        return results
