"""
Endpoints de Campanhas.
"""

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.agent import Agent
from app.db.models.plan import ServicePlan
from app.db.models.campaign import Campaign, CampaignStatus, ProspectingSource, campaign_plans
from app.db.models.prospect import Prospect
from app.db.models.message import Message
from app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse, 
    CampaignDetail, CampaignStartScraping, CampaignListItem
)
from app.schemas.prospect import ProspectResponse
from app.schemas.common import MessageResponse
from app.dependencies import get_current_user, get_pagination_params
from app.tasks.scraping import (
    scrape_google_maps, 
    scrape_google_search, 
    scrape_instagram,
    batch_scrape_prospects
)
from app.tasks.continuous_scraping import start_campaign_scraping as start_continuous_scraping_task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria uma nova campanha de prospecção.
    
    - **name**: Nome da campanha
    - **description**: Descrição da campanha
    - **prospecting_source**: Fonte de prospecção (google, google_maps, instagram, all)
    - **niche**: Nicho de mercado (ex: restaurantes)
    - **location**: Localização alvo (ex: São Paulo, SP)
    - **hashtags**: Lista de hashtags para busca no Instagram
    - **keywords**: Palavras-chave adicionais
    - **channel**: Canal de comunicação (instagram, whatsapp, email)
    - **agent_id**: ID do agente LLM (opcional)
    - **plan_ids**: Lista de IDs dos planos associados
    - **rate_limit**: Limite de mensagens por hora
    """
    # Verificar se agente existe e pertence ao usuário
    if campaign_data.agent_id:
        result = await db.execute(
            select(Agent)
            .where(Agent.id == campaign_data.agent_id, Agent.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agente não encontrado",
            )
    
    # Criar campanha com novos campos
    campaign = Campaign(
        user_id=current_user.id,
        name=campaign_data.name,
        description=campaign_data.description,
        prospecting_source=campaign_data.prospecting_source,
        niche=campaign_data.niche,
        location=campaign_data.location,
        hashtags=campaign_data.hashtags,
        keywords=campaign_data.keywords,
        channel=campaign_data.channel,
        agent_id=campaign_data.agent_id,
        rate_limit=campaign_data.rate_limit,
        search_config=campaign_data.search_config.model_dump(),
    )
    
    db.add(campaign)
    await db.flush()
    
    # Associar planos
    if campaign_data.plan_ids:
        result = await db.execute(
            select(ServicePlan)
            .where(
                ServicePlan.id.in_(campaign_data.plan_ids),
                ServicePlan.user_id == current_user.id
            )
        )
        plans = result.scalars().all()
        
        for plan in plans:
            campaign.plans.append(plan)
    
    await db.commit()
    await db.refresh(campaign)
    
    return campaign


@router.get("", response_model=List[CampaignListItem])
async def list_campaigns(
    status_filter: CampaignStatus = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    """
    Lista todas as campanhas do usuário com contadores.
    
    - **status_filter**: Filtrar por status (opcional)
    """
    query = (
        select(Campaign)
        .options(selectinload(Campaign.agent))
        .where(Campaign.user_id == current_user.id)
    )
    
    if status_filter:
        query = query.where(Campaign.status == status_filter)
    
    query = query.offset(pagination["offset"]).limit(pagination["page_size"]).order_by(Campaign.created_at.desc())
    
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    # Adicionar contadores para cada campanha
    from app.db.models.message import MessageDirection
    
    campaign_list = []
    for campaign in campaigns:
        # Contar prospects
        prospects_count = await db.execute(
            select(func.count(Prospect.id)).where(Prospect.campaign_id == campaign.id)
        )
        
        # Contar mensagens enviadas (outbound)
        messages_count = await db.execute(
            select(func.count(Message.id)).where(
                Message.campaign_id == campaign.id,
                Message.direction == MessageDirection.OUTBOUND
            )
        )
        
        # Contar respostas (mensagens inbound)
        responses_count = await db.execute(
            select(func.count(Message.id)).where(
                Message.campaign_id == campaign.id,
                Message.direction == MessageDirection.INBOUND
            )
        )
        
        campaign_dict = {
            "id": campaign.id,
            "user_id": campaign.user_id,
            "agent_id": campaign.agent_id,
            "name": campaign.name,
            "description": campaign.description,
            "status": campaign.status,
            "prospecting_source": campaign.prospecting_source,
            "niche": campaign.niche,
            "location": campaign.location,
            "hashtags": campaign.hashtags or [],
            "keywords": campaign.keywords or [],
            "channel": campaign.channel,
            "rate_limit": campaign.rate_limit,
            "search_config": campaign.search_config or {},
            "created_at": campaign.created_at,
            "updated_at": campaign.updated_at,
            "prospects_count": prospects_count.scalar() or 0,
            "messages_count": messages_count.scalar() or 0,
            "responses_count": responses_count.scalar() or 0,
            "agent_name": campaign.agent.name if campaign.agent else None,
        }
        campaign_list.append(campaign_dict)
    
    return campaign_list


@router.get("/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os detalhes de uma campanha específica.
    """
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.agent))
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    # Carregar plans separadamente (devido ao lazy="dynamic")
    plans_result = await db.execute(
        select(ServicePlan)
        .join(campaign_plans, ServicePlan.id == campaign_plans.c.plan_id)
        .where(campaign_plans.c.campaign_id == campaign.id)
    )
    plans = plans_result.scalars().all()
    
    # Contar prospects e mensagens
    prospects_count = await db.execute(
        select(func.count(Prospect.id)).where(Prospect.campaign_id == campaign.id)
    )
    messages_count = await db.execute(
        select(func.count(Message.id)).where(Message.campaign_id == campaign.id)
    )
    
    # Adicionar contagens ao response
    campaign_dict = {
        **campaign.__dict__,
        "plans": plans,
        "prospects_count": prospects_count.scalar() or 0,
        "messages_count": messages_count.scalar() or 0,
    }
    
    return campaign_dict


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza uma campanha existente.
    """
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    if campaign.status == CampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível editar uma campanha ativa. Pause-a primeiro.",
        )
    
    # Atualizar campos fornecidos
    update_data = campaign_data.model_dump(exclude_unset=True, exclude={"plan_ids"})
    
    if "search_config" in update_data and update_data["search_config"]:
        update_data["search_config"] = update_data["search_config"]
    
    for field, value in update_data.items():
        if value is not None:
            setattr(campaign, field, value)
    
    # Atualizar planos se fornecidos
    if campaign_data.plan_ids is not None:
        result = await db.execute(
            select(ServicePlan)
            .where(
                ServicePlan.id.in_(campaign_data.plan_ids),
                ServicePlan.user_id == current_user.id
            )
        )
        plans = result.scalars().all()
        campaign.plans = plans
    
    await db.commit()
    await db.refresh(campaign)
    
    return campaign


@router.delete("/{campaign_id}", response_model=MessageResponse)
async def delete_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deleta uma campanha.
    """
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    if campaign.status == CampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível deletar uma campanha ativa. Pause-a primeiro.",
        )
    
    await db.delete(campaign)
    await db.commit()
    
    return MessageResponse(message="Campanha deletada com sucesso")


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: UUID,
    auto_scrape: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia uma campanha.
    
    - **auto_scrape**: Se True (padrão), inicia automaticamente o scraping contínuo de prospects
    
    O scraping contínuo irá buscar leads até que:
    1. O limite de leads do plano seja atingido
    2. O usuário pause a campanha manualmente
    """
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    if campaign.status == CampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campanha já está ativa",
        )
    
    if not campaign.agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campanha precisa ter um agente configurado",
        )
    
    campaign.status = CampaignStatus.ACTIVE
    await db.commit()
    await db.refresh(campaign)
    
    # Disparar scraping contínuo automaticamente se configurado
    logger.info(f"Campanha {campaign_id} ativada. auto_scrape={auto_scrape}")
    
    if auto_scrape:
        try:
            # Iniciar scraping contínuo
            result = start_continuous_scraping_task(str(campaign_id), current_user.id)
            logger.info(f"✅ Scraping contínuo iniciado para campanha {campaign_id}: {result}")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar scraping contínuo para campanha {campaign_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Não falhar a requisição, apenas logar o erro
    
    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pausa uma campanha ativa.
    """
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    if campaign.status != CampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campanha não está ativa",
        )
    
    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    await db.refresh(campaign)
    
    return campaign


@router.post("/{campaign_id}/complete", response_model=CampaignResponse)
async def complete_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Marca uma campanha como concluída.
    """
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    campaign.status = CampaignStatus.COMPLETED
    await db.commit()
    await db.refresh(campaign)
    
    return campaign


@router.post("/{campaign_id}/scrape")
async def start_campaign_scraping(
    campaign_id: UUID,
    scraping_config: CampaignStartScraping = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia o scraping de prospects para uma campanha.
    
    Usa as configurações da campanha (prospecting_source, niche, location, hashtags)
    para buscar prospects nas fontes configuradas.
    
    - **limit**: Limite de prospects por fonte (default: 50)
    - **sources_override**: Sobrescrever fontes da campanha (opcional)
    """
    if scraping_config is None:
        scraping_config = CampaignStartScraping()
    
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    # Montar query de busca
    search_query = campaign.get_search_query()
    if not search_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campanha precisa ter nicho ou keywords configurados para buscar prospects",
        )
    
    location = campaign.location or ""
    
    # Determinar fontes de scraping
    if scraping_config.sources_override:
        sources = scraping_config.sources_override
    else:
        # Mapear fonte configurada para lista de fontes
        source_mapping = {
            ProspectingSource.GOOGLE: ["google"],
            ProspectingSource.GOOGLE_MAPS: ["google_maps"],
            ProspectingSource.INSTAGRAM: ["instagram"],
            ProspectingSource.LINKEDIN: ["google"],  # LinkedIn não implementado, fallback para Google
            ProspectingSource.ALL: ["google", "google_maps", "instagram"],
        }
        sources = source_mapping.get(campaign.prospecting_source, ["google_maps"])
    
    task_ids = {}
    
    # Disparar tasks de scraping para cada fonte
    for source in sources:
        if source == "google":
            task = scrape_google_search.delay(
                query=search_query,
                location=location,
                limit=scraping_config.limit,
                campaign_id=str(campaign_id),
            )
            task_ids["google"] = task.id
            
        elif source == "google_maps":
            task = scrape_google_maps.delay(
                query=search_query,
                location=location,
                limit=scraping_config.limit,
                campaign_id=str(campaign_id),
                save_progressive=True,  # Salvar conforme encontra
                detailed_mode=True,  # Modo detalhado para obter telefone/website
                extract_emails=False,  # Não extrair emails por padrão
            )
            task_ids["google_maps"] = task.id
            
        elif source == "instagram":
            # Para Instagram, usar hashtags se disponíveis
            instagram_query = search_query
            if campaign.hashtags:
                instagram_query = campaign.hashtags[0]  # Usar primeira hashtag
            
            task = scrape_instagram.delay(
                query=instagram_query,
                location=location,
                limit=scraping_config.limit,
                campaign_id=str(campaign_id),
            )
            task_ids["instagram"] = task.id
    
    return {
        "status": "dispatched",
        "message": f"Scraping iniciado em {len(sources)} fonte(s)",
        "campaign_id": str(campaign_id),
        "search_query": search_query,
        "location": location,
        "sources": sources,
        "task_ids": task_ids,
    }


@router.get("/{campaign_id}/scraping-sources")
async def get_available_scraping_sources(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna as fontes de scraping disponíveis para a campanha.
    """
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    return {
        "configured_source": campaign.prospecting_source.value,
        "available_sources": ["google", "google_maps", "instagram"],
        "campaign_config": {
            "niche": campaign.niche,
            "location": campaign.location,
            "hashtags": campaign.hashtags,
            "keywords": campaign.keywords,
            "search_query": campaign.get_search_query(),
        }
    }


@router.get("/{campaign_id}/prospects")
async def get_campaign_prospects(
    campaign_id: UUID,
    status_filter: str = None,
    search: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    """
    Lista os prospects de uma campanha específica com paginação, busca e ordenação.
    
    - **status_filter**: Filtrar por status (found, contacted, replied, converted, ignored)
    - **search**: Buscar por nome do prospect
    - **sort_by**: Campo para ordenação (name, website_url, created_at, score)
    - **sort_order**: Direção da ordenação (asc, desc)
    """
    # Verificar se campanha existe e pertence ao usuário
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    # Query base
    base_query = select(Prospect).where(Prospect.campaign_id == campaign_id)
    
    # Aplicar filtro de status
    if status_filter:
        base_query = base_query.where(Prospect.status == status_filter)
    
    # Aplicar busca por nome
    if search:
        search_term = f"%{search}%"
        base_query = base_query.where(
            (Prospect.name.ilike(search_term)) | 
            (Prospect.username.ilike(search_term)) |
            (Prospect.company.ilike(search_term))
        )
    
    # Contar total antes de paginar
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Aplicar ordenação
    valid_sort_fields = {
        "name": Prospect.name,
        "website_url": Prospect.website_url,
        "created_at": Prospect.created_at,
        "score": Prospect.score,
        "platform": Prospect.platform,
        "status": Prospect.status,
    }
    
    sort_field = valid_sort_fields.get(sort_by, Prospect.created_at)
    
    if sort_order.lower() == "asc":
        base_query = base_query.order_by(sort_field.asc().nulls_last())
    else:
        base_query = base_query.order_by(sort_field.desc().nulls_last())
    
    # Aplicar paginação
    query = base_query.offset(pagination["offset"]).limit(pagination["page_size"])
    
    result = await db.execute(query)
    prospects = result.scalars().all()
    
    # Calcular total de páginas
    total_pages = (total + pagination["page_size"] - 1) // pagination["page_size"] if total > 0 else 1
    
    return {
        "items": prospects,
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
        "total_pages": total_pages,
    }