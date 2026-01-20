"""
Tarefas de scraping para coleta de prospects.
"""

import asyncio
from celery import shared_task
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import logging

from app.services.scraping import GoogleScraper, GoogleMapsScraper, InstagramScraper, ScrapeResult
from app.services.scraping.models import ScrapedBusiness
from app.services.notifications import (
    publish_scraping_progress,
    publish_lead_found,
    publish_scraping_completed,
    publish_scraping_error,
    publish_limit_reached,
)

logger = logging.getLogger(__name__)

# Constantes para controle de limites
LIMIT_REACHED_MARKER = "__LIMIT_REACHED__"


def run_async(coro):
    """Helper para executar coroutines em tasks síncronas do Celery."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _create_db_session():
    """Cria uma sessão de banco síncrona para uso nas tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    # Converter URL async para sync
    db_url = str(settings.DATABASE_URL)
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def _get_user_id_from_campaign(db_session, campaign_id: str) -> Optional[int]:
    """Obtém o user_id de uma campanha."""
    from app.db.models.campaign import Campaign
    
    campaign = db_session.query(Campaign).filter(
        Campaign.id == UUID(campaign_id)
    ).first()
    
    return campaign.user_id if campaign else None


def _check_lead_limit(db_session, user_id: int) -> Tuple[bool, int]:
    """
    Verifica se o usuário ainda pode adicionar leads.
    
    Returns:
        Tuple[bool, int]: (pode_adicionar, leads_restantes)
    """
    from app.services.lead_limits import sync_check_can_add_lead
    return sync_check_can_add_lead(db_session, user_id)


def _save_prospect_to_db(
    db_session,
    business: ScrapedBusiness,
    campaign_id: str,
    check_limits: bool = True,
) -> Tuple[bool, bool]:
    """
    Salva um prospect no banco de dados com verificação de limites.
    
    Args:
        db_session: Sessão do banco
        business: Dados do negócio
        campaign_id: ID da campanha
        check_limits: Se True, verifica limites antes de salvar
        
    Returns:
        Tuple[bool, bool]: (salvou_com_sucesso, limite_atingido)
    """
    from app.db.models.prospect import Prospect, ProspectStatus, ProspectPlatform
    from app.services.lead_limits import sync_pause_user_campaigns
    
    try:
        # Verificar limites se necessário
        if check_limits:
            user_id = _get_user_id_from_campaign(db_session, campaign_id)
            if user_id:
                can_add, remaining = _check_lead_limit(db_session, user_id)
                if not can_add:
                    logger.warning(
                        f"⚠️ Limite de leads atingido para usuário {user_id}. "
                        f"Pausando campanhas."
                    )
                    sync_pause_user_campaigns(db_session, user_id, "Limite de leads atingido")
                    return False, True  # Não salvou, limite atingido
                
                # Avisar quando estiver próximo do limite
                if remaining != -1 and remaining <= 10:
                    logger.info(f"⚠️ Usuário {user_id} tem apenas {remaining} leads restantes")
        
        # Gerar username a partir do nome
        username = business.name.lower().replace(' ', '_')[:50] if business.name else "unknown"
        
        # Verificar se já existe (por nome e campanha)
        existing = db_session.query(Prospect).filter(
            Prospect.campaign_id == UUID(campaign_id),
            Prospect.name == business.name
        ).first()
        
        if existing:
            logger.debug(f"Prospect já existe: {business.name}")
            return False, False  # Não salvou (duplicado), mas não é limite
        
        prospect = Prospect(
            campaign_id=UUID(campaign_id),
            name=business.name or "Sem nome",
            username=username,
            platform=ProspectPlatform.GOOGLE_MAPS,
            website_url=business.website,
            has_website=bool(business.website),
            email=business.email,
            phone=business.phone,
            company=business.name,  # Usar nome como empresa
            position=business.category,  # Usar categoria como posição
            status=ProspectStatus.FOUND,
            score=0,
            extra_data={
                "address": business.address,
                "rating": business.rating,
                "reviews_count": business.reviews_count,
                "place_id": business.place_id,
                "latitude": business.latitude,
                "longitude": business.longitude,
                "source": business.source,
            }
        )
        
        db_session.add(prospect)
        db_session.commit()
        return True, False  # Salvou com sucesso, limite não atingido
        
    except Exception as e:
        logger.error(f"Erro ao salvar prospect {business.name}: {e}")
        db_session.rollback()
        return False, False


@shared_task(bind=True, max_retries=2, default_retry_delay=30, time_limit=600, soft_time_limit=540)
def scrape_google_maps(
    self, 
    query: str, 
    location: str, 
    limit: int = 100,
    campaign_id: str = None,
    save_progressive: bool = True,
    detailed_mode: bool = True,  # True por padrão para extrair telefone/website
    extract_emails: bool = False,  # Extrair emails dos websites
) -> Dict[str, Any]:
    """
    Scrape otimizado do Google Maps para encontrar empresas.
    
    Características:
    - Salvamento progressivo: prospects são salvos conforme encontrados
    - Timeout de 10 minutos para evitar travamentos
    - Modo detalhado por padrão (clica nos cards para telefone/website)
    - Verificação de limites de leads do usuário
    
    Args:
        query: Termo de busca (ex: "restaurantes")
        location: Localização (ex: "São Paulo, SP")
        limit: Número máximo de resultados
        campaign_id: ID da campanha (obrigatório para salvar)
        save_progressive: Se True, salva conforme encontra (recomendado)
        detailed_mode: Se True, clica em cada card para telefone/website (recomendado)
        extract_emails: Se True, visita websites para extrair emails (mais lento)
    
    Returns:
        Dict com resultados do scraping
    """
    saved_count = 0
    found_count = 0
    db_session = None
    limit_reached = False
    user_id = None
    
    try:
        logger.info(f"🔍 Iniciando scraping Google Maps: '{query}' em '{location}'")
        logger.info(f"   Limite: {limit}, Campaign: {campaign_id}, Progressivo: {save_progressive}")
        
        # Preparar sessão do banco se for salvar progressivamente
        if campaign_id and save_progressive:
            db_session = _create_db_session()
            # Obter user_id da campanha para notificações
            user_id = _get_user_id_from_campaign(db_session, campaign_id)
        
        # Callback para salvamento progressivo com verificação de limites
        async def on_business_found(business: ScrapedBusiness) -> bool:
            nonlocal saved_count, found_count, limit_reached
            
            found_count += 1
            
            if limit_reached:
                # Se limite já foi atingido, não tenta salvar mais
                return False
                
            if db_session and campaign_id:
                saved, reached = _save_prospect_to_db(db_session, business, campaign_id, check_limits=True)
                
                if reached:
                    limit_reached = True
                    logger.warning(f"🛑 Limite de leads atingido! Parando scraping.")
                    # Notificar via WebSocket
                    if user_id:
                        publish_limit_reached(str(user_id), campaign_id)
                    return False
                
                if saved:
                    saved_count += 1
                    
                    # Notificar progresso via WebSocket
                    if user_id:
                        publish_scraping_progress(
                            campaign_id=campaign_id,
                            user_id=str(user_id),
                            found=found_count,
                            saved=saved_count,
                            current_name=business.name,
                        )
                        
                        # Notificar lead encontrado
                        publish_lead_found(
                            campaign_id=campaign_id,
                            user_id=str(user_id),
                            lead_data=business.to_dict(),
                        )
                    
                    return True
            return False
        
        async def _scrape():
            async with GoogleMapsScraper() as scraper:
                return await scraper.scrape(
                    query, 
                    location, 
                    limit,
                    on_business_found=on_business_found if (campaign_id and save_progressive) else None,
                    detailed_mode=detailed_mode,
                    extract_emails=extract_emails,
                )
        
        result: ScrapeResult = run_async(_scrape())
        
        # Se não salvou progressivamente, salvar tudo ao final
        if campaign_id and not save_progressive and db_session is None:
            db_session = _create_db_session()
            for business in result.businesses:
                if limit_reached:
                    break
                saved, reached = _save_prospect_to_db(db_session, business, campaign_id, check_limits=True)
                if saved:
                    saved_count += 1
                if reached:
                    limit_reached = True
                    break
        
        # Converter para dict serializável
        output = {
            "status": "success" if result.success and not limit_reached else ("limit_reached" if limit_reached else "error"),
            "query": query,
            "location": location,
            "total_found": result.total_found,
            "saved_count": saved_count,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
            "prospects": [b.to_dict() for b in result.businesses],
            "limit_reached": limit_reached,
        }
        
        if campaign_id:
            output["campaign_id"] = campaign_id
        
        # Notificar conclusão via WebSocket
        if user_id and campaign_id:
            publish_scraping_completed(
                campaign_id=campaign_id,
                user_id=str(user_id),
                total_found=result.total_found,
                total_saved=saved_count,
                duration_seconds=result.duration_seconds,
            )
        
        if limit_reached:
            output["message"] = "Limite de leads atingido. Atualize seu plano ou compre pacotes adicionais."
            logger.warning(
                f"⚠️ Scraping Google Maps interrompido por limite: "
                f"{result.total_found} encontrados, {saved_count} salvos em {result.duration_seconds:.1f}s"
            )
        else:
            logger.info(
                f"✅ Scraping Google Maps concluído: "
                f"{result.total_found} encontrados, {saved_count} salvos em {result.duration_seconds:.1f}s"
            )
        return output
        
    except Exception as e:
        logger.error(f"❌ Erro no scraping Google Maps: {str(e)}")
        
        # Notificar erro via WebSocket
        if user_id and campaign_id:
            publish_scraping_error(
                campaign_id=campaign_id,
                user_id=str(user_id),
                error_message=str(e),
            )
        
        # Retornar resultado parcial em vez de retry
        return {
            "status": "error",
            "query": query,
            "location": location,
            "total_found": 0,
            "saved_count": saved_count,
            "error": str(e),
            "prospects": [],
            "campaign_id": campaign_id,
            "limit_reached": limit_reached,
        }
    finally:
        if db_session:
            db_session.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_google_search(
    self,
    query: str,
    location: str,
    limit: int = 50,
    extract_contacts: bool = False,
    campaign_id: str = None,
) -> Dict[str, Any]:
    """
    Scrape do Google Search para encontrar empresas/sites.
    
    Args:
        query: Termo de busca
        location: Localização para contexto
        limit: Número máximo de resultados
        extract_contacts: Se True, extrai contatos dos sites encontrados
        campaign_id: ID da campanha (opcional)
    
    Returns:
        Dict com resultados do scraping
    """
    try:
        logger.info(f"Iniciando scraping Google Search: {query} em {location}")
        
        async def _scrape():
            async with GoogleScraper() as scraper:
                if extract_contacts:
                    return await scraper.search_with_contact_extraction(query, location, limit)
                else:
                    return await scraper.scrape(query, location, limit)
        
        result = run_async(_scrape())
        
        # Se extract_contacts=True, result já é uma lista de dicts
        if extract_contacts:
            output = {
                "status": "success",
                "query": query,
                "location": location,
                "total_found": len(result),
                "prospects": result,
            }
        else:
            # result é ScrapeResult
            output = {
                "status": "success" if result.success else "error",
                "query": query,
                "location": location,
                "total_found": result.total_found,
                "duration_seconds": result.duration_seconds,
                "error": result.error,
                "prospects": [b.to_dict() for b in result.businesses],
            }
        
        if campaign_id:
            output["campaign_id"] = campaign_id
        
        logger.info(f"Scraping Google Search concluído: {output['total_found']} resultados")
        return output
        
    except Exception as e:
        logger.error(f"Erro no scraping Google Search: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_linkedin(self, company_name: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Scrape do LinkedIn para encontrar informações de contato.
    
    Args:
        company_name: Nome da empresa
        filters: Filtros adicionais (cargo, localização, etc.)
    
    Returns:
        Dict com resultados do scraping
    """
    try:
        logger.info(f"Iniciando scraping LinkedIn: {company_name}")
        
        # TODO: Implementar scraping real (requer autenticação)
        # LinkedIn tem proteções robustas, considerar usar API oficial ou serviços de terceiros
        
        results = {
            "status": "not_implemented",
            "message": "LinkedIn scraping requer implementação de autenticação e pode violar ToS",
            "company": company_name,
            "contacts": []
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Erro no scraping LinkedIn: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enrich_prospect_data(self, prospect_id: str) -> Dict[str, Any]:
    """
    Enriquece dados de um prospect com informações adicionais.
    
    Busca no site do prospect por emails, telefones e redes sociais.
    
    Args:
        prospect_id: ID do prospect
    
    Returns:
        Dict com dados enriquecidos
    """
    try:
        logger.info(f"Enriquecendo dados do prospect: {prospect_id}")
        
        # TODO: Buscar prospect no banco
        # TODO: Se tiver website, extrair contatos
        
        async def _enrich(website: str):
            async with GoogleScraper() as scraper:
                return await scraper.extract_contact_from_website(website)
        
        # Por enquanto retorna placeholder
        return {
            "status": "pending_implementation",
            "prospect_id": prospect_id,
            "enriched_fields": []
        }
        
    except Exception as e:
        logger.error(f"Erro ao enriquecer prospect: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def extract_website_contacts(self, website_url: str) -> Dict[str, Any]:
    """
    Extrai informações de contato de um website específico.
    
    Args:
        website_url: URL do website
    
    Returns:
        Dict com emails, telefones e redes sociais
    """
    try:
        logger.info(f"Extraindo contatos de: {website_url}")
        
        async def _extract():
            async with GoogleScraper() as scraper:
                return await scraper.extract_contact_from_website(website_url)
        
        contact = run_async(_extract())
        
        if contact:
            return {
                "status": "success",
                "url": website_url,
                "contact": contact.to_dict(),
            }
        else:
            return {
                "status": "error",
                "url": website_url,
                "error": "Não foi possível extrair contatos",
            }
        
    except Exception as e:
        logger.error(f"Erro ao extrair contatos de {website_url}: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def batch_scrape_prospects(
    self,
    sources: List[str],
    query: str,
    location: str,
    limit_per_source: int = 50,
    campaign_id: str = None,
) -> Dict[str, Any]:
    """
    Executa scraping em múltiplas fontes em batch.
    
    Args:
        sources: Lista de fontes ("google", "google_maps", "instagram")
        query: Termo de busca
        location: Localização
        limit_per_source: Limite por fonte
        campaign_id: ID da campanha
    
    Returns:
        Dict com resultados consolidados
    """
    try:
        logger.info(f"Batch scraping: {sources} para '{query}' em {location}")
        
        all_prospects = []
        results_by_source = {}
        
        for source in sources:
            if source == "google":
                result = scrape_google_search.delay(
                    query=query,
                    location=location,
                    limit=limit_per_source,
                    campaign_id=campaign_id,
                )
                results_by_source["google"] = result.id
                
            elif source == "google_maps":
                result = scrape_google_maps.delay(
                    query=query,
                    location=location,
                    limit=limit_per_source,
                    campaign_id=campaign_id,
                )
                results_by_source["google_maps"] = result.id
            
            elif source == "instagram":
                result = scrape_instagram.delay(
                    query=query,
                    location=location,
                    limit=limit_per_source,
                    campaign_id=campaign_id,
                )
                results_by_source["instagram"] = result.id
        
        return {
            "status": "dispatched",
            "query": query,
            "location": location,
            "sources": sources,
            "task_ids": results_by_source,
            "campaign_id": campaign_id,
        }
        
    except Exception as e:
        logger.error(f"Erro no batch scraping: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=90)
def scrape_instagram(
    self,
    query: str,
    location: str,
    limit: int = 30,
    campaign_id: str = None,
) -> Dict[str, Any]:
    """
    Scrape do Instagram para encontrar perfis de negócios.
    
    Args:
        query: Termo de busca ou hashtag
        location: Localização (para contexto)
        limit: Número máximo de resultados
        campaign_id: ID da campanha (opcional)
    
    Returns:
        Dict com resultados do scraping
    """
    try:
        logger.info(f"Iniciando scraping Instagram: {query}")
        
        async def _scrape():
            async with InstagramScraper() as scraper:
                return await scraper.scrape(query, location, limit)
        
        result: ScrapeResult = run_async(_scrape())
        
        output = {
            "status": "success" if result.success else "error",
            "query": query,
            "location": location,
            "total_found": result.total_found,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
            "prospects": [b.to_dict() for b in result.businesses],
        }
        
        if campaign_id:
            output["campaign_id"] = campaign_id
        
        logger.info(f"Scraping Instagram concluído: {result.total_found} perfis encontrados")
        return output
        
    except Exception as e:
        logger.error(f"Erro no scraping Instagram: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def scrape_instagram_profile(
    self,
    username: str,
) -> Dict[str, Any]:
    """
    Extrai dados de um perfil específico do Instagram.
    
    Args:
        username: Nome de usuário do Instagram (sem @)
    
    Returns:
        Dict com dados do perfil
    """
    try:
        logger.info(f"Extraindo perfil Instagram: @{username}")
        
        async def _scrape():
            async with InstagramScraper() as scraper:
                return await scraper.get_profile(username)
        
        profile = run_async(_scrape())
        
        if profile:
            return {
                "status": "success",
                "username": username,
                "profile": profile.to_dict(),
            }
        else:
            return {
                "status": "error",
                "username": username,
                "error": "Perfil não encontrado",
            }
        
    except Exception as e:
        logger.error(f"Erro ao extrair perfil @{username}: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def scrape_instagram_hashtag(
    self,
    hashtag: str,
    limit: int = 30,
    campaign_id: str = None,
) -> Dict[str, Any]:
    """
    Busca perfis de negócios por hashtag no Instagram.
    
    Args:
        hashtag: Hashtag para buscar (sem #)
        limit: Número máximo de perfis
        campaign_id: ID da campanha (opcional)
    
    Returns:
        Dict com resultados
    """
    try:
        logger.info(f"Buscando Instagram por #{hashtag}")
        
        async def _scrape():
            async with InstagramScraper() as scraper:
                return await scraper.search_by_hashtag(hashtag, limit)
        
        profiles = run_async(_scrape())
        
        output = {
            "status": "success",
            "hashtag": hashtag,
            "total_found": len(profiles),
            "prospects": [p.to_dict() for p in profiles],
        }
        
        if campaign_id:
            output["campaign_id"] = campaign_id
        
        logger.info(f"Busca #{hashtag} concluída: {len(profiles)} perfis encontrados")
        return output
        
    except Exception as e:
        logger.error(f"Erro na busca #{hashtag}: {str(e)}")
        raise self.retry(exc=e)
