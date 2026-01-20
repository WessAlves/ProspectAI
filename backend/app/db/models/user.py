"""
Modelo de Usuário.
"""

import enum
from sqlalchemy import Column, String, Enum, Boolean, Integer, Date, Text
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class PersonType(str, enum.Enum):
    """Tipo de pessoa."""
    INDIVIDUAL = "individual"  # Pessoa Física
    COMPANY = "company"  # Pessoa Jurídica


class PlanTier(str, enum.Enum):
    """Níveis de plano do usuário."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    SCALE = "scale"


# Configurações de limites por plano
PLAN_LIMITS = {
    PlanTier.FREE: {
        "leads_per_month": 50,
        "agents": 1,
        "campaigns": 1,
        "whatsapp_enabled": False,
        "whatsapp_official_api": False,
        "advanced_filters": False,
        "funnel_reports": False,
        "campaign_comparison": False,
        "crm_integration": False,
        "priority_support": False,
        "sso": False,
    },
    PlanTier.STARTER: {
        "leads_per_month": 500,
        "agents": 1,
        "campaigns": 3,
        "whatsapp_enabled": True,
        "whatsapp_official_api": False,
        "advanced_filters": True,
        "funnel_reports": True,
        "campaign_comparison": False,
        "crm_integration": False,
        "priority_support": False,
        "sso": False,
    },
    PlanTier.PRO: {
        "leads_per_month": 2000,
        "agents": 5,
        "campaigns": 10,
        "whatsapp_enabled": True,
        "whatsapp_official_api": True,
        "advanced_filters": True,
        "funnel_reports": True,
        "campaign_comparison": True,
        "crm_integration": True,
        "priority_support": False,
        "sso": False,
    },
    PlanTier.SCALE: {
        "leads_per_month": -1,  # -1 = ilimitado
        "agents": -1,  # -1 = ilimitado
        "campaigns": -1,  # -1 = ilimitado
        "whatsapp_enabled": True,
        "whatsapp_official_api": True,
        "advanced_filters": True,
        "funnel_reports": True,
        "campaign_comparison": True,
        "crm_integration": True,
        "priority_support": True,
        "sso": True,
    },
}


class UserRole(str, enum.Enum):
    """Perfis de usuário."""
    ADMIN = "admin"
    COMMON = "common"


class User(BaseModel):
    """
    Modelo de usuário do sistema.
    
    Attributes:
        email: Email único do usuário
        password_hash: Hash da senha (bcrypt)
        full_name: Nome completo do usuário
        role: Perfil do usuário (admin, common)
        plan_tier: Nível do plano (free, starter, pro, scale)
        is_active: Se o usuário está ativo
        is_superuser: Se é um superusuário (deprecated, use role)
    """
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.COMMON, nullable=False)
    plan_tier = Column(Enum(PlanTier, values_callable=lambda x: [e.value for e in x]), default=PlanTier.FREE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Perfil completo
    profile_completed = Column(Boolean, default=False, nullable=False)
    person_type = Column(Enum(PersonType, values_callable=lambda x: [e.value for e in x]), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Campos para Pessoa Física
    cpf = Column(String(14), unique=True, nullable=True)  # 000.000.000-00
    birth_date = Column(Date, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Campos para Pessoa Jurídica
    cnpj = Column(String(18), unique=True, nullable=True)  # 00.000.000/0000-00
    company_name = Column(String(255), nullable=True)  # Razão Social
    trade_name = Column(String(255), nullable=True)  # Nome Fantasia
    state_registration = Column(String(50), nullable=True)  # Inscrição Estadual
    municipal_registration = Column(String(50), nullable=True)  # Inscrição Municipal
    
    # Endereço
    address_street = Column(String(255), nullable=True)
    address_number = Column(String(20), nullable=True)
    address_complement = Column(String(100), nullable=True)
    address_neighborhood = Column(String(100), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_state = Column(String(2), nullable=True)
    address_zip_code = Column(String(10), nullable=True)  # 00000-000
    
    # Dados de pagamento (tokens criptografados - nunca armazenar número do cartão)
    payment_method_id = Column(String(255), nullable=True)  # ID do método no gateway (Stripe, etc)
    card_last_four = Column(String(4), nullable=True)  # Últimos 4 dígitos
    card_brand = Column(String(20), nullable=True)  # visa, mastercard, etc
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    billing_name = Column(String(255), nullable=True)  # Nome no cartão
    
    @property
    def is_admin(self) -> bool:
        """Verifica se o usuário é admin."""
        return self.role == UserRole.ADMIN or self.is_superuser
    
    @property
    def plan_limits(self) -> dict:
        """Retorna os limites do plano do usuário."""
        return PLAN_LIMITS.get(self.plan_tier, PLAN_LIMITS[PlanTier.FREE])
    
    def can_create_agent(self, current_agent_count: int) -> bool:
        """Verifica se o usuário pode criar mais agentes."""
        limit = self.plan_limits["agents"]
        return limit == -1 or current_agent_count < limit
    
    def can_create_campaign(self, current_campaign_count: int) -> bool:
        """Verifica se o usuário pode criar mais campanhas."""
        limit = self.plan_limits["campaigns"]
        return limit == -1 or current_campaign_count < limit
    
    def can_prospect(self, current_month_prospects: int) -> bool:
        """Verifica se o usuário pode prospectar mais neste mês."""
        limit = self.plan_limits["prospects_per_month"]
        return limit == -1 or current_month_prospects < limit
    
    def has_feature(self, feature: str) -> bool:
        """Verifica se o usuário tem acesso a uma feature."""
        return self.plan_limits.get(feature, False)
    
    # Relacionamentos
    agents = relationship("Agent", back_populates="user", lazy="dynamic")
    service_plans = relationship("ServicePlan", back_populates="user", lazy="dynamic")
    campaigns = relationship("Campaign", back_populates="user", lazy="dynamic")
    integrated_accounts = relationship("IntegratedAccount", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User {self.email}>"
