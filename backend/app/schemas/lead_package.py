from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from decimal import Decimal
from uuid import UUID


class PackageTypeEnum(str, Enum):
    """Tipos de pacotes disponíveis"""
    LEADS_500 = "leads_500"
    LEADS_1000 = "leads_1000"
    LEADS_1500 = "leads_1500"


class PaymentStatusEnum(str, Enum):
    """Status do pagamento"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


# Configuração dos pacotes (espelhado do model)
PACKAGE_CONFIG = {
    PackageTypeEnum.LEADS_500: {"leads": 500, "price": 50.00, "display_name": "Pacote 500 Leads"},
    PackageTypeEnum.LEADS_1000: {"leads": 1000, "price": 70.00, "display_name": "Pacote 1000 Leads"},
    PackageTypeEnum.LEADS_1500: {"leads": 1500, "price": 100.00, "display_name": "Pacote 1500 Leads"},
}


class PackageInfo(BaseModel):
    """Informações de um pacote disponível para compra"""
    package_type: PackageTypeEnum
    leads: int
    price: float
    display_name: str
    price_per_lead: float = Field(description="Preço por lead")


class AvailablePackagesResponse(BaseModel):
    """Lista de pacotes disponíveis"""
    packages: List[PackageInfo]


class PurchasePackageRequest(BaseModel):
    """Request para comprar um pacote"""
    package_type: PackageTypeEnum
    payment_method: Optional[str] = Field(None, description="Método de pagamento (pix, card, boleto)")


class LeadPackageResponse(BaseModel):
    """Resposta com dados de um pacote comprado"""
    id: UUID
    user_id: UUID
    package_type: PackageTypeEnum
    leads_purchased: int
    leads_used: int
    leads_remaining: int = Field(description="Leads restantes do pacote")
    price_paid: float
    payment_status: PaymentStatusEnum
    payment_id: Optional[str]
    payment_method: Optional[str]
    purchase_month: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeadUsageSummary(BaseModel):
    """Resumo do uso de leads do usuário"""
    # Limites do plano
    plan_name: str
    plan_monthly_limit: int
    
    # Uso atual
    leads_used_this_month: int
    leads_from_plan: int = Field(description="Leads disponíveis do plano mensal")
    leads_from_packages: int = Field(description="Leads adicionais de pacotes comprados")
    
    # Totais
    total_available: int = Field(description="Total de leads disponíveis (plano + pacotes)")
    total_remaining: int = Field(description="Leads restantes para usar")
    usage_percentage: float = Field(description="Porcentagem de uso (0-100)")
    
    # Status
    is_limit_reached: bool = Field(description="Se atingiu o limite")
    campaigns_paused: bool = Field(description="Se as campanhas estão pausadas por limite")
    
    # Pacotes ativos
    active_packages: List[LeadPackageResponse] = Field(default_factory=list)


class LeadLimitReachedResponse(BaseModel):
    """Resposta quando limite de leads é atingido"""
    message: str = "Limite de leads atingido"
    usage: LeadUsageSummary
    available_packages: List[PackageInfo]
    upgrade_options: List[dict] = Field(description="Opções de upgrade de plano")
