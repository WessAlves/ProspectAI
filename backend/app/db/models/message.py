"""
Modelo de Mensagem.
"""

import enum
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class MessageDirection(str, enum.Enum):
    """Direção da mensagem."""
    OUTBOUND = "outbound"  # Enviada
    INBOUND = "inbound"    # Recebida


class MessageStatus(str, enum.Enum):
    """Status de entrega da mensagem."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class Message(BaseModel):
    """
    Modelo de mensagem enviada/recebida.
    
    Attributes:
        prospect_id: ID do prospect
        campaign_id: ID da campanha
        content: Conteúdo da mensagem
        direction: Direção (outbound/inbound)
        status: Status de entrega
        sent_at: Timestamp de envio
        delivered_at: Timestamp de entrega
        read_at: Timestamp de leitura
        extra_data: Dados adicionais
    """
    
    __tablename__ = "messages"
    
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("prospects.id"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    direction = Column(Enum(MessageDirection), nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    extra_data = Column(JSONB, default=dict, nullable=False)
    
    # Relacionamentos
    prospect = relationship("Prospect", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} - {self.direction.value}>"
