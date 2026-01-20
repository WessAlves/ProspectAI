"""
Modelo de Plano de Serviço.
"""

from sqlalchemy import Column, String, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class ServicePlan(BaseModel):
    """
    Modelo de plano/serviço oferecido pelo usuário.
    
    Attributes:
        user_id: ID do usuário proprietário
        name: Nome do plano/serviço
        description: Descrição detalhada
        price: Preço do serviço
        features: Lista de features em JSON
    """
    
    __tablename__ = "service_plans"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    features = Column(JSONB, default=list, nullable=False)
    
    # Relacionamentos
    user = relationship("User", back_populates="service_plans")
    campaigns = relationship(
        "Campaign",
        secondary="campaign_plans",
        back_populates="plans",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<ServicePlan {self.name}>"
