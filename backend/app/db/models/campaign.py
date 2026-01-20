"""
Modelo de Campanha de Prospecção.
"""

import enum
from sqlalchemy import Column, String, Enum, Integer, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.db.base import BaseModel


class CampaignStatus(str, enum.Enum):
    """Status possíveis de uma campanha."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CampaignChannel(str, enum.Enum):
    """Canais de comunicação/envio de mensagens."""
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class ProspectingSource(str, enum.Enum):
    """Fontes de prospecção/mineração de leads."""
    GOOGLE = "google"
    GOOGLE_MAPS = "google_maps"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    ALL = "all"


# Tabela associativa para relação N:N entre Campaign e ServicePlan
campaign_plans = Table(
    "campaign_plans",
    Base.metadata,
    Column("campaign_id", UUID(as_uuid=True), ForeignKey("campaigns.id"), primary_key=True),
    Column("plan_id", UUID(as_uuid=True), ForeignKey("service_plans.id"), primary_key=True),
)


class Campaign(BaseModel):
    """
    Modelo de campanha de prospecção.
    
    Attributes:
        user_id: ID do usuário proprietário
        agent_id: ID do agente LLM associado
        name: Nome da campanha
        description: Descrição da campanha
        status: Status atual (draft, active, paused, completed)
        
        # Configurações de Prospecção
        prospecting_source: Fonte de prospecção (google, google_maps, instagram, all)
        niche: Nicho de mercado (ex: "restaurantes", "clínicas odontológicas")
        location: Localização alvo (ex: "São Paulo, SP")
        hashtags: Lista de hashtags para busca no Instagram
        keywords: Palavras-chave adicionais para busca
        
        # Configurações de Comunicação
        channel: Canal de comunicação (instagram, whatsapp, email)
        rate_limit: Limite de mensagens por hora
        
        # Configurações avançadas
        search_config: Configurações adicionais de busca em JSON
    """
    
    __tablename__ = "campaigns"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    
    # Configurações de Prospecção
    prospecting_source = Column(
        Enum(ProspectingSource), 
        default=ProspectingSource.GOOGLE_MAPS, 
        nullable=False
    )
    niche = Column(String(255), nullable=True)  # Ex: "restaurantes", "academias"
    location = Column(String(255), nullable=True)  # Ex: "São Paulo, SP"
    hashtags = Column(ARRAY(String), default=list, nullable=True)  # Para Instagram
    keywords = Column(ARRAY(String), default=list, nullable=True)  # Palavras-chave adicionais
    
    # Configurações de Comunicação
    channel = Column(Enum(CampaignChannel), default=CampaignChannel.WHATSAPP, nullable=False)
    rate_limit = Column(Integer, default=20, nullable=False)  # mensagens por hora
    
    # Configurações avançadas em JSON
    search_config = Column(JSONB, default=dict, nullable=False)
    
    # Relacionamentos
    user = relationship("User", back_populates="campaigns")
    agent = relationship("Agent", back_populates="campaigns")
    plans = relationship(
        "ServicePlan",
        secondary=campaign_plans,
        back_populates="campaigns",
        lazy="dynamic"
    )
    prospects = relationship("Prospect", back_populates="campaign", lazy="dynamic")
    messages = relationship("Message", back_populates="campaign", lazy="dynamic")
    metrics = relationship("CampaignMetrics", back_populates="campaign", lazy="dynamic")
    
    def get_search_query(self) -> str:
        """Gera a query de busca baseado no nicho e keywords."""
        parts = []
        if self.niche:
            parts.append(self.niche)
        if self.keywords:
            parts.extend(self.keywords)
        return " ".join(parts) if parts else ""
    
    def __repr__(self):
        return f"<Campaign {self.name}>"
