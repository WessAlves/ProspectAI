"""
Modelo de Métricas de Campanha.
"""

from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class CampaignMetrics(BaseModel):
    """
    Modelo de métricas agregadas de campanha.
    
    Attributes:
        campaign_id: ID da campanha
        date: Data das métricas
        prospects_found: Prospects encontrados
        messages_sent: Mensagens enviadas
        messages_delivered: Mensagens entregues
        messages_read: Mensagens lidas
        replies_received: Respostas recebidas
        conversions: Conversões
    """
    
    __tablename__ = "campaign_metrics"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    prospects_found = Column(Integer, default=0, nullable=False)
    messages_sent = Column(Integer, default=0, nullable=False)
    messages_delivered = Column(Integer, default=0, nullable=False)
    messages_read = Column(Integer, default=0, nullable=False)
    replies_received = Column(Integer, default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    
    # Relacionamentos
    campaign = relationship("Campaign", back_populates="metrics")
    
    def __repr__(self):
        return f"<CampaignMetrics {self.campaign_id} - {self.date}>"
