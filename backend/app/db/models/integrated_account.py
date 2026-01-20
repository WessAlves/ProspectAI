"""
Modelo de Conta Integrada (Instagram, WhatsApp).
"""

import enum
from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class IntegrationPlatform(str, enum.Enum):
    """Plataformas de integração."""
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"


class AccountStatus(str, enum.Enum):
    """Status da conta integrada."""
    ACTIVE = "active"
    EXPIRED = "expired"
    BLOCKED = "blocked"


class IntegratedAccount(BaseModel):
    """
    Modelo de conta integrada para envio de mensagens.
    
    Attributes:
        user_id: ID do usuário proprietário
        platform: Plataforma (instagram, whatsapp)
        account_identifier: Identificador da conta
        credentials: Credenciais encriptadas
        status: Status da conta
    """
    
    __tablename__ = "integrated_accounts"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(Enum(IntegrationPlatform), nullable=False)
    account_identifier = Column(String(255), nullable=False)
    credentials = Column(Text, nullable=False)  # Encriptado com AES-256
    status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)
    
    # Relacionamentos
    user = relationship("User", back_populates="integrated_accounts")
    
    def __repr__(self):
        return f"<IntegratedAccount {self.platform.value} - {self.account_identifier}>"
