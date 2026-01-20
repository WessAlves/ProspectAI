"""
Tarefas de scraping contínuo para campanhas.

Este módulo implementa o scraping contínuo que mantém as campanhas
buscando leads até atingir o limite do plano ou ser pausada.
"""

import time
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.celery_app import celery_app

logger = logging.getLogger(__name__)

# Configurações de scraping contínuo
SCRAPING_INTERVAL_MINUTES = 30  # Intervalo entre buscas
MAX_LEADS_PER_SEARCH = 50  # Máximo de leads por busca
MIN_INTERVAL_BETWEEN_SEARCHES = 300  # 5 minutos mínimo entre buscas


def _create_db_session():
    """Cria uma sessão de banco síncrona."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    db_url = str(settings.DATABASE_URL)
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def _get_campaign_info(db_session, campaign_id: str) -> Optional[Dict]:
    """Obtém informações da campanha."""
    from app.db.models.campaign import Campaign, CampaignStatus
    
    campaign = db_session.query(Campaign).filter(
        Campaign.id == UUID(campaign_id)
    ).first()
    
    if not campaign:
        return None
    
    # Montar search query
    search_query = campaign.get_search_query()
    
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "status": campaign.status,
        "user_id": campaign.user_id,
        "search_query": search_query,
        "niche": campaign.niche,
        "location": campaign.location or "",
        "keywords": campaign.keywords or [],
        "prospecting_source": campaign.prospecting_source,
        "current_leads": 0,  # Será calculado
    }


def _count_campaign_leads(db_session, campaign_id: str) -> int:
    """Conta leads da campanha."""
    from app.db.models.prospect import Prospect
    
    count = db_session.query(Prospect).filter(
        Prospect.campaign_id == UUID(campaign_id)
    ).count()
    
    return count


def _check_user_lead_limit(db_session, user_id) -> tuple[bool, int]:
    """Verifica se usuário pode adicionar mais leads."""
    from app.services.lead_limits import sync_check_can_add_lead
    return sync_check_can_add_lead(db_session, user_id)


def _is_campaign_active(db_session, campaign_id: str) -> bool:
    """Verifica se a campanha está ativa."""
    from app.db.models.campaign import Campaign, CampaignStatus
    
    campaign = db_session.query(Campaign).filter(
        Campaign.id == UUID(campaign_id)
    ).first()
    
    return campaign and campaign.status == CampaignStatus.ACTIVE


@celery_app.task(bind=True, max_retries=0, time_limit=1800, soft_time_limit=1700)
def continuous_scraping(
    self,
    campaign_id: str,
    search_query: str = None,
    location: str = None,
) -> Dict[str, Any]:
    """
    Task de scraping contínuo para uma campanha.
    
    Esta task:
    1. Executa uma busca de leads
    2. Verifica se a campanha ainda está ativa
    3. Verifica se o limite de leads foi atingido
    4. Se não, reagenda uma nova busca após o intervalo
    
    Args:
        campaign_id: ID da campanha
        search_query: Termo de busca (usa keywords da campanha se não fornecido)
        location: Localização (usa da campanha se não fornecida)
    """
    db_session = None
    
    try:
        db_session = _create_db_session()
        
        # Obter informações da campanha
        campaign_info = _get_campaign_info(db_session, campaign_id)
        if not campaign_info:
            logger.error(f"Campanha {campaign_id} não encontrada")
            return {"status": "error", "message": "Campanha não encontrada"}
        
        # Verificar se campanha está ativa
        if not _is_campaign_active(db_session, campaign_id):
            logger.info(f"Campanha {campaign_id} não está ativa. Parando scraping contínuo.")
            return {
                "status": "stopped",
                "reason": "campaign_not_active",
                "campaign_id": campaign_id,
            }
        
        # Verificar limite de leads do usuário
        can_add, remaining = _check_user_lead_limit(db_session, campaign_info["user_id"])
        if not can_add:
            logger.info(f"Limite de leads atingido para campanha {campaign_id}")
            
            # Notificar via WebSocket
            from app.services.notifications import publish_limit_reached
            publish_limit_reached(str(campaign_info["user_id"]), campaign_id)
            
            return {
                "status": "limit_reached",
                "campaign_id": campaign_id,
                "message": "Limite de leads atingido",
            }
        
        # Contar leads atuais da campanha
        current_leads = _count_campaign_leads(db_session, campaign_id)
        
        # Calcular quantos leads buscar (limita a MAX_LEADS_PER_SEARCH por ciclo)
        leads_to_fetch = min(
            MAX_LEADS_PER_SEARCH,
            remaining if remaining != -1 else MAX_LEADS_PER_SEARCH
        )
        
        # Definir query e location
        query = search_query
        if not query:
            query = campaign_info.get("search_query")
        if not query and campaign_info.get("niche"):
            query = campaign_info["niche"]
        if not query:
            query = campaign_info.get("name", "empresas")
        
        loc = location or campaign_info.get("location", "Brasil")
        
        logger.info(
            f"🔄 Scraping contínuo para campanha {campaign_id}: "
            f"'{query}' em '{loc}' (buscar: {leads_to_fetch} leads, já tem: {current_leads})"
        )
        
        db_session.close()
        db_session = None
        
        # Executar scraping
        from app.tasks.scraping import scrape_google_maps
        result = scrape_google_maps(
            query=query,
            location=loc,
            limit=leads_to_fetch,
            campaign_id=campaign_id,
            save_progressive=True,
            detailed_mode=True,
        )
        
        # Verificar resultado
        saved_count = result.get("saved_count", 0)
        limit_reached = result.get("limit_reached", False)
        
        logger.info(
            f"📊 Resultado scraping contínuo: "
            f"{saved_count} leads salvos para campanha {campaign_id}"
        )
        
        # Se limite atingido, parar
        if limit_reached:
            return {
                "status": "limit_reached",
                "campaign_id": campaign_id,
                "saved_count": saved_count,
            }
        
        # Reagendar próxima busca se campanha ainda ativa
        db_session = _create_db_session()
        if _is_campaign_active(db_session, campaign_id):
            # Verificar se ainda pode adicionar leads
            can_continue, leads_remaining = _check_user_lead_limit(db_session, campaign_info["user_id"])
            
            if can_continue:
                # Agendar próxima execução
                next_run = datetime.utcnow() + timedelta(minutes=SCRAPING_INTERVAL_MINUTES)
                
                continuous_scraping.apply_async(
                    args=[campaign_id, query, loc],
                    eta=next_run,
                )
                
                new_lead_count = _count_campaign_leads(db_session, campaign_id)
                logger.info(
                    f"⏰ Próximo scraping para campanha {campaign_id} agendado para "
                    f"{next_run.strftime('%H:%M:%S UTC')} (total leads: {new_lead_count})"
                )
                
                return {
                    "status": "success",
                    "campaign_id": campaign_id,
                    "saved_count": saved_count,
                    "total_leads": new_lead_count,
                    "leads_remaining": leads_remaining,
                    "next_run": next_run.isoformat(),
                    "continuing": True,
                }
            else:
                new_lead_count = _count_campaign_leads(db_session, campaign_id)
                logger.info(f"Campanha {campaign_id} atingiu limite do plano: {new_lead_count} leads")
                
                # Notificar via WebSocket
                from app.services.notifications import publish_limit_reached
                publish_limit_reached(str(campaign_info["user_id"]), campaign_id)
                
                return {
                    "status": "limit_reached",
                    "campaign_id": campaign_id,
                    "total_leads": new_lead_count,
                }
        
        return {
            "status": "stopped",
            "reason": "campaign_paused",
            "campaign_id": campaign_id,
            "saved_count": saved_count,
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no scraping contínuo: {str(e)}")
        return {
            "status": "error",
            "campaign_id": campaign_id,
            "error": str(e),
        }
    finally:
        if db_session:
            db_session.close()


@celery_app.task(bind=True)
def start_continuous_scraping(self, campaign_id: str) -> Dict[str, Any]:
    """
    Inicia o scraping contínuo para uma campanha.
    
    Chamado quando uma campanha é iniciada/ativada.
    """
    logger.info(f"🚀 Iniciando scraping contínuo para campanha {campaign_id}")
    
    # Iniciar primeira execução imediatamente
    task = continuous_scraping.delay(campaign_id)
    
    return {
        "status": "started",
        "campaign_id": campaign_id,
        "task_id": task.id,
        "message": "Scraping contínuo iniciado",
    }


@celery_app.task(bind=True)
def stop_continuous_scraping(self, campaign_id: str) -> Dict[str, Any]:
    """
    Para o scraping contínuo de uma campanha.
    
    O scraping para automaticamente quando detecta que a campanha
    não está mais ativa, então esta task é mais para feedback.
    """
    logger.info(f"⏹️ Parando scraping contínuo para campanha {campaign_id}")
    
    return {
        "status": "stop_requested",
        "campaign_id": campaign_id,
        "message": "O scraping será interrompido na próxima verificação",
    }


def get_scraping_status(campaign_id: str) -> Dict[str, Any]:
    """
    Obtém status do scraping contínuo de uma campanha.
    
    Returns:
        Dict com status atual
    """
    db_session = None
    try:
        db_session = _create_db_session()
        
        campaign_info = _get_campaign_info(db_session, campaign_id)
        if not campaign_info:
            return {"status": "not_found"}
        
        current_leads = _count_campaign_leads(db_session, campaign_id)
        is_active = _is_campaign_active(db_session, campaign_id)
        
        can_add, remaining = _check_user_lead_limit(db_session, campaign_info["user_id"])
        
        return {
            "status": "active" if is_active else "paused",
            "campaign_id": campaign_id,
            "current_leads": current_leads,
            "can_add_more": can_add,
            "leads_remaining": remaining,
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        if db_session:
            db_session.close()


def start_campaign_scraping(campaign_id: str, user_id: int = None) -> Dict[str, Any]:
    """
    Helper para iniciar scraping contínuo de uma campanha.
    
    Chamado pelo endpoint quando uma campanha é ativada.
    
    Args:
        campaign_id: ID da campanha
        user_id: ID do usuário (opcional, para logging)
        
    Returns:
        Dict com status de inicialização
    """
    logger.info(f"🚀 Iniciando scraping contínuo para campanha {campaign_id} (user: {user_id})")
    
    # Dispara a task de início
    task = start_continuous_scraping.delay(campaign_id)
    
    return {
        "status": "started",
        "campaign_id": campaign_id,
        "task_id": task.id,
        "message": "Scraping contínuo iniciado com sucesso",
    }
