"""
Endpoints de autenticação.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.user import User, PlanTier
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Token, TokenRefresh, LoginRequest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.dependencies import get_current_user

router = APIRouter()


def get_plan_tier_from_id(plan_id: str) -> PlanTier:
    """Converte o ID do plano para o enum PlanTier."""
    plan_mapping = {
        "free": PlanTier.FREE,
        "starter": PlanTier.STARTER,
        "pro": PlanTier.PRO,
        "scale": PlanTier.SCALE,
    }
    return plan_mapping.get(plan_id.lower(), PlanTier.FREE)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra um novo usuário.
    
    - **email**: Email único do usuário
    - **password**: Senha (mínimo 6 caracteres)
    - **full_name**: Nome completo
    - **plan_id**: ID do plano (free, starter, pro, scale) - opcional, padrão: free
    """
    # Verificar se email já existe
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado",
        )
    
    # Obter o plano
    plan_tier = get_plan_tier_from_id(user_data.plan_id or "free")
    
    # Criar usuário
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        plan_tier=plan_tier,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Autentica um usuário e retorna os tokens.
    
    - **email**: Email do usuário
    - **password**: Senha do usuário
    """
    # Buscar usuário
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )
    
    # Gerar tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    """
    Renova o access token usando o refresh token.
    
    - **refresh_token**: Token de refresh válido
    """
    user_id = verify_token(token_data.refresh_token, token_type="refresh")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )
    
    # Verificar se usuário ainda existe e está ativo
    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
        )
    
    # Gerar novos tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Retorna as informações do usuário autenticado.
    """
    return current_user


@router.put("/me/plan", response_model=UserResponse)
async def update_user_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza o plano do usuário autenticado.
    
    - **plan_id**: ID do plano (free, starter, pro, scale)
    
    Nota: Em produção, isso deveria passar por um sistema de pagamento.
    """
    valid_plans = ["free", "starter", "pro", "scale"]
    if plan_id.lower() not in valid_plans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plano inválido. Opções: {', '.join(valid_plans)}",
        )
    
    plan_tier = get_plan_tier_from_id(plan_id)
    current_user.plan_tier = plan_tier
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Realiza logout do usuário.
    
    Nota: Com JWT stateless, o logout é feito no client-side
    descartando o token. Este endpoint serve para consistência da API.
    """
    return {"message": "Logout realizado com sucesso"}
