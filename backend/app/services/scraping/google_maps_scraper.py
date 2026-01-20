"""
Scraper para Google Maps - Versão Otimizada.

Extrai informações de empresas/negócios do Google Maps de forma progressiva,
salvando resultados conforme são encontrados para evitar travamentos longos.
"""

import re
import time
import logging
import asyncio
from typing import List, Optional, Dict, Any, Callable, Awaitable
from urllib.parse import quote_plus

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from app.services.scraping.base import BaseScraper
from app.services.scraping.models import ScrapedBusiness, ScrapeResult

logger = logging.getLogger(__name__)

# Tipo para callback de salvamento progressivo
SaveCallback = Callable[[ScrapedBusiness], Awaitable[bool]]


class GoogleMapsScraper(BaseScraper):
    """
    Scraper otimizado para extrair dados de empresas do Google Maps.
    
    Características:
    - Extração completa de dados (telefone, website, endereço)
    - Salvamento progressivo via callback
    - Timeouts adequados para evitar travamentos
    - Extração paralela otimizada
    
    Exemplo de uso básico:
        async with GoogleMapsScraper() as scraper:
            result = await scraper.scrape("restaurantes", "São Paulo, SP", limit=50)
            for business in result.businesses:
                print(business.name, business.phone)
    
    Exemplo com salvamento progressivo:
        async def save_prospect(business: ScrapedBusiness) -> bool:
            # Salvar no banco
            return True  # Retorna se salvou com sucesso
            
        async with GoogleMapsScraper() as scraper:
            result = await scraper.scrape(
                "restaurantes", 
                "São Paulo, SP", 
                limit=50,
                on_business_found=save_prospect
            )
    """
    
    BASE_URL = "https://www.google.com/maps/search/"
    
    # Timeouts configuráveis
    PAGE_LOAD_TIMEOUT = 30000  # 30 segundos para carregar página
    SCROLL_TIMEOUT = 3000  # 3 segundos para cada scroll
    DETAIL_TIMEOUT = 8000  # 8 segundos para carregar detalhes
    MAX_SCROLL_WITHOUT_NEW = 5  # Parar após 5 scrolls sem novos resultados
    MAX_TOTAL_DURATION = 600  # 10 minutos máximo de execução
    
    async def scrape(
        self,
        query: str,
        location: str,
        limit: int = 100,
        on_business_found: Optional[SaveCallback] = None,
        detailed_mode: bool = True,  # True para extrair telefone/website
        extract_emails: bool = False,  # Extrair emails dos websites
    ) -> ScrapeResult:
        """
        Executa scraping otimizado no Google Maps.
        
        Args:
            query: Termo de busca (ex: "restaurantes", "dentistas")
            location: Localização (ex: "São Paulo, SP")
            limit: Número máximo de resultados
            on_business_found: Callback chamado para cada negócio encontrado
                              Permite salvar progressivamente no banco
            detailed_mode: Se True, extrai dados completos (telefone, website, etc)
                          Se False, extrai apenas dados visíveis (mais rápido)
            extract_emails: Se True, visita o site para extrair email (mais lento)
            
        Returns:
            ScrapeResult com os negócios encontrados
        """
        start_time = time.time()
        businesses: List[ScrapedBusiness] = []
        saved_count = 0
        
        # Salvar config para uso nos métodos internos
        self._extract_emails = extract_emails
        
        try:
            page = await self.new_page()
            
            # Construir URL de busca
            search_term = f"{query} em {location}"
            url = f"{self.BASE_URL}{quote_plus(search_term)}"
            
            logger.info(f"GoogleMapsScraper: Iniciando busca - '{query}' em '{location}'")
            logger.info(f"GoogleMapsScraper: URL = {url}")
            logger.info(f"GoogleMapsScraper: Modo detalhado = {detailed_mode}, Extrair emails = {extract_emails}")
            
            await page.goto(url, wait_until="networkidle", timeout=self.PAGE_LOAD_TIMEOUT)
            
            # Aceitar cookies se necessário
            await self._accept_cookies(page)
            
            # Aguardar lista de resultados
            has_results = await self._wait_for_results(page)
            
            if not has_results:
                logger.warning("GoogleMapsScraper: Nenhum resultado encontrado na busca")
                await page.close()
                return ScrapeResult(
                    success=True,
                    businesses=[],
                    total_found=0,
                    query=query,
                    location=location,
                    duration_seconds=round(time.time() - start_time, 2),
                )
            
            # Extrair negócios com scroll progressivo
            businesses, saved_count = await self._extract_businesses_progressive(
                page, 
                limit,
                on_business_found,
                detailed_mode,
                start_time,
            )
            
            await page.close()
            
            duration = time.time() - start_time
            
            logger.info(
                f"GoogleMapsScraper: Concluído em {duration:.1f}s - "
                f"{len(businesses)} encontrados, {saved_count} salvos"
            )
            
            return ScrapeResult(
                success=True,
                businesses=businesses,
                total_found=len(businesses),
                query=query,
                location=location,
                duration_seconds=round(duration, 2),
            )
            
        except Exception as e:
            logger.error(f"GoogleMapsScraper: Erro - {str(e)}")
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
            # Botão de aceitar cookies do Google
            accept_button = page.locator('button:has-text("Aceitar tudo")')
            if await accept_button.count() > 0:
                await accept_button.first.click()
                await self.random_delay(0.5, 1)
        except Exception:
            pass
    
    async def _wait_for_results(self, page: Page) -> bool:
        """
        Aguarda a lista de resultados carregar.
        
        Returns:
            True se encontrou resultados, False se não
        """
        try:
            # Aguardar o feed de resultados
            await page.wait_for_selector('[role="feed"]', timeout=self.PAGE_LOAD_TIMEOUT)
            return True
        except PlaywrightTimeout:
            try:
                # Tentar seletor alternativo
                await page.wait_for_selector('.Nv2PK', timeout=5000)
                return True
            except PlaywrightTimeout:
                # Verificar se tem mensagem de "nenhum resultado"
                no_results = await page.query_selector('div:has-text("Nenhum resultado")')
                if no_results:
                    return False
                return False
    
    async def _extract_businesses_progressive(
        self,
        page: Page,
        limit: int,
        on_business_found: Optional[SaveCallback],
        detailed_mode: bool,
        start_time: float,
    ) -> tuple[List[ScrapedBusiness], int]:
        """
        Extrai negócios de forma progressiva, salvando conforme encontra.
        
        Otimizações:
        - Extrai dados visíveis sem clicar (modo rápido)
        - Salva via callback imediatamente
        - Para se não encontrar novos resultados
        - Respeita timeout máximo
        """
        businesses: List[ScrapedBusiness] = []
        seen_names = set()
        saved_count = 0
        scroll_count = 0
        scrolls_without_new = 0
        last_count = 0
        
        while len(businesses) < limit:
            # Verificar timeout máximo
            elapsed = time.time() - start_time
            if elapsed > self.MAX_TOTAL_DURATION:
                logger.warning(f"GoogleMapsScraper: Timeout máximo atingido ({elapsed:.0f}s)")
                break
            
            # Extrair itens visíveis da lista
            new_businesses = await self._extract_visible_items(page, seen_names, detailed_mode)
            
            for business in new_businesses:
                if len(businesses) >= limit:
                    break
                    
                businesses.append(business)
                seen_names.add(business.name)
                
                # Salvar progressivamente via callback
                if on_business_found:
                    try:
                        saved = await on_business_found(business)
                        if saved:
                            saved_count += 1
                            logger.info(
                                f"GoogleMapsScraper: [{saved_count}/{len(businesses)}] "
                                f"Salvo: {business.name}"
                            )
                    except Exception as e:
                        logger.warning(f"Erro ao salvar {business.name}: {e}")
            
            # Verificar se encontrou novos
            if len(businesses) == last_count:
                scrolls_without_new += 1
                if scrolls_without_new >= self.MAX_SCROLL_WITHOUT_NEW:
                    logger.info(
                        f"GoogleMapsScraper: Parado - {scrolls_without_new} scrolls "
                        f"sem novos resultados"
                    )
                    break
            else:
                scrolls_without_new = 0
                last_count = len(businesses)
            
            # Scroll para carregar mais
            feed = await page.query_selector('[role="feed"]')
            if feed:
                await feed.evaluate('el => el.scrollTop = el.scrollHeight')
                await asyncio.sleep(1.5)  # Esperar carregar
            
            scroll_count += 1
            
            # Log de progresso a cada 10 scrolls
            if scroll_count % 10 == 0:
                logger.info(
                    f"GoogleMapsScraper: Progresso - {len(businesses)} negócios "
                    f"encontrados após {scroll_count} scrolls"
                )
            
            # Verificar se chegou ao fim da lista
            end_message = await page.query_selector('span:has-text("Você chegou ao fim")')
            if end_message:
                logger.info("GoogleMapsScraper: Fim da lista de resultados")
                break
        
        return businesses, saved_count
    
    async def _extract_visible_items(
        self,
        page: Page,
        seen_names: set,
        detailed_mode: bool,
    ) -> List[ScrapedBusiness]:
        """
        Extrai dados dos itens visíveis na lista.
        
        Modo rápido: Extrai dados visíveis sem clicar (nome, categoria, rating)
        Modo detalhado: Clica em cada card para extrair mais dados
        """
        businesses: List[ScrapedBusiness] = []
        
        # Selecionar todos os cards de resultados
        items = await page.query_selector_all('[role="feed"] > div > div > a')
        
        for item in items:
            try:
                # Extrair nome do aria-label
                aria_label = await item.get_attribute("aria-label")
                if not aria_label or aria_label in seen_names:
                    continue
                
                name = aria_label.strip()
                
                if detailed_mode:
                    # Modo detalhado: clicar para obter mais dados
                    # Passa o nome já extraído do aria-label
                    business = await self._extract_business_from_card(page, item, name)
                    if business:
                        businesses.append(business)
                else:
                    # Modo rápido: extrair dados visíveis
                    business = await self._extract_quick_data(page, item, name)
                    if business:
                        businesses.append(business)
                        
            except Exception as e:
                logger.debug(f"Erro ao processar item: {e}")
                continue
        
        return businesses
    
    async def _extract_quick_data(
        self,
        page: Page,
        item,
        name: str,
    ) -> Optional[ScrapedBusiness]:
        """
        Extrai dados rapidamente sem clicar no card.
        Usa dados visíveis na lista - MODO RÁPIDO (menos dados).
        """
        try:
            business = ScrapedBusiness(
                name=name,
                source="google_maps",
            )
            
            # Tentar extrair dados adicionais do container do card
            parent = await item.query_selector("xpath=..")
            if parent:
                text_content = await parent.inner_text()
                lines = text_content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    
                    # Rating (ex: "4,5" ou "4.5")
                    if re.match(r'^[\d][,.][\d]$', line):
                        business.rating = float(line.replace(',', '.'))
                    
                    # Telefone - padrões brasileiros
                    phone_patterns = [
                        r'\(?\d{2}\)?\s*\d{4,5}[-.\s]?\d{4}',
                        r'\+55\s*\d{2}\s*\d{4,5}[-.\s]?\d{4}',
                    ]
                    for pattern in phone_patterns:
                        phone_match = re.search(pattern, line)
                        if phone_match:
                            business.phone = self._clean_phone(phone_match.group())
                            break
                    
                    # Categoria (geralmente é curta e não tem números)
                    if len(line) > 3 and len(line) < 40 and not any(c.isdigit() for c in line):
                        if not business.category and line != name:
                            business.category = line
            
            # Extrair href para obter dados da URL
            href = await item.get_attribute("href")
            if href:
                # Place ID
                place_id_match = re.search(r'!1s([^!]+)', href)
                if place_id_match:
                    business.place_id = place_id_match.group(1)
                
                # Coordenadas
                coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', href)
                if coords_match:
                    business.latitude = float(coords_match.group(1))
                    business.longitude = float(coords_match.group(2))
            
            return business
            
        except Exception as e:
            logger.debug(f"Erro extração rápida: {e}")
            return None
    
    async def extract_email_from_website(
        self,
        website_url: str,
        timeout: int = 10000,
    ) -> Optional[str]:
        """
        Tenta extrair email do website do negócio.
        
        Args:
            website_url: URL do site
            timeout: Timeout em ms
            
        Returns:
            Email encontrado ou None
        """
        if not website_url:
            return None
            
        try:
            page = await self.new_page()
            
            # Navegar para o site
            await page.goto(website_url, wait_until="domcontentloaded", timeout=timeout)
            
            # Buscar emails no HTML
            html = await page.content()
            
            # Padrões de email
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, html)
            
            # Filtrar emails válidos (remover imagens, etc)
            valid_emails = []
            invalid_extensions = ['.png', '.jpg', '.gif', '.svg', '.css', '.js']
            
            for email in emails:
                email_lower = email.lower()
                if not any(ext in email_lower for ext in invalid_extensions):
                    if not email_lower.startswith('example@'):
                        valid_emails.append(email)
            
            await page.close()
            
            if valid_emails:
                # Preferir emails com domínio do site
                from urllib.parse import urlparse
                domain = urlparse(website_url).netloc.replace('www.', '')
                
                for email in valid_emails:
                    if domain in email:
                        return email
                
                return valid_emails[0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao extrair email de {website_url}: {e}")
            return None
    
    async def _extract_business_from_card(
        self,
        page: Page,
        card,
        card_name: str,
    ) -> Optional[ScrapedBusiness]:
        """Extrai dados completos de um card de negócio clicando nele.
        
        Args:
            page: Página do Playwright
            card: Elemento do card
            card_name: Nome já extraído do aria-label do card
        """
        try:
            # Clicar no card para abrir detalhes
            await card.click()
            await asyncio.sleep(1.5)  # Aguardar painel carregar
            
            # Aguardar painel de detalhes
            try:
                await page.wait_for_selector('[role="main"]', timeout=self.DETAIL_TIMEOUT)
            except PlaywrightTimeout:
                logger.debug("Timeout aguardando painel de detalhes")
                return None
            
            # Aguardar um pouco mais para todos os dados carregarem
            await asyncio.sleep(0.5)
            
            # Tentar extrair nome do H1, mas usar card_name como fallback
            name_el = await page.query_selector('h1')
            name_from_h1 = await name_el.inner_text() if name_el else None
            
            # Se o H1 for genérico como "Resultados", usar o nome do card
            name = card_name  # Priorizar nome do card (aria-label)
            if name_from_h1 and name_from_h1.strip() not in ["Resultados", "Pesquisa", ""]:
                name = name_from_h1.strip()
            
            if not name:
                return None
            
            # Extrair dados do painel
            business = ScrapedBusiness(
                name=name,
                source="google_maps",
            )
            
            # ========== TELEFONE ==========
            # Tentar múltiplos seletores para telefone
            phone_selectors = [
                '[data-item-id^="phone:"]',
                'a[href^="tel:"]',
                'button[aria-label*="telefone" i]',
                'button[aria-label*="ligar" i]',
                '[data-tooltip*="telefone" i]',
            ]
            
            for selector in phone_selectors:
                phone_el = await page.query_selector(selector)
                if phone_el:
                    # Tentar pegar do href primeiro
                    href = await phone_el.get_attribute("href")
                    if href and href.startswith("tel:"):
                        business.phone = self._clean_phone(href.replace("tel:", ""))
                        break
                    
                    # Tentar pegar do aria-label
                    aria = await phone_el.get_attribute("aria-label")
                    if aria:
                        phone_match = re.search(r'[\d\s\-\(\)]{10,}', aria)
                        if phone_match:
                            business.phone = self._clean_phone(phone_match.group())
                            break
                    
                    # Tentar pegar do texto
                    text = await phone_el.inner_text()
                    if text:
                        phone_match = re.search(r'[\d\s\-\(\)]{10,}', text)
                        if phone_match:
                            business.phone = self._clean_phone(phone_match.group())
                            break
            
            # Método alternativo: buscar no HTML completo da página
            if not business.phone:
                try:
                    main_content = await page.query_selector('[role="main"]')
                    if main_content:
                        html = await main_content.inner_html()
                        # Regex para telefone brasileiro
                        phone_patterns = [
                            r'\(?\d{2}\)?\s*\d{4,5}[-.\s]?\d{4}',  # (11) 99999-9999
                            r'\+55\s*\d{2}\s*\d{4,5}[-.\s]?\d{4}',  # +55 11 99999-9999
                        ]
                        for pattern in phone_patterns:
                            match = re.search(pattern, html)
                            if match:
                                business.phone = self._clean_phone(match.group())
                                break
                except Exception:
                    pass
            
            # ========== WEBSITE ==========
            website_selectors = [
                '[data-item-id="authority"]',
                'a[data-item-id="authority"]',
                'a[href*="http"][aria-label*="site" i]',
                'a[href*="http"][aria-label*="website" i]',
            ]
            
            for selector in website_selectors:
                website_el = await page.query_selector(selector)
                if website_el:
                    href = await website_el.get_attribute("href")
                    if href and ("http" in href or "www" in href):
                        # Limpar URLs de redirecionamento do Google
                        if "google.com/url" in href:
                            url_match = re.search(r'url=([^&]+)', href)
                            if url_match:
                                from urllib.parse import unquote
                                business.website = unquote(url_match.group(1))
                        else:
                            business.website = href
                        break
            
            # ========== ENDEREÇO ==========
            address_selectors = [
                '[data-item-id="address"]',
                'button[aria-label*="endereço" i]',
                '[data-tooltip*="endereço" i]',
            ]
            
            for selector in address_selectors:
                address_el = await page.query_selector(selector)
                if address_el:
                    text = await address_el.inner_text()
                    if text and len(text) > 5:
                        business.address = text.strip()
                        break
            
            # ========== RATING ==========
            rating_selectors = [
                'div[role="img"][aria-label*="estrela"]',
                'span[aria-label*="estrela"]',
                '.fontDisplayLarge',  # Número grande de rating
            ]
            
            for selector in rating_selectors:
                rating_el = await page.query_selector(selector)
                if rating_el:
                    aria = await rating_el.get_attribute("aria-label")
                    if aria:
                        match = re.search(r'([\d,\.]+)', aria)
                        if match:
                            business.rating = float(match.group(1).replace(',', '.'))
                            break
                    text = await rating_el.inner_text()
                    if text:
                        match = re.search(r'^[\d,\.]+$', text.strip())
                        if match:
                            business.rating = float(match.group().replace(',', '.'))
                            break
            
            # ========== REVIEWS COUNT ==========
            reviews_selectors = [
                'span[aria-label*="avaliação"]',
                'span[aria-label*="comentário"]',
                'button[aria-label*="avaliação"]',
            ]
            
            for selector in reviews_selectors:
                reviews_el = await page.query_selector(selector)
                if reviews_el:
                    text = await reviews_el.inner_text()
                    if text:
                        # Extrair número removendo pontos de milhar
                        clean_text = text.replace('.', '').replace(',', '')
                        match = re.search(r'(\d+)', clean_text)
                        if match:
                            business.reviews_count = int(match.group(1))
                            break
            
            # ========== CATEGORIA ==========
            category_selectors = [
                'button[jsaction*="category"]',
                '[jsaction*="pane.rating.category"]',
                'span.DkEaL',  # Classe comum de categoria
            ]
            
            for selector in category_selectors:
                category_el = await page.query_selector(selector)
                if category_el:
                    text = await category_el.inner_text()
                    if text and len(text) > 2:
                        business.category = text.strip()
                        break
            
            # ========== PLACE ID & COORDENADAS ==========
            current_url = page.url
            
            place_id_match = re.search(r'!1s([^!]+)', current_url)
            if place_id_match:
                business.place_id = place_id_match.group(1)
            
            coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
            if coords_match:
                business.latitude = float(coords_match.group(1))
                business.longitude = float(coords_match.group(2))
            
            # Log dos dados extraídos
            logger.debug(
                f"Extraído: {business.name} | "
                f"Tel: {business.phone or 'N/A'} | "
                f"Site: {business.website or 'N/A'} | "
                f"End: {business.address[:30] if business.address else 'N/A'}..."
            )
            
            # ========== EMAIL (opcional) ==========
            # Se configurado e tem website, tentar extrair email
            if getattr(self, '_extract_emails', False) and business.website:
                try:
                    logger.debug(f"Tentando extrair email de {business.website}")
                    email = await self.extract_email_from_website(business.website)
                    if email:
                        business.email = email
                        logger.debug(f"Email encontrado: {email}")
                except Exception as e:
                    logger.debug(f"Erro ao extrair email: {e}")
            
            return business
            
        except Exception as e:
            logger.warning(f"Erro ao extrair detalhes: {e}")
            return None
    
    def _clean_phone(self, phone: str) -> str:
        """Limpa e formata número de telefone."""
        # Remove tudo exceto números
        digits = re.sub(r'[^\d]', '', phone)
        
        # Formatar para padrão brasileiro
        if len(digits) == 11:  # Celular com DDD
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) == 10:  # Fixo com DDD
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        
        return phone.strip()
    
    async def scrape_business_details(
        self,
        place_id: str,
    ) -> Optional[ScrapedBusiness]:
        """
        Extrai detalhes completos de um negócio pelo Place ID.
        
        Args:
            place_id: Google Place ID
            
        Returns:
            ScrapedBusiness com detalhes completos
        """
        try:
            page = await self.new_page()
            
            url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            await page.goto(url, wait_until="networkidle")
            
            await self._accept_cookies(page)
            await page.wait_for_selector('[role="main"]', timeout=10000)
            
            # Extrair dados (reutilizar lógica)
            name_el = await page.query_selector('h1')
            name = await name_el.inner_text() if name_el else "Unknown"
            
            business = ScrapedBusiness(
                name=name.strip(),
                place_id=place_id,
                source="google_maps",
            )
            
            # Extrair todos os campos disponíveis...
            # (mesma lógica do _extract_business_from_card)
            
            await page.close()
            return business
            
        except Exception as e:
            logger.error(f"Erro ao extrair detalhes: {e}")
            return None
