"""
Schemas Pydantic para Campaign.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.db.models.campaign import CampaignStatus, CampaignChannel, ProspectingSource


class SearchConfig(BaseModel):
    """Configurações avançadas de busca da campanha."""
    min_followers: Optional[int] = Field(None, ge=0, description="Mínimo de seguidores (Instagram)")
    max_followers: Optional[int] = Field(None, ge=0, description="Máximo de seguidores (Instagram)")
    has_website: Optional[bool] = Field(None, description="Filtrar por presença de website")
    min_posts: Optional[int] = Field(None, ge=0, description="Mínimo de posts (Instagram)")
    last_active_days: Optional[int] = Field(None, ge=1, description="Dias desde última atividade")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Avaliação mínima (Google Maps)")
    business_types: List[str] = Field(default_factory=list, description="Tipos de negócio")


class CampaignBase(BaseModel):
    """Schema base de campanha."""
    name: str = Field(..., min_length=1, max_length=255, description="Nome da campanha")
    description: Optional[str] = Field(None, max_length=1000, description="Descrição da campanha")
    
    # Configurações de Prospecção
    prospecting_source: ProspectingSource = Field(
        default=ProspectingSource.GOOGLE_MAPS,
        description="Fonte de prospecção (google, google_maps, instagram, all)"
    )
    niche: Optional[str] = Field(
        None, 
        max_length=255,
        description="Nicho de mercado (ex: restaurantes, clínicas)"
    )
    location: Optional[str] = Field(
        None,
        max_length=255, 
        description="Localização alvo (ex: São Paulo, SP)"
    )
    hashtags: List[str] = Field(
        default_factory=list,
        description="Hashtags para busca no Instagram (sem #)"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Palavras-chave adicionais para busca"
    )
    
    # Configurações de Comunicação
    channel: CampaignChannel = Field(
        default=CampaignChannel.WHATSAPP,
        description="Canal de comunicação (instagram, whatsapp, email)"
    )
    rate_limit: int = Field(
        default=20, 
        ge=1, 
        le=100,
        description="Limite de mensagens por hora"
    )
    
    # Configurações avançadas
    search_config: SearchConfig = Field(
        default_factory=SearchConfig,
        description="Configurações avançadas de busca"
    )


class CampaignCreate(CampaignBase):
    """Schema para criação de campanha."""
    agent_id: Optional[UUID] = Field(None, description="ID do agente LLM")
    plan_ids: List[UUID] = Field(default_factory=list, description="IDs dos planos de serviço")


class CampaignUpdate(BaseModel):
    """Schema para atualização de campanha."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    agent_id: Optional[UUID] = None
    plan_ids: Optional[List[UUID]] = None
    
    # Configurações de Prospecção
    prospecting_source: Optional[ProspectingSource] = None
    niche: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    hashtags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    
    # Configurações de Comunicação
    channel: Optional[CampaignChannel] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=100)
    
    # Configurações avançadas
    search_config: Optional[SearchConfig] = None


class CampaignResponse(BaseModel):
    """Schema de resposta de campanha."""
    id: UUID
    user_id: UUID
    agent_id: Optional[UUID]
    name: str
    description: Optional[str]
    status: CampaignStatus
    
    # Prospecção
    prospecting_source: ProspectingSource
    niche: Optional[str]
    location: Optional[str]
    hashtags: Optional[List[str]]
    keywords: Optional[List[str]]
    
    # Comunicação
    channel: CampaignChannel
    rate_limit: int
    search_config: Dict[str, Any]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CampaignListItem(CampaignResponse):
    """Schema para listagem de campanhas com contadores."""
    prospects_count: int = Field(default=0, description="Número de prospects/leads")
    messages_count: int = Field(default=0, description="Número de mensagens enviadas")
    responses_count: int = Field(default=0, description="Número de respostas recebidas")
    agent_name: Optional[str] = Field(default=None, description="Nome do agente")
    
    class Config:
        from_attributes = True


class CampaignDetail(CampaignResponse):
    """Schema detalhado de campanha com relacionamentos."""
    plans: List["ServicePlanResponse"] = Field(default_factory=list)
    agent: Optional["AgentResponse"] = None
    prospects_count: int = Field(default=0, description="Número de prospects")
    messages_count: int = Field(default=0, description="Número de mensagens enviadas")
    
    class Config:
        from_attributes = True


class CampaignStartScraping(BaseModel):
    """Schema para iniciar scraping de uma campanha."""
    limit: int = Field(default=50, ge=10, le=500, description="Limite de prospects por fonte")
    sources_override: Optional[List[str]] = Field(
        None,
        description="Sobrescrever fontes configuradas (google, google_maps, instagram)"
    )


# Import circular - resolver após
from app.schemas.plan import ServicePlanResponse
from app.schemas.agent import AgentResponse
CampaignDetail.model_rebuild()
