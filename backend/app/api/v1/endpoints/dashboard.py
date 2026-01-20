"""
Endpoints de Dashboard e Analytics.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from app.db.session import get_db
from app.db.models.user import User, PLAN_LIMITS
from app.db.models.agent import Agent
from app.db.models.campaign import Campaign, CampaignStatus
from app.db.models.prospect import Prospect, ProspectStatus
from app.db.models.message import Message, MessageDirection, MessageStatus
from app.db.models.metrics import CampaignMetrics
from app.schemas.dashboard import (
    DashboardOverview,
    FunnelMetrics,
    CampaignComparison,
    DateRangeMetrics,
    UsageLimits,
    InteractionHistoryItem,
    InteractionHistoryResponse,
    FunnelStage,
    FunnelReportResponse,
    CampaignComparisonItem,
    CampaignComparisonResponse,
    DashboardFeatures,
    FullDashboardResponse,
    TimelineEntry,
)
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna uma visão geral do dashboard do usuário.
    """
    # Total e ativas de campanhas
    campaigns_result = await db.execute(
        select(func.count(Campaign.id), Campaign.status)
        .where(Campaign.user_id == current_user.id)
        .group_by(Campaign.status)
    )
    campaigns_by_status = {status: count for count, status in campaigns_result.fetchall()}
    total_campaigns = sum(campaigns_by_status.values())
    active_campaigns = campaigns_by_status.get(CampaignStatus.ACTIVE, 0)
    
    # IDs das campanhas do usuário
    campaign_ids_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    campaign_ids = [c[0] for c in campaign_ids_result.fetchall()]
    
    if not campaign_ids:
        return DashboardOverview(
            total_campaigns=0,
            active_campaigns=0,
            total_leads=0,
            total_messages_sent=0,
            total_replies=0,
            total_conversions=0,
            conversion_rate=0.0,
            reply_rate=0.0,
        )
    
    # Total de leads (prospects)
    leads_result = await db.execute(
        select(func.count(Prospect.id))
        .where(Prospect.campaign_id.in_(campaign_ids))
    )
    total_leads = leads_result.scalar() or 0
    
    # Conversões
    conversions_result = await db.execute(
        select(func.count(Prospect.id))
        .where(
            Prospect.campaign_id.in_(campaign_ids),
            Prospect.status == ProspectStatus.CONVERTED
        )
    )
    total_conversions = conversions_result.scalar() or 0
    
    # Mensagens enviadas
    messages_sent_result = await db.execute(
        select(func.count(Message.id))
        .where(
            Message.campaign_id.in_(campaign_ids),
            Message.direction == MessageDirection.OUTBOUND
        )
    )
    total_messages_sent = messages_sent_result.scalar() or 0
    
    # Respostas recebidas
    replies_result = await db.execute(
        select(func.count(Message.id))
        .where(
            Message.campaign_id.in_(campaign_ids),
            Message.direction == MessageDirection.INBOUND
        )
    )
    total_replies = replies_result.scalar() or 0
    
    # Calcular taxas
    conversion_rate = (total_conversions / total_leads * 100) if total_leads > 0 else 0.0
    reply_rate = (total_replies / total_messages_sent * 100) if total_messages_sent > 0 else 0.0
    
    return DashboardOverview(
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_leads=total_leads,
        total_messages_sent=total_messages_sent,
        total_replies=total_replies,
        total_conversions=total_conversions,
        conversion_rate=round(conversion_rate, 2),
        reply_rate=round(reply_rate, 2),
    )


@router.get("/funnel/{campaign_id}", response_model=FunnelMetrics)
async def get_campaign_funnel(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna as métricas do funil de uma campanha específica.
    """
    # Verificar se campanha pertence ao usuário
    campaign_result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada",
        )
    
    # Leads encontrados
    found_result = await db.execute(
        select(func.count(Prospect.id))
        .where(Prospect.campaign_id == campaign_id)
    )
    leads_found = found_result.scalar() or 0
    
    # Mensagens enviadas
    sent_result = await db.execute(
        select(func.count(Message.id))
        .where(
            Message.campaign_id == campaign_id,
            Message.direction == MessageDirection.OUTBOUND
        )
    )
    messages_sent = sent_result.scalar() or 0
    
    # Mensagens entregues
    delivered_result = await db.execute(
        select(func.count(Message.id))
        .where(
            Message.campaign_id == campaign_id,
            Message.direction == MessageDirection.OUTBOUND,
            Message.status.in_([MessageStatus.DELIVERED, MessageStatus.READ])
        )
    )
    messages_delivered = delivered_result.scalar() or 0
    
    # Mensagens lidas
    read_result = await db.execute(
        select(func.count(Message.id))
        .where(
            Message.campaign_id == campaign_id,
            Message.direction == MessageDirection.OUTBOUND,
            Message.status == MessageStatus.READ
        )
    )
    messages_read = read_result.scalar() or 0
    
    # Respostas recebidas
    replies_result = await db.execute(
        select(func.count(Message.id))
        .where(
            Message.campaign_id == campaign_id,
            Message.direction == MessageDirection.INBOUND
        )
    )
    replies_received = replies_result.scalar() or 0
    
    # Conversões
    conversions_result = await db.execute(
        select(func.count(Prospect.id))
        .where(
            Prospect.campaign_id == campaign_id,
            Prospect.status == ProspectStatus.CONVERTED
        )
    )
    conversions = conversions_result.scalar() or 0
    
    # Calcular taxas
    delivery_rate = (messages_delivered / messages_sent * 100) if messages_sent > 0 else 0.0
    read_rate = (messages_read / messages_delivered * 100) if messages_delivered > 0 else 0.0
    reply_rate = (replies_received / messages_sent * 100) if messages_sent > 0 else 0.0
    conversion_rate = (conversions / leads_found * 100) if leads_found > 0 else 0.0
    
    return FunnelMetrics(
        leads_found=leads_found,
        messages_sent=messages_sent,
        messages_delivered=messages_delivered,
        messages_read=messages_read,
        replies_received=replies_received,
        conversions=conversions,
        delivery_rate=round(delivery_rate, 2),
        read_rate=round(read_rate, 2),
        reply_rate=round(reply_rate, 2),
        conversion_rate=round(conversion_rate, 2),
    )


@router.get("/compare", response_model=List[CampaignComparison])
async def compare_campaigns(
    campaign_ids: List[UUID] = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compara métricas entre múltiplas campanhas.
    """
    # Verificar se todas as campanhas pertencem ao usuário
    campaigns_result = await db.execute(
        select(Campaign)
        .where(
            Campaign.id.in_(campaign_ids),
            Campaign.user_id == current_user.id
        )
    )
    campaigns = campaigns_result.scalars().all()
    
    if len(campaigns) != len(campaign_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uma ou mais campanhas não encontradas",
        )
    
    comparisons = []
    
    for campaign in campaigns:
        # Total de leads
        leads_result = await db.execute(
            select(func.count(Prospect.id))
            .where(Prospect.campaign_id == campaign.id)
        )
        total_leads = leads_result.scalar() or 0
        
        # Total de mensagens
        messages_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id == campaign.id,
                Message.direction == MessageDirection.OUTBOUND
            )
        )
        total_messages = messages_result.scalar() or 0
        
        # Respostas
        replies_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id == campaign.id,
                Message.direction == MessageDirection.INBOUND
            )
        )
        total_replies = replies_result.scalar() or 0
        
        # Conversões
        conversions_result = await db.execute(
            select(func.count(Prospect.id))
            .where(
                Prospect.campaign_id == campaign.id,
                Prospect.status == ProspectStatus.CONVERTED
            )
        )
        conversions = conversions_result.scalar() or 0
        
        reply_rate = (total_replies / total_messages * 100) if total_messages > 0 else 0.0
        conversion_rate = (conversions / total_leads * 100) if total_leads > 0 else 0.0
        
        comparisons.append(CampaignComparison(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            total_leads=total_leads,
            total_messages=total_messages,
            reply_rate=round(reply_rate, 2),
            conversion_rate=round(conversion_rate, 2),
        ))
    
    return comparisons


@router.get("/timeline", response_model=List[DateRangeMetrics])
async def get_timeline_metrics(
    days: int = Query(default=30, ge=1, le=365),
    campaign_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna métricas agregadas por dia.
    """
    start_date = date.today() - timedelta(days=days)
    
    # Verificar campanhas do usuário
    if campaign_id:
        campaign_result = await db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        )
        if not campaign_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
        campaign_filter = CampaignMetrics.campaign_id == campaign_id
    else:
        campaign_ids_result = await db.execute(
            select(Campaign.id).where(Campaign.user_id == current_user.id)
        )
        campaign_ids = [c[0] for c in campaign_ids_result.fetchall()]
        if not campaign_ids:
            return []
        campaign_filter = CampaignMetrics.campaign_id.in_(campaign_ids)
    
    # Buscar métricas agregadas
    metrics_result = await db.execute(
        select(
            CampaignMetrics.date,
            func.sum(CampaignMetrics.prospects_found),
            func.sum(CampaignMetrics.messages_sent),
            func.sum(CampaignMetrics.replies_received),
            func.sum(CampaignMetrics.conversions),
        )
        .where(campaign_filter, CampaignMetrics.date >= start_date)
        .group_by(CampaignMetrics.date)
        .order_by(CampaignMetrics.date)
    )
    
    timeline = []
    for row in metrics_result.fetchall():
        timeline.append(DateRangeMetrics(
            date=row[0],
            leads_found=row[1] or 0,
            messages_sent=row[2] or 0,
            replies_received=row[3] or 0,
            conversions=row[4] or 0,
        ))
    
    return timeline


@router.get("/metrics")
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna as métricas principais do dashboard.
    Endpoint esperado pelo frontend.
    """
    from datetime import datetime, timedelta
    from app.db.models.agent import Agent
    
    # Contar campanhas ativas
    campaigns_result = await db.execute(
        select(func.count(Campaign.id))
        .where(Campaign.user_id == current_user.id, Campaign.status == CampaignStatus.ACTIVE)
    )
    active_campaigns = campaigns_result.scalar() or 0
    
    # Contar agentes que estão em campanhas ativas (agentes ativos rodando)
    active_agents_result = await db.execute(
        select(func.count(func.distinct(Campaign.agent_id)))
        .where(
            Campaign.user_id == current_user.id,
            Campaign.status == CampaignStatus.ACTIVE,
            Campaign.agent_id.isnot(None)
        )
    )
    active_agents = active_agents_result.scalar() or 0
    
    # IDs das campanhas do usuário
    campaign_ids_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    campaign_ids = [c[0] for c in campaign_ids_result.fetchall()]
    
    total_leads = 0
    messages_sent_today = 0
    response_rate = 0.0
    conversion_rate = 0.0
    
    if campaign_ids:
        # Total de leads
        leads_result = await db.execute(
            select(func.count(Prospect.id))
            .where(Prospect.campaign_id.in_(campaign_ids))
        )
        total_leads = leads_result.scalar() or 0
        
        # Mensagens enviadas hoje
        today = datetime.utcnow().date()
        messages_today_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id.in_(campaign_ids),
                Message.direction == MessageDirection.OUTBOUND,
                func.date(Message.created_at) == today
            )
        )
        messages_sent_today = messages_today_result.scalar() or 0
        
        # Total de mensagens enviadas
        total_sent_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id.in_(campaign_ids),
                Message.direction == MessageDirection.OUTBOUND
            )
        )
        total_sent = total_sent_result.scalar() or 0
        
        # Total de respostas
        total_replies_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id.in_(campaign_ids),
                Message.direction == MessageDirection.INBOUND
            )
        )
        total_replies = total_replies_result.scalar() or 0
        
        # Conversões
        conversions_result = await db.execute(
            select(func.count(Prospect.id))
            .where(
                Prospect.campaign_id.in_(campaign_ids),
                Prospect.status == ProspectStatus.CONVERTED
            )
        )
        total_conversions = conversions_result.scalar() or 0
        
        # Calcular taxas
        response_rate = (total_replies / total_sent * 100) if total_sent > 0 else 0.0
        conversion_rate = (total_conversions / total_leads * 100) if total_leads > 0 else 0.0
    
    return {
        "total_leads": total_leads,
        "active_agents": active_agents,
        "active_campaigns": active_campaigns,
        "messages_sent_today": messages_sent_today,
        "response_rate": round(response_rate, 2),
        "conversion_rate": round(conversion_rate, 2),
    }


@router.get("/recent-activities")
async def get_recent_activities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna as atividades recentes e top agentes.
    Endpoint esperado pelo frontend.
    """
    from datetime import datetime, timedelta
    from app.db.models.agent import Agent
    
    activities = []
    
    # Buscar campanhas recentes
    recent_campaigns = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == current_user.id)
        .order_by(Campaign.created_at.desc())
        .limit(5)
    )
    for campaign in recent_campaigns.scalars():
        activities.append({
            "id": str(campaign.id),
            "type": "campaign",
            "description": f"Campanha '{campaign.name}' criada",
            "timestamp": campaign.created_at.strftime("%d/%m/%Y %H:%M"),
        })
    
    # Top agentes (por enquanto, só listar os agentes)
    top_agents_result = await db.execute(
        select(Agent)
        .where(Agent.user_id == current_user.id)
        .limit(5)
    )
    top_agents = []
    for agent in top_agents_result.scalars():
        top_agents.append({
            "id": str(agent.id),
            "name": agent.name,
            "messages_sent": 0,  # TODO: calcular quando houver dados
            "response_rate": 0,
        })
    
    return {
        "activities": activities[:10],
        "top_agents": top_agents,
    }


# ============================================
# Novos endpoints para Dashboard por Plano
# ============================================

@router.get("/usage-limits", response_model=UsageLimits)
async def get_usage_limits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os limites de uso do plano atual do usuário.
    Disponível para todos os planos.
    """
    plan_limits = current_user.plan_limits
    
    # Contar agentes do usuário
    agents_result = await db.execute(
        select(func.count(Agent.id))
        .where(Agent.user_id == current_user.id)
    )
    agents_used = agents_result.scalar() or 0
    
    # Contar campanhas do usuário
    campaigns_result = await db.execute(
        select(func.count(Campaign.id))
        .where(Campaign.user_id == current_user.id)
    )
    campaigns_used = campaigns_result.scalar() or 0
    
    # Contar leads do mês atual
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    campaign_ids_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    campaign_ids = [c[0] for c in campaign_ids_result.fetchall()]
    
    leads_used = 0
    if campaign_ids:
        leads_result = await db.execute(
            select(func.count(Prospect.id))
            .where(
                Prospect.campaign_id.in_(campaign_ids),
                Prospect.created_at >= first_day_of_month
            )
        )
        leads_used = leads_result.scalar() or 0
    
    # Calcular limites restantes
    leads_limit = plan_limits["leads_per_month"]
    agents_limit = plan_limits["agents"]
    campaigns_limit = plan_limits["campaigns"]
    
    return UsageLimits(
        plan_tier=current_user.plan_tier.value,
        leads_limit=leads_limit,
        leads_used=leads_used,
        leads_remaining=max(0, leads_limit - leads_used) if leads_limit != -1 else -1,
        agents_limit=agents_limit,
        agents_used=agents_used,
        agents_remaining=max(0, agents_limit - agents_used) if agents_limit != -1 else -1,
        campaigns_limit=campaigns_limit,
        campaigns_used=campaigns_used,
        campaigns_remaining=max(0, campaigns_limit - campaigns_used) if campaigns_limit != -1 else -1,
        whatsapp_enabled=plan_limits["whatsapp_enabled"],
        whatsapp_official_api=plan_limits["whatsapp_official_api"],
        advanced_filters=plan_limits["advanced_filters"],
        funnel_reports=plan_limits["funnel_reports"],
        campaign_comparison=plan_limits["campaign_comparison"],
        crm_integration=plan_limits["crm_integration"],
        priority_support=plan_limits["priority_support"],
        sso=plan_limits["sso"],
    )


@router.get("/features", response_model=DashboardFeatures)
async def get_dashboard_features(
    current_user: User = Depends(get_current_user),
):
    """
    Retorna as features de dashboard disponíveis para o plano do usuário.
    """
    plan_limits = current_user.plan_limits
    
    return DashboardFeatures(
        basic_kpis=True,  # Sempre disponível
        interaction_history=True,  # Sempre disponível (CRM básico)
        funnel_reports=plan_limits["funnel_reports"],
        campaign_comparison=plan_limits["campaign_comparison"],
        advanced_filters=plan_limits["advanced_filters"],
        crm_integration=plan_limits["crm_integration"],
    )


@router.get("/interaction-history", response_model=InteractionHistoryResponse)
async def get_interaction_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    campaign_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o histórico de interações (CRM básico).
    Disponível para todos os planos.
    """
    # Buscar campanhas do usuário
    if campaign_id:
        campaign_result = await db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        )
        if not campaign_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
        campaign_ids = [campaign_id]
    else:
        campaign_ids_result = await db.execute(
            select(Campaign.id).where(Campaign.user_id == current_user.id)
        )
        campaign_ids = [c[0] for c in campaign_ids_result.fetchall()]
    
    if not campaign_ids:
        return InteractionHistoryResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )
    
    # Base query
    base_query = select(Prospect, Campaign.name.label("campaign_name")).join(
        Campaign, Prospect.campaign_id == Campaign.id
    ).where(Prospect.campaign_id.in_(campaign_ids))
    
    if status_filter:
        try:
            status_enum = ProspectStatus(status_filter)
            base_query = base_query.where(Prospect.status == status_enum)
        except ValueError:
            pass
    
    # Contar total
    count_result = await db.execute(
        select(func.count()).select_from(
            base_query.subquery()
        )
    )
    total = count_result.scalar() or 0
    
    # Paginar
    offset = (page - 1) * page_size
    results = await db.execute(
        base_query.order_by(Prospect.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    items = []
    for row in results.fetchall():
        prospect = row[0]
        campaign_name = row[1]
        
        # Buscar última mensagem
        last_message_result = await db.execute(
            select(Message)
            .where(Message.prospect_id == prospect.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_message = last_message_result.scalar_one_or_none()
        
        # Contar mensagens
        messages_count_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.prospect_id == prospect.id)
        )
        total_messages = messages_count_result.scalar() or 0
        
        # Contar respostas
        replies_count_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.prospect_id == prospect.id,
                Message.direction == MessageDirection.INBOUND
            )
        )
        reply_count = replies_count_result.scalar() or 0
        
        items.append(InteractionHistoryItem(
            id=prospect.id,
            lead_id=prospect.id,
            lead_name=prospect.name or prospect.username or "Sem nome",
            lead_source=prospect.source or "unknown",
            campaign_id=prospect.campaign_id,
            campaign_name=campaign_name,
            last_message=last_message.content[:100] if last_message else None,
            last_message_at=last_message.created_at if last_message else None,
            status=prospect.status.value,
            total_messages=total_messages,
            reply_count=reply_count,
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return InteractionHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/funnel-report", response_model=FunnelReportResponse)
async def get_funnel_report(
    campaign_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o relatório completo do funil de conversão.
    Disponível apenas para planos Starter+.
    """
    # Verificar se o usuário tem acesso a esta feature
    if not current_user.has_feature("funnel_reports"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu plano não inclui relatórios de funil. Faça upgrade para Starter ou superior.",
        )
    
    campaign_name = None
    
    if campaign_id:
        campaign_result = await db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        )
        campaign = campaign_result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
        campaign_ids = [campaign_id]
        campaign_name = campaign.name
    else:
        campaign_ids_result = await db.execute(
            select(Campaign.id).where(Campaign.user_id == current_user.id)
        )
        campaign_ids = [c[0] for c in campaign_ids_result.fetchall()]
    
    if not campaign_ids:
        return FunnelReportResponse(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            stages=[],
            total_leads=0,
            total_conversions=0,
            overall_conversion_rate=0.0,
        )
    
    # Contar leads por status
    status_counts = {}
    for status_type in ProspectStatus:
        result = await db.execute(
            select(func.count(Prospect.id))
            .where(
                Prospect.campaign_id.in_(campaign_ids),
                Prospect.status == status_type
            )
        )
        status_counts[status_type] = result.scalar() or 0
    
    total_leads = sum(status_counts.values())
    total_conversions = status_counts.get(ProspectStatus.CONVERTED, 0)
    
    # Criar estágios do funil
    stages = [
        FunnelStage(
            name="Encontrados",
            count=total_leads,
            percentage=100.0,
            color="#6366f1"
        ),
        FunnelStage(
            name="Contatados",
            count=status_counts.get(ProspectStatus.CONTACTED, 0) + 
                  status_counts.get(ProspectStatus.REPLIED, 0) +
                  status_counts.get(ProspectStatus.CONVERTED, 0) +
                  status_counts.get(ProspectStatus.REJECTED, 0),
            percentage=0.0,
            color="#8b5cf6"
        ),
        FunnelStage(
            name="Responderam",
            count=status_counts.get(ProspectStatus.REPLIED, 0) +
                  status_counts.get(ProspectStatus.CONVERTED, 0),
            percentage=0.0,
            color="#a855f7"
        ),
        FunnelStage(
            name="Convertidos",
            count=total_conversions,
            percentage=0.0,
            color="#22c55e"
        ),
    ]
    
    # Calcular percentuais
    for stage in stages:
        if total_leads > 0:
            stage.percentage = round(stage.count / total_leads * 100, 2)
    
    overall_conversion_rate = (total_conversions / total_leads * 100) if total_leads > 0 else 0.0
    
    return FunnelReportResponse(
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        stages=stages,
        total_leads=total_leads,
        total_conversions=total_conversions,
        overall_conversion_rate=round(overall_conversion_rate, 2),
    )


@router.get("/campaign-comparison", response_model=CampaignComparisonResponse)
async def get_campaign_comparison(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna a comparação de performance entre campanhas.
    Disponível apenas para planos Pro+.
    """
    # Verificar se o usuário tem acesso a esta feature
    if not current_user.has_feature("campaign_comparison"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu plano não inclui comparação de campanhas. Faça upgrade para Pro ou superior.",
        )
    
    # Buscar todas as campanhas do usuário
    campaigns_result = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == current_user.id)
        .order_by(Campaign.created_at.desc())
    )
    campaigns = campaigns_result.scalars().all()
    
    if not campaigns:
        return CampaignComparisonResponse(
            campaigns=[],
            avg_reply_rate=0.0,
            avg_conversion_rate=0.0,
        )
    
    comparison_items = []
    total_reply_rate = 0.0
    total_conversion_rate = 0.0
    best_score = -1
    worst_score = 101
    best_id = None
    worst_id = None
    
    for campaign in campaigns:
        # Leads
        leads_result = await db.execute(
            select(func.count(Prospect.id))
            .where(Prospect.campaign_id == campaign.id)
        )
        total_leads = leads_result.scalar() or 0
        
        # Mensagens enviadas
        sent_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id == campaign.id,
                Message.direction == MessageDirection.OUTBOUND
            )
        )
        messages_sent = sent_result.scalar() or 0
        
        # Mensagens entregues
        delivered_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id == campaign.id,
                Message.direction == MessageDirection.OUTBOUND,
                Message.status.in_([MessageStatus.DELIVERED, MessageStatus.READ])
            )
        )
        messages_delivered = delivered_result.scalar() or 0
        
        # Mensagens lidas
        read_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id == campaign.id,
                Message.direction == MessageDirection.OUTBOUND,
                Message.status == MessageStatus.READ
            )
        )
        messages_read = read_result.scalar() or 0
        
        # Respostas
        replies_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.campaign_id == campaign.id,
                Message.direction == MessageDirection.INBOUND
            )
        )
        replies_received = replies_result.scalar() or 0
        
        # Conversões
        conversions_result = await db.execute(
            select(func.count(Prospect.id))
            .where(
                Prospect.campaign_id == campaign.id,
                Prospect.status == ProspectStatus.CONVERTED
            )
        )
        conversions = conversions_result.scalar() or 0
        
        # Calcular taxas
        delivery_rate = (messages_delivered / messages_sent * 100) if messages_sent > 0 else 0.0
        read_rate = (messages_read / messages_delivered * 100) if messages_delivered > 0 else 0.0
        reply_rate = (replies_received / messages_sent * 100) if messages_sent > 0 else 0.0
        conversion_rate = (conversions / total_leads * 100) if total_leads > 0 else 0.0
        
        # Calcular score de performance (ponderado)
        performance_score = (
            delivery_rate * 0.1 +
            read_rate * 0.2 +
            reply_rate * 0.3 +
            conversion_rate * 0.4
        )
        
        total_reply_rate += reply_rate
        total_conversion_rate += conversion_rate
        
        if performance_score > best_score:
            best_score = performance_score
            best_id = campaign.id
        if performance_score < worst_score:
            worst_score = performance_score
            worst_id = campaign.id
        
        comparison_items.append(CampaignComparisonItem(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            status=campaign.status.value,
            created_at=campaign.created_at,
            total_leads=total_leads,
            messages_sent=messages_sent,
            messages_delivered=messages_delivered,
            messages_read=messages_read,
            replies_received=replies_received,
            conversions=conversions,
            delivery_rate=round(delivery_rate, 2),
            read_rate=round(read_rate, 2),
            reply_rate=round(reply_rate, 2),
            conversion_rate=round(conversion_rate, 2),
            performance_score=round(performance_score, 2),
        ))
    
    num_campaigns = len(campaigns)
    
    return CampaignComparisonResponse(
        campaigns=comparison_items,
        best_performer_id=best_id,
        worst_performer_id=worst_id,
        avg_reply_rate=round(total_reply_rate / num_campaigns, 2) if num_campaigns > 0 else 0.0,
        avg_conversion_rate=round(total_conversion_rate / num_campaigns, 2) if num_campaigns > 0 else 0.0,
    )


@router.get("/full", response_model=FullDashboardResponse)
async def get_full_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o dashboard completo com todas as seções baseado no plano do usuário.
    """
    plan_limits = current_user.plan_limits
    
    # Overview básico
    overview = await get_dashboard_overview(db=db, current_user=current_user)
    
    # Usage limits
    usage_limits = await get_usage_limits(db=db, current_user=current_user)
    
    # Features disponíveis
    features = DashboardFeatures(
        basic_kpis=True,
        interaction_history=True,
        funnel_reports=plan_limits["funnel_reports"],
        campaign_comparison=plan_limits["campaign_comparison"],
        advanced_filters=plan_limits["advanced_filters"],
        crm_integration=plan_limits["crm_integration"],
    )
    
    # Atividades recentes
    activities_data = await get_recent_activities(db=db, current_user=current_user)
    recent_activities = [
        TimelineEntry(
            timestamp=datetime.strptime(a["timestamp"], "%d/%m/%Y %H:%M"),
            event_type=a["type"],
            description=a["description"],
        )
        for a in activities_data["activities"]
    ]
    
    # Timeline de métricas (últimos 30 dias)
    timeline = await get_timeline_metrics(days=30, db=db, current_user=current_user)
    
    # Funil (se disponível)
    funnel = None
    if plan_limits["funnel_reports"]:
        try:
            funnel = await get_funnel_report(db=db, current_user=current_user)
        except HTTPException:
            pass
    
    # Comparação de campanhas (se disponível)
    campaign_comparison = None
    if plan_limits["campaign_comparison"]:
        try:
            campaign_comparison = await get_campaign_comparison(db=db, current_user=current_user)
        except HTTPException:
            pass
    
    return FullDashboardResponse(
        overview=overview,
        usage_limits=usage_limits,
        features=features,
        recent_activities=recent_activities,
        top_agents=activities_data["top_agents"],
        funnel=funnel,
        campaign_comparison=campaign_comparison,
        timeline=timeline,
    )
