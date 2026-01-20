"""
Modelo de Pacotes de Leads Adicionais.
"""

import enum
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import BaseModel


class PackageType(str, enum.Enum):
    """Tipos de pacotes disponíveis."""
    LEADS_500 = "leads_500"
    LEADS_1000 = "leads_1000"
    LEADS_1500 = "leads_1500"


class PaymentStatus(str, enum.Enum):
    """Status do pagamento."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


# Configuração dos pacotes
PACKAGE_CONFIG = {
    PackageType.LEADS_500: {
        "name": "Pacote de 500 Leads Adicionais",
        "leads": 500,
        "price": 50.00,
        "description": "500 leads adicionais para prospecção",
    },
    PackageType.LEADS_1000: {
        "name": "Pacote de 1000 Leads Adicionais",
        "leads": 1000,
        "price": 70.00,
        "description": "1000 leads adicionais para prospecção",
    },
    PackageType.LEADS_1500: {
        "name": "Pacote de 1500 Leads Adicionais",
        "leads": 1500,
        "price": 100.00,
        "description": "1500 leads adicionais para prospecção",
    },
}


class LeadPackage(BaseModel):
    """
    Modelo de pacote de leads comprado pelo usuário.
    
    Attributes:
        user_id: ID do usuário que comprou
        package_type: Tipo do pacote
        leads_purchased: Quantidade de leads comprados
        leads_used: Quantidade de leads já usados do pacote
        price_paid: Valor pago (em BRL)
        payment_status: Status do pagamento
        payment_id: ID da transação no gateway de pagamento
        valid_until: Data de validade do pacote (opcional, pode expirar)
        purchase_month: Mês/ano de referência (YYYY-MM)
    """
    
    __tablename__ = "lead_packages"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    package_type = Column(
        Enum(PackageType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    leads_purchased = Column(Integer, nullable=False)
    leads_used = Column(Integer, default=0, nullable=False)
    price_paid = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(
        Enum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    payment_id = Column(String(255), nullable=True)  # ID no gateway (Stripe, etc)
    payment_method = Column(String(50), nullable=True)  # card, pix, boleto
    valid_until = Column(DateTime, nullable=True)  # NULL = não expira
    purchase_month = Column(String(7), nullable=False)  # YYYY-MM
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relacionamentos
    user = relationship("User", backref="lead_packages")
    
    @property
    def leads_remaining(self) -> int:
        """Retorna a quantidade de leads restantes no pacote."""
        return max(0, self.leads_purchased - self.leads_used)
    
    @property
    def is_exhausted(self) -> bool:
        """Verifica se o pacote foi totalmente usado."""
        return self.leads_used >= self.leads_purchased
    
    @property
    def is_valid(self) -> bool:
        """Verifica se o pacote ainda é válido."""
        if not self.is_active:
            return False
        if self.payment_status != PaymentStatus.PAID:
            return False
        if self.valid_until and datetime.utcnow() > self.valid_until:
            return False
        return not self.is_exhausted
    
    def use_leads(self, amount: int) -> int:
        """
        Usa leads do pacote.
        
        Returns:
            Quantidade efetivamente usada (pode ser menor se não houver suficiente)
        """
        available = self.leads_remaining
        to_use = min(amount, available)
        self.leads_used += to_use
        return to_use
    
    def __repr__(self):
        return f"<LeadPackage {self.package_type.value} - {self.leads_remaining}/{self.leads_purchased}>"
