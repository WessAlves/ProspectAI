"""
Modelo de Prospect (lead encontrado).
"""

import enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class ProspectPlatform(str, enum.Enum):
    """Plataforma de origem do prospect."""
    INSTAGRAM = "instagram"
    GOOGLE = "google"
    GOOGLE_MAPS = "google_maps"
    MANUAL = "manual"
    IMPORT = "import"


class ProspectStatus(str, enum.Enum):
    """Status do prospect no funil."""
    FOUND = "found"
    CONTACTED = "contacted"
    REPLIED = "replied"
    CONVERTED = "converted"
    REJECTED = "rejected"
    IGNORED = "ignored"


class Prospect(BaseModel):
    """
    Modelo de prospect/lead encontrado na prospecção.
    
    Attributes:
        campaign_id: ID da campanha associada
        name: Nome do prospect/empresa
        username: Username (Instagram) ou identificador
        platform: Plataforma de origem
        profile_url: URL do perfil
        followers_count: Número de seguidores
        has_website: Se possui website
        website_url: URL do website
        last_post_date: Data do último post
        extra_data: Dados adicionais em JSON
        status: Status no funil
    """
    
    __tablename__ = "prospects"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=False)
    platform = Column(
        Enum(ProspectPlatform, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    profile_url = Column(String(500), nullable=True)
    followers_count = Column(Integer, nullable=True)
    has_website = Column(Boolean, default=False, nullable=False)
    website_url = Column(String(500), nullable=True)
    last_post_date = Column(DateTime, nullable=True)
    extra_data = Column(JSONB, default=dict, nullable=False)  # Renamed from metadata
    status = Column(
        Enum(ProspectStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProspectStatus.FOUND,
        nullable=False
    )
    score = Column(Integer, default=0, nullable=False)  # Score de qualificação
    
    # Campos adicionais para leads manuais
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    
    # Relacionamentos
    campaign = relationship("Campaign", back_populates="prospects")
    messages = relationship("Message", back_populates="prospect", lazy="dynamic")
    
    def __repr__(self):
        return f"<Prospect {self.username}>"
