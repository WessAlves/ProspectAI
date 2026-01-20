"""
Scraper para Instagram.

Extrai informações de perfis de negócios do Instagram.
Utiliza a interface web pública sem necessidade de login.
"""

import re
import json
import time
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from app.services.scraping.base import BaseScraper
from app.services.scraping.models import ScrapedBusiness, ScrapedContact, ScrapeResult

logger = logging.getLogger(__name__)


class InstagramScraper(BaseScraper):
    """
    Scraper para extrair dados do Instagram.
    
    Extrai informações de perfis de negócios como:
    - Nome do negócio
    - Bio/descrição
    - Website
    - Contatos (email, telefone)
    - Seguidores e engajamento
    
    Exemplo de uso:
        async with InstagramScraper() as scraper:
            # Buscar perfil específico
            profile = await scraper.get_profile("restaurante_exemplo")
            
            # Buscar perfis por hashtag
            result = await scraper.search_by_hashtag("restaurantessp", limit=20)
    
    NOTA: O Instagram tem proteções contra scraping. Use com moderação
    e considere usar a API oficial para uso comercial.
    """
    
    BASE_URL = "https://www.instagram.com"
    
    async def scrape(
        self,
        query: str,
        location: str,
        limit: int = 50,
    ) -> ScrapeResult:
        """
        Busca perfis no Instagram baseado em uma query.
        
        Args:
            query: Termo de busca ou hashtag
            location: Localização (usada para filtrar resultados)
            limit: Número máximo de resultados
            
        Returns:
            ScrapeResult com os perfis encontrados
        """
        start_time = time.time()
        businesses: List[ScrapedBusiness] = []
        
        try:
            # Tentar buscar por hashtag primeiro
            hashtag = self._format_hashtag(query)
            
            logger.info(f"InstagramScraper: Buscando por #{hashtag}")
            
            hashtag_results = await self.search_by_hashtag(hashtag, limit)
            businesses.extend(hashtag_results)
            
            # Se não encontrou resultados suficientes, tentar busca direta
            if len(businesses) < limit:
                search_results = await self.search_profiles(query, limit - len(businesses))
                businesses.extend(search_results)
            
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
            logger.error(f"InstagramScraper: Erro - {str(e)}")
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
    
    def _format_hashtag(self, query: str) -> str:
        """Formata query para hashtag (remove espaços e caracteres especiais)."""
        # Remove # se já tiver
        query = query.lstrip('#')
        # Remove espaços e caracteres especiais
        hashtag = re.sub(r'[^a-zA-Z0-9áéíóúãõâêîôûç]', '', query.lower())
        return hashtag
    
    async def search_by_hashtag(
        self,
        hashtag: str,
        limit: int = 50,
    ) -> List[ScrapedBusiness]:
        """
        Busca posts por hashtag e extrai perfis dos autores.
        
        Args:
            hashtag: Hashtag para buscar (sem #)
            limit: Limite de perfis únicos
            
        Returns:
            Lista de ScrapedBusiness dos perfis encontrados
        """
        businesses: List[ScrapedBusiness] = []
        seen_usernames = set()
        
        try:
            page = await self.new_page()
            
            url = f"{self.BASE_URL}/explore/tags/{hashtag}/"
            logger.info(f"InstagramScraper: Acessando {url}")
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await self.random_delay(2, 4)
            
            # Verificar se página de login apareceu
            if await self._check_login_wall(page):
                logger.warning("Instagram solicitou login - tentando contornar")
                await self._dismiss_login_modal(page)
            
            # Scroll para carregar mais posts
            posts_data = await self._extract_posts_from_hashtag(page, limit * 2)
            
            for post in posts_data:
                if len(businesses) >= limit:
                    break
                    
                username = post.get('username')
                if username and username not in seen_usernames:
                    seen_usernames.add(username)
                    
                    # Extrair dados do perfil
                    profile = await self.get_profile(username)
                    if profile:
                        businesses.append(profile)
                        await self.random_delay(3, 6)  # Delay maior entre perfis
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Erro ao buscar hashtag #{hashtag}: {e}")
        
        return businesses
    
    async def search_profiles(
        self,
        query: str,
        limit: int = 20,
    ) -> List[ScrapedBusiness]:
        """
        Busca perfis diretamente pela busca do Instagram.
        
        Args:
            query: Termo de busca
            limit: Limite de resultados
            
        Returns:
            Lista de ScrapedBusiness
        """
        businesses: List[ScrapedBusiness] = []
        
        try:
            page = await self.new_page()
            
            # Ir para página inicial primeiro
            await page.goto(self.BASE_URL, wait_until="networkidle", timeout=30000)
            await self.random_delay(2, 3)
            
            # Tentar usar a busca
            search_url = f"{self.BASE_URL}/web/search/topsearch/?query={quote_plus(query)}"
            
            # Fazer request direta para API de busca
            response = await page.request.get(search_url)
            
            if response.ok:
                data = await response.json()
                users = data.get('users', [])
                
                for user_data in users[:limit]:
                    user = user_data.get('user', {})
                    username = user.get('username')
                    
                    if username:
                        # Verificar se é conta de negócio
                        if user.get('is_business') or user.get('is_professional_account'):
                            profile = await self.get_profile(username)
                            if profile:
                                businesses.append(profile)
                                await self.random_delay(2, 4)
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Erro na busca de perfis: {e}")
        
        return businesses
    
    async def get_profile(
        self,
        username: str,
    ) -> Optional[ScrapedBusiness]:
        """
        Extrai dados de um perfil específico do Instagram.
        
        Args:
            username: Nome de usuário do Instagram
            
        Returns:
            ScrapedBusiness com os dados do perfil ou None
        """
        try:
            page = await self.new_page()
            
            url = f"{self.BASE_URL}/{username}/"
            logger.info(f"InstagramScraper: Extraindo perfil @{username}")
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await self.random_delay(1, 2)
            
            # Verificar se perfil existe
            if await page.query_selector('text="Sorry, this page isn\'t available"'):
                logger.warning(f"Perfil @{username} não encontrado")
                await page.close()
                return None
            
            # Tentar extrair dados do JSON embutido na página
            profile_data = await self._extract_profile_json(page)
            
            if not profile_data:
                # Fallback: extrair do HTML
                profile_data = await self._extract_profile_html(page)
            
            await page.close()
            
            if profile_data:
                return self._create_business_from_profile(username, profile_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair perfil @{username}: {e}")
            return None
    
    async def _extract_profile_json(self, page: Page) -> Optional[Dict[str, Any]]:
        """Extrai dados do perfil do JSON embutido na página."""
        try:
            # Instagram armazena dados em scripts JSON
            scripts = await page.query_selector_all('script[type="application/ld+json"]')
            
            for script in scripts:
                content = await script.inner_text()
                try:
                    data = json.loads(content)
                    if data.get('@type') == 'ProfilePage':
                        return data
                except json.JSONDecodeError:
                    continue
            
            # Tentar extrair de window._sharedData
            shared_data = await page.evaluate('''
                () => {
                    if (window._sharedData && window._sharedData.entry_data) {
                        const profilePage = window._sharedData.entry_data.ProfilePage;
                        if (profilePage && profilePage[0]) {
                            return profilePage[0].graphql?.user;
                        }
                    }
                    return null;
                }
            ''')
            
            return shared_data
            
        except Exception as e:
            logger.debug(f"Erro ao extrair JSON: {e}")
            return None
    
    async def _extract_profile_html(self, page: Page) -> Dict[str, Any]:
        """Extrai dados do perfil diretamente do HTML."""
        data = {}
        
        try:
            # Nome completo
            name_el = await page.query_selector('header section span')
            if name_el:
                data['full_name'] = await name_el.inner_text()
            
            # Bio
            bio_el = await page.query_selector('header section > div > span')
            if bio_el:
                data['biography'] = await bio_el.inner_text()
            
            # Website (no link da bio)
            website_el = await page.query_selector('header a[href*="l.instagram.com"]')
            if website_el:
                href = await website_el.get_attribute('href')
                # Decodificar URL redirecionada do Instagram
                if 'u=' in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'u' in parsed:
                        data['external_url'] = parsed['u'][0]
            
            # Contagem de seguidores, seguindo e posts
            stats = await page.query_selector_all('header section ul li')
            for stat in stats:
                text = await stat.inner_text()
                if 'posts' in text.lower() or 'publicações' in text.lower():
                    data['media_count'] = self._parse_count(text)
                elif 'followers' in text.lower() or 'seguidores' in text.lower():
                    data['follower_count'] = self._parse_count(text)
                elif 'following' in text.lower() or 'seguindo' in text.lower():
                    data['following_count'] = self._parse_count(text)
            
            # Categoria do negócio
            category_el = await page.query_selector('header div[class*="category"]')
            if category_el:
                data['category'] = await category_el.inner_text()
            
            # Verificar se é conta verificada
            verified_el = await page.query_selector('header svg[aria-label*="Verified"]')
            data['is_verified'] = verified_el is not None
            
        except Exception as e:
            logger.debug(f"Erro ao extrair HTML: {e}")
        
        return data
    
    def _parse_count(self, text: str) -> int:
        """Converte texto como '1.5K' ou '2M' para número."""
        try:
            # Extrair número do texto
            match = re.search(r'[\d,.]+[KkMm]?', text.replace(' ', ''))
            if not match:
                return 0
            
            num_str = match.group().replace(',', '.')
            
            if 'k' in num_str.lower():
                return int(float(num_str.lower().replace('k', '')) * 1000)
            elif 'm' in num_str.lower():
                return int(float(num_str.lower().replace('m', '')) * 1000000)
            else:
                return int(float(num_str))
        except:
            return 0
    
    def _create_business_from_profile(
        self,
        username: str,
        data: Dict[str, Any],
    ) -> ScrapedBusiness:
        """Cria ScrapedBusiness a partir dos dados do perfil."""
        # Extrair emails e telefones da bio
        biography = data.get('biography', '') or data.get('description', '') or ''
        
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', biography)
        phones = re.findall(r'[\(\+]?\d{1,3}[\)\s.-]?\d{2,5}[\s.-]?\d{4,5}[\s.-]?\d{4}', biography)
        
        # Website
        website = data.get('external_url') or data.get('url')
        
        # Determinar se é negócio baseado em métricas
        follower_count = data.get('follower_count') or data.get('edge_followed_by', {}).get('count', 0)
        
        return ScrapedBusiness(
            name=data.get('full_name') or data.get('name') or username,
            website=website,
            email=emails[0] if emails else None,
            phone=phones[0] if phones else None,
            category=data.get('category') or data.get('business_category_name'),
            source="instagram",
            extra_data={
                "username": username,
                "instagram_url": f"https://instagram.com/{username}",
                "biography": biography[:500] if biography else None,
                "follower_count": follower_count,
                "following_count": data.get('following_count') or data.get('edge_follow', {}).get('count', 0),
                "media_count": data.get('media_count') or data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                "is_verified": data.get('is_verified', False),
                "is_business": data.get('is_business_account', False),
                "is_professional": data.get('is_professional_account', False),
                "business_email": data.get('business_email'),
                "business_phone": data.get('business_phone_number'),
                "business_address": data.get('business_address_json'),
            },
        )
    
    async def _extract_posts_from_hashtag(
        self,
        page: Page,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Extrai dados de posts de uma página de hashtag."""
        posts = []
        
        try:
            # Scroll para carregar mais posts
            scroll_count = min(limit // 12, 10)  # ~12 posts por scroll, máximo 10 scrolls
            
            for _ in range(scroll_count):
                await page.evaluate('window.scrollBy(0, 1000)')
                await self.random_delay(1, 2)
            
            # Extrair links dos posts
            post_links = await page.query_selector_all('article a[href*="/p/"]')
            
            seen_hrefs = set()
            for link in post_links[:limit]:
                href = await link.get_attribute('href')
                if href and href not in seen_hrefs:
                    seen_hrefs.add(href)
                    
                    # Extrair username do post (se possível)
                    # Instagram mostra o autor em alguns elementos
                    username = await self._get_post_author(page, href)
                    if username:
                        posts.append({'href': href, 'username': username})
            
        except Exception as e:
            logger.debug(f"Erro ao extrair posts: {e}")
        
        return posts
    
    async def _get_post_author(self, page: Page, post_href: str) -> Optional[str]:
        """Tenta obter o autor de um post."""
        try:
            # Navegar para o post
            post_page = await self.new_page()
            await post_page.goto(f"{self.BASE_URL}{post_href}", wait_until="networkidle", timeout=15000)
            
            # Extrair username do autor
            author_el = await post_page.query_selector('header a[href*="/"]')
            if author_el:
                href = await author_el.get_attribute('href')
                if href:
                    username = href.strip('/').split('/')[-1]
                    await post_page.close()
                    return username
            
            await post_page.close()
            
        except Exception as e:
            logger.debug(f"Erro ao obter autor do post: {e}")
        
        return None
    
    async def _check_login_wall(self, page: Page) -> bool:
        """Verifica se o Instagram está solicitando login."""
        login_indicators = [
            'text="Log in"',
            'text="Log In"',
            'text="Entrar"',
            '[aria-label="Log in"]',
        ]
        
        for indicator in login_indicators:
            if await page.query_selector(indicator):
                return True
        
        return False
    
    async def _dismiss_login_modal(self, page: Page):
        """Tenta fechar modal de login se aparecer."""
        try:
            close_buttons = [
                'button[aria-label="Close"]',
                'button[aria-label="Fechar"]',
                'svg[aria-label="Close"]',
            ]
            
            for selector in close_buttons:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.random_delay(1, 2)
                    return
            
            # Tentar clicar fora do modal
            await page.click('body', position={'x': 10, 'y': 10})
            
        except Exception:
            pass
    
    async def extract_contact_info(
        self,
        username: str,
    ) -> Optional[ScrapedContact]:
        """
        Extrai informações de contato detalhadas de um perfil.
        
        Args:
            username: Nome de usuário do Instagram
            
        Returns:
            ScrapedContact com emails, telefones e redes sociais
        """
        profile = await self.get_profile(username)
        
        if not profile:
            return None
        
        contact = ScrapedContact(
            source_url=f"https://instagram.com/{username}",
        )
        
        # Emails
        if profile.email:
            contact.emails.append(profile.email)
        if profile.extra_data.get('business_email'):
            contact.emails.append(profile.extra_data['business_email'])
        
        # Telefones
        if profile.phone:
            contact.phones.append(profile.phone)
        if profile.extra_data.get('business_phone'):
            contact.phones.append(profile.extra_data['business_phone'])
        
        # Redes sociais
        contact.social_media['instagram'] = username
        
        # Se tiver website, tentar extrair mais contatos
        if profile.website:
            try:
                from app.services.scraping.google_scraper import GoogleScraper
                async with GoogleScraper() as google_scraper:
                    website_contact = await google_scraper.extract_contact_from_website(profile.website)
                    if website_contact:
                        contact.emails.extend([e for e in website_contact.emails if e not in contact.emails])
                        contact.phones.extend([p for p in website_contact.phones if p not in contact.phones])
                        contact.social_media.update(website_contact.social_media)
            except Exception as e:
                logger.debug(f"Erro ao extrair contatos do website: {e}")
        
        return contact
