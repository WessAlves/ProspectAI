"""
Schemas Pydantic para User.
"""

import re
from datetime import datetime, date
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db.models.user import PlanTier, UserRole, PLAN_LIMITS, PersonType


def validate_cpf(cpf: str) -> bool:
    """Valida um CPF brasileiro."""
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula o primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    # Calcula o segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf[10]) == digito2


def validate_cnpj(cnpj: str) -> bool:
    """Valida um CNPJ brasileiro."""
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Cálculo do primeiro dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != digito1:
        return False
    
    # Cálculo do segundo dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cnpj[13]) == digito2


def format_cpf(cpf: str) -> str:
    """Formata um CPF para o padrão 000.000.000-00."""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf


def format_cnpj(cnpj: str) -> str:
    """Formata um CNPJ para o padrão 00.000.000/0000-00."""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj


class UserBase(BaseModel):
    """Schema base de usuário."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    """Schema para criação de usuário."""
    password: str = Field(..., min_length=6, max_length=100)
    plan_id: Optional[str] = Field(default="free", description="ID do plano: free, starter, pro, scale")


class UserUpdate(BaseModel):
    """Schema para atualização de usuário."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=100)


# === Schemas de Endereço ===

class AddressSchema(BaseModel):
    """Schema para endereço."""
    street: Optional[str] = Field(None, max_length=255, alias="address_street")
    number: Optional[str] = Field(None, max_length=20, alias="address_number")
    complement: Optional[str] = Field(None, max_length=100, alias="address_complement")
    neighborhood: Optional[str] = Field(None, max_length=100, alias="address_neighborhood")
    city: Optional[str] = Field(None, max_length=100, alias="address_city")
    state: Optional[str] = Field(None, min_length=2, max_length=2, alias="address_state")
    zip_code: Optional[str] = Field(None, max_length=10, alias="address_zip_code")
    
    @field_validator('zip_code')
    @classmethod
    def validate_zip_code(cls, v):
        if v:
            # Remove caracteres não numéricos
            cleaned = re.sub(r'[^0-9]', '', v)
            if len(cleaned) != 8:
                raise ValueError('CEP deve ter 8 dígitos')
            # Formata como 00000-000
            return f"{cleaned[:5]}-{cleaned[5:]}"
        return v
    
    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        if v:
            valid_states = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
                          'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
                          'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
            if v.upper() not in valid_states:
                raise ValueError('Estado inválido')
            return v.upper()
        return v


# === Schemas de Perfil - Pessoa Física ===

class IndividualProfileUpdate(BaseModel):
    """Schema para atualização de perfil de pessoa física."""
    person_type: Literal["individual"] = "individual"
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    cpf: str = Field(..., min_length=11, max_length=14)
    birth_date: date
    phone: Optional[str] = Field(None, max_length=20)
    
    # Endereço
    address_street: Optional[str] = Field(None, max_length=255)
    address_number: Optional[str] = Field(None, max_length=20)
    address_complement: Optional[str] = Field(None, max_length=100)
    address_neighborhood: Optional[str] = Field(None, max_length=100)
    address_city: Optional[str] = Field(None, max_length=100)
    address_state: Optional[str] = Field(None, min_length=2, max_length=2)
    address_zip_code: Optional[str] = Field(None, max_length=10)
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf_field(cls, v):
        if not validate_cpf(v):
            raise ValueError('CPF inválido')
        return format_cpf(v)
    
    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v):
        from datetime import date as date_type
        today = date_type.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Usuário deve ter pelo menos 18 anos')
        if age > 120:
            raise ValueError('Data de nascimento inválida')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v:
            # Remove caracteres não numéricos
            cleaned = re.sub(r'[^0-9]', '', v)
            if len(cleaned) < 10 or len(cleaned) > 11:
                raise ValueError('Telefone deve ter 10 ou 11 dígitos')
            # Formata como (00) 00000-0000
            if len(cleaned) == 11:
                return f"({cleaned[:2]}) {cleaned[2:7]}-{cleaned[7:]}"
            return f"({cleaned[:2]}) {cleaned[2:6]}-{cleaned[6:]}"
        return v


# === Schemas de Perfil - Pessoa Jurídica ===

class CompanyProfileUpdate(BaseModel):
    """Schema para atualização de perfil de pessoa jurídica."""
    person_type: Literal["company"] = "company"
    cnpj: str = Field(..., min_length=14, max_length=18)
    company_name: str = Field(..., min_length=2, max_length=255)  # Razão Social
    trade_name: Optional[str] = Field(None, max_length=255)  # Nome Fantasia
    state_registration: Optional[str] = Field(None, max_length=50)
    municipal_registration: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Dados do responsável
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    
    # Endereço
    address_street: Optional[str] = Field(None, max_length=255)
    address_number: Optional[str] = Field(None, max_length=20)
    address_complement: Optional[str] = Field(None, max_length=100)
    address_neighborhood: Optional[str] = Field(None, max_length=100)
    address_city: Optional[str] = Field(None, max_length=100)
    address_state: Optional[str] = Field(None, min_length=2, max_length=2)
    address_zip_code: Optional[str] = Field(None, max_length=10)
    
    @field_validator('cnpj')
    @classmethod
    def validate_cnpj_field(cls, v):
        if not validate_cnpj(v):
            raise ValueError('CNPJ inválido')
        return format_cnpj(v)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v:
            cleaned = re.sub(r'[^0-9]', '', v)
            if len(cleaned) < 10 or len(cleaned) > 11:
                raise ValueError('Telefone deve ter 10 ou 11 dígitos')
            if len(cleaned) == 11:
                return f"({cleaned[:2]}) {cleaned[2:7]}-{cleaned[7:]}"
            return f"({cleaned[:2]}) {cleaned[2:6]}-{cleaned[6:]}"
        return v


# === Schema de Alteração de Senha ===

class PasswordChange(BaseModel):
    """Schema para alteração de senha."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('As senhas não coincidem')
        return v


# === Schema de Cartão de Crédito ===

class PaymentMethodCreate(BaseModel):
    """Schema para adicionar método de pagamento."""
    card_number: str = Field(..., min_length=13, max_length=19)
    card_holder_name: str = Field(..., min_length=2, max_length=255)
    exp_month: int = Field(..., ge=1, le=12)
    exp_year: int = Field(..., ge=2024, le=2100)
    cvv: str = Field(..., min_length=3, max_length=4)
    
    # Endereço de cobrança (opcional, usa o do perfil se não informado)
    billing_address_zip_code: Optional[str] = None
    
    @field_validator('card_number')
    @classmethod
    def validate_card_number(cls, v):
        # Remove espaços e traços
        cleaned = re.sub(r'[\s-]', '', v)
        if not cleaned.isdigit():
            raise ValueError('Número do cartão deve conter apenas dígitos')
        if len(cleaned) < 13 or len(cleaned) > 19:
            raise ValueError('Número do cartão inválido')
        # Validação Luhn (algoritmo de verificação de cartão)
        digits = [int(d) for d in cleaned]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))
        if checksum % 10 != 0:
            raise ValueError('Número do cartão inválido')
        return cleaned
    
    @field_validator('cvv')
    @classmethod
    def validate_cvv(cls, v):
        if not v.isdigit():
            raise ValueError('CVV deve conter apenas dígitos')
        return v


class PaymentMethodResponse(BaseModel):
    """Schema de resposta de método de pagamento."""
    has_payment_method: bool
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    billing_name: Optional[str] = None


# === Schema de Perfil Completo ===

class ProfileResponse(BaseModel):
    """Schema de resposta do perfil completo do usuário."""
    id: UUID
    email: str
    full_name: str
    profile_completed: bool
    person_type: Optional[PersonType] = None
    phone: Optional[str] = None
    
    # Pessoa Física
    cpf: Optional[str] = None
    birth_date: Optional[date] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Pessoa Jurídica
    cnpj: Optional[str] = None
    company_name: Optional[str] = None
    trade_name: Optional[str] = None
    state_registration: Optional[str] = None
    municipal_registration: Optional[str] = None
    
    # Endereço
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip_code: Optional[str] = None
    
    # Pagamento (apenas metadados seguros)
    has_payment_method: bool = False
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlanLimitsResponse(BaseModel):
    """Schema de resposta dos limites do plano."""
    leads_per_month: int
    agents: int
    campaigns: int
    whatsapp_enabled: bool
    whatsapp_official_api: bool
    advanced_filters: bool
    funnel_reports: bool
    campaign_comparison: bool
    crm_integration: bool
    priority_support: bool
    sso: bool


class UserResponse(UserBase):
    """Schema de resposta de usuário."""
    id: UUID
    role: UserRole
    plan_tier: PlanTier
    is_active: bool
    is_admin: bool
    plan_limits: PlanLimitsResponse
    profile_completed: bool = False
    person_type: Optional[PersonType] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """Schema de usuário no banco (inclui hash da senha)."""
    password_hash: str
