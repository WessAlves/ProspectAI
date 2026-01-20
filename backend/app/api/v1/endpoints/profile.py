"""
Endpoints de perfil do usuário.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.user import User, PersonType
from app.schemas.user import (
    ProfileResponse,
    IndividualProfileUpdate,
    CompanyProfileUpdate,
    PasswordChange,
    PaymentMethodCreate,
    PaymentMethodResponse,
)
from app.core.security import get_password_hash, verify_password
from app.dependencies import get_current_user

router = APIRouter()


def get_card_brand(card_number: str) -> str:
    """Detecta a bandeira do cartão pelo número."""
    if card_number.startswith('4'):
        return 'visa'
    elif card_number.startswith(('51', '52', '53', '54', '55')) or \
         (2221 <= int(card_number[:4]) <= 2720):
        return 'mastercard'
    elif card_number.startswith(('34', '37')):
        return 'amex'
    elif card_number.startswith('6011') or card_number.startswith('65'):
        return 'discover'
    elif card_number.startswith(('36', '38', '39')) or \
         card_number.startswith(('300', '301', '302', '303', '304', '305')):
        return 'diners'
    elif card_number.startswith(('6062', '3841')):
        return 'hipercard'
    elif card_number.startswith('50'):
        return 'elo'
    return 'unknown'


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o perfil completo do usuário autenticado.
    """
    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        profile_completed=current_user.profile_completed,
        person_type=current_user.person_type,
        phone=current_user.phone,
        # Pessoa Física
        cpf=current_user.cpf,
        birth_date=current_user.birth_date,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        # Pessoa Jurídica
        cnpj=current_user.cnpj,
        company_name=current_user.company_name,
        trade_name=current_user.trade_name,
        state_registration=current_user.state_registration,
        municipal_registration=current_user.municipal_registration,
        # Endereço
        address_street=current_user.address_street,
        address_number=current_user.address_number,
        address_complement=current_user.address_complement,
        address_neighborhood=current_user.address_neighborhood,
        address_city=current_user.address_city,
        address_state=current_user.address_state,
        address_zip_code=current_user.address_zip_code,
        # Pagamento
        has_payment_method=current_user.payment_method_id is not None,
        card_last_four=current_user.card_last_four,
        card_brand=current_user.card_brand,
    )


@router.put("/profile/individual", response_model=ProfileResponse)
async def update_individual_profile(
    profile_data: IndividualProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza o perfil do usuário como pessoa física.
    
    - **first_name**: Primeiro nome
    - **last_name**: Sobrenome
    - **cpf**: CPF (validado)
    - **birth_date**: Data de nascimento (deve ter 18+ anos)
    - **phone**: Telefone (opcional)
    - **address_***: Campos de endereço (opcionais)
    """
    # Verificar se CPF já está em uso por outro usuário
    if profile_data.cpf:
        result = await db.execute(
            select(User).where(
                User.cpf == profile_data.cpf,
                User.id != current_user.id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF já cadastrado por outro usuário",
            )
    
    # Atualizar campos
    current_user.person_type = PersonType.INDIVIDUAL
    current_user.first_name = profile_data.first_name
    current_user.last_name = profile_data.last_name
    current_user.cpf = profile_data.cpf
    current_user.birth_date = profile_data.birth_date
    current_user.phone = profile_data.phone
    current_user.full_name = f"{profile_data.first_name} {profile_data.last_name}"
    
    # Limpar campos de pessoa jurídica
    current_user.cnpj = None
    current_user.company_name = None
    current_user.trade_name = None
    current_user.state_registration = None
    current_user.municipal_registration = None
    
    # Endereço
    current_user.address_street = profile_data.address_street
    current_user.address_number = profile_data.address_number
    current_user.address_complement = profile_data.address_complement
    current_user.address_neighborhood = profile_data.address_neighborhood
    current_user.address_city = profile_data.address_city
    current_user.address_state = profile_data.address_state
    current_user.address_zip_code = profile_data.address_zip_code
    
    # Marcar perfil como completo
    current_user.profile_completed = True
    
    await db.commit()
    await db.refresh(current_user)
    
    return await get_profile(current_user)


@router.put("/profile/company", response_model=ProfileResponse)
async def update_company_profile(
    profile_data: CompanyProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza o perfil do usuário como pessoa jurídica.
    
    - **cnpj**: CNPJ (validado)
    - **company_name**: Razão Social
    - **trade_name**: Nome Fantasia (opcional)
    - **first_name**: Nome do responsável
    - **last_name**: Sobrenome do responsável
    - **phone**: Telefone (opcional)
    - **address_***: Campos de endereço (opcionais)
    """
    # Verificar se CNPJ já está em uso por outro usuário
    if profile_data.cnpj:
        result = await db.execute(
            select(User).where(
                User.cnpj == profile_data.cnpj,
                User.id != current_user.id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ já cadastrado por outro usuário",
            )
    
    # Atualizar campos
    current_user.person_type = PersonType.COMPANY
    current_user.cnpj = profile_data.cnpj
    current_user.company_name = profile_data.company_name
    current_user.trade_name = profile_data.trade_name
    current_user.state_registration = profile_data.state_registration
    current_user.municipal_registration = profile_data.municipal_registration
    current_user.first_name = profile_data.first_name
    current_user.last_name = profile_data.last_name
    current_user.phone = profile_data.phone
    current_user.full_name = f"{profile_data.first_name} {profile_data.last_name}"
    
    # Limpar campos de pessoa física
    current_user.cpf = None
    current_user.birth_date = None
    
    # Endereço
    current_user.address_street = profile_data.address_street
    current_user.address_number = profile_data.address_number
    current_user.address_complement = profile_data.address_complement
    current_user.address_neighborhood = profile_data.address_neighborhood
    current_user.address_city = profile_data.address_city
    current_user.address_state = profile_data.address_state
    current_user.address_zip_code = profile_data.address_zip_code
    
    # Marcar perfil como completo
    current_user.profile_completed = True
    
    await db.commit()
    await db.refresh(current_user)
    
    return await get_profile(current_user)


@router.put("/password")
async def change_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Altera a senha do usuário.
    
    - **current_password**: Senha atual
    - **new_password**: Nova senha (mínimo 6 caracteres)
    - **confirm_password**: Confirmação da nova senha
    """
    # Verificar senha atual
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta",
        )
    
    # Atualizar senha
    current_user.password_hash = get_password_hash(password_data.new_password)
    
    await db.commit()
    
    return {"message": "Senha alterada com sucesso"}


@router.get("/payment-method", response_model=PaymentMethodResponse)
async def get_payment_method(
    current_user: User = Depends(get_current_user),
):
    """
    Retorna as informações do método de pagamento do usuário.
    """
    return PaymentMethodResponse(
        has_payment_method=current_user.payment_method_id is not None,
        card_last_four=current_user.card_last_four,
        card_brand=current_user.card_brand,
        exp_month=current_user.card_exp_month,
        exp_year=current_user.card_exp_year,
        billing_name=current_user.billing_name,
    )


@router.post("/payment-method", response_model=PaymentMethodResponse)
async def add_payment_method(
    payment_data: PaymentMethodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Adiciona ou atualiza o método de pagamento do usuário.
    
    NOTA: Em produção, isso deve usar um gateway de pagamento (Stripe, PagSeguro, etc.)
    para tokenizar o cartão de forma segura. Nunca armazenar números de cartão diretamente.
    
    - **card_number**: Número do cartão
    - **card_holder_name**: Nome no cartão
    - **exp_month**: Mês de expiração (1-12)
    - **exp_year**: Ano de expiração
    - **cvv**: Código de segurança
    """
    # Em produção, aqui você chamaria a API do gateway de pagamento
    # Ex: stripe.PaymentMethod.create(...)
    # E armazenaria apenas o ID retornado
    
    # Simulação - armazenar metadados seguros
    card_brand = get_card_brand(payment_data.card_number)
    card_last_four = payment_data.card_number[-4:]
    
    # Em produção: payment_method_id viria do gateway
    import uuid
    payment_method_id = f"pm_simulated_{uuid.uuid4().hex[:16]}"
    
    current_user.payment_method_id = payment_method_id
    current_user.card_last_four = card_last_four
    current_user.card_brand = card_brand
    current_user.card_exp_month = payment_data.exp_month
    current_user.card_exp_year = payment_data.exp_year
    current_user.billing_name = payment_data.card_holder_name
    
    await db.commit()
    await db.refresh(current_user)
    
    return PaymentMethodResponse(
        has_payment_method=True,
        card_last_four=card_last_four,
        card_brand=card_brand,
        exp_month=payment_data.exp_month,
        exp_year=payment_data.exp_year,
        billing_name=payment_data.card_holder_name,
    )


@router.delete("/payment-method")
async def remove_payment_method(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove o método de pagamento do usuário.
    """
    if not current_user.payment_method_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum método de pagamento cadastrado",
        )
    
    # Em produção: também remover do gateway de pagamento
    
    current_user.payment_method_id = None
    current_user.card_last_four = None
    current_user.card_brand = None
    current_user.card_exp_month = None
    current_user.card_exp_year = None
    current_user.billing_name = None
    
    await db.commit()
    
    return {"message": "Método de pagamento removido com sucesso"}
