"""
Schemas Pydantic para Dashboard e métricas.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class DashboardOverview(BaseModel):
    """Visão geral do dashboard."""
    total_campaigns: int
    active_campaigns: int
    total_leads: int
    total_messages_sent: int
    total_replies: int
    total_conversions: int
    conversion_rate: float
    reply_rate: float


class CampaignMetricsResponse(BaseModel):
    """Métricas de uma campanha."""
    campaign_id: UUID
    date: date
    leads_found: int
    messages_sent: int
    messages_delivered: int
    messages_read: int
    replies_received: int
    conversions: int
    
    class Config:
        from_attributes = True


class FunnelMetrics(BaseModel):
    """Métricas do funil de conversão."""
    leads_found: int
    messages_sent: int
    messages_delivered: int
    messages_read: int
    replies_received: int
    conversions: int
    
    # Taxas
    delivery_rate: float
    read_rate: float
    reply_rate: float
    conversion_rate: float


class TimelineEntry(BaseModel):
    """Entrada da timeline de atividades."""
    timestamp: datetime
    event_type: str
    description: str
    campaign_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None


class CampaignComparison(BaseModel):
    """Comparação entre campanhas."""
    campaign_id: UUID
    campaign_name: str
    total_leads: int
    total_messages: int
    reply_rate: float
    conversion_rate: float


class DateRangeMetrics(BaseModel):
    """Métricas por período."""
    date: date
    leads_found: int
    messages_sent: int
    replies_received: int
    conversions: int


# ============================================
# Novos schemas para Dashboard por Plano
# ============================================

class UsageLimits(BaseModel):
    """Limites de uso do plano atual."""
    plan_tier: str
    leads_limit: int  # -1 = ilimitado
    leads_used: int
    leads_remaining: int
    agents_limit: int
    agents_used: int
    agents_remaining: int
    campaigns_limit: int
    campaigns_used: int
    campaigns_remaining: int
    # Features disponíveis
    whatsapp_enabled: bool
    whatsapp_official_api: bool
    advanced_filters: bool
    funnel_reports: bool
    campaign_comparison: bool
    crm_integration: bool
    priority_support: bool
    sso: bool


class InteractionHistoryItem(BaseModel):
    """Item do histórico de interações (CRM básico)."""
    id: UUID
    lead_id: UUID
    lead_name: str
    lead_source: str  # instagram, google_maps, etc
    campaign_id: UUID
    campaign_name: str
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    status: str  # pending, contacted, replied, converted, rejected
    total_messages: int
    reply_count: int


class InteractionHistoryResponse(BaseModel):
    """Resposta do histórico de interações."""
    items: List[InteractionHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class FunnelStage(BaseModel):
    """Estágio do funil de conversão."""
    name: str
    count: int
    percentage: float
    color: str


class FunnelReportResponse(BaseModel):
    """Relatório completo do funil de conversão."""
    campaign_id: Optional[UUID] = None
    campaign_name: Optional[str] = None
    stages: List[FunnelStage]
    total_leads: int
    total_conversions: int
    overall_conversion_rate: float
    # Métricas detalhadas
    avg_time_to_reply: Optional[float] = None  # em horas
    avg_messages_until_conversion: Optional[float] = None
    best_performing_day: Optional[str] = None
    best_performing_hour: Optional[int] = None


class CampaignComparisonItem(BaseModel):
    """Item de comparação de campanhas."""
    campaign_id: UUID
    campaign_name: str
    status: str
    created_at: datetime
    # Métricas
    total_leads: int
    messages_sent: int
    messages_delivered: int
    messages_read: int
    replies_received: int
    conversions: int
    # Taxas
    delivery_rate: float
    read_rate: float
    reply_rate: float
    conversion_rate: float
    # Performance score (0-100)
    performance_score: float


class CampaignComparisonResponse(BaseModel):
    """Resposta da comparação de campanhas."""
    campaigns: List[CampaignComparisonItem]
    best_performer_id: Optional[UUID] = None
    worst_performer_id: Optional[UUID] = None
    # Médias gerais
    avg_reply_rate: float
    avg_conversion_rate: float


class DashboardFeatures(BaseModel):
    """Features disponíveis do dashboard baseado no plano."""
    basic_kpis: bool = True  # Sempre disponível
    interaction_history: bool = True  # Sempre disponível (CRM básico)
    funnel_reports: bool
    campaign_comparison: bool
    advanced_filters: bool
    crm_integration: bool


class FullDashboardResponse(BaseModel):
    """Resposta completa do dashboard com todas as seções."""
    # Métricas básicas (todos os planos)
    overview: DashboardOverview
    usage_limits: UsageLimits
    features: DashboardFeatures
    # Atividades recentes (todos os planos)
    recent_activities: List[TimelineEntry]
    top_agents: List[Dict[str, Any]]
    # Funil (Starter+)
    funnel: Optional[FunnelReportResponse] = None
    # Comparação (Pro+)
    campaign_comparison: Optional[CampaignComparisonResponse] = None
    # Timeline de métricas (todos os planos)
    timeline: List[DateRangeMetrics]
