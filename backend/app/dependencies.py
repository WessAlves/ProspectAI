"""
Dependências de injeção para a API.
"""

from typing import Generator, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.user import User
from app.core.security import verify_token


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency que obtém o usuário atual a partir do token JWT.
    
    Args:
        credentials: Token de autorização do header
        db: Sessão do banco de dados
    
    Returns:
        User: Usuário autenticado
    
    Raises:
        HTTPException: Se o token for inválido ou o usuário não existir
    """
    token = credentials.credentials
    user_id = verify_token(token, token_type="access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )
    
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency que verifica se o usuário é um superusuário.
    
    Args:
        current_user: Usuário atual
    
    Returns:
        User: Superusuário
    
    Raises:
        HTTPException: Se não for superusuário
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente",
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency que verifica se o usuário é um administrador.
    
    Args:
        current_user: Usuário atual
    
    Returns:
        User: Usuário administrador
    
    Raises:
        HTTPException: Se não for administrador
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user


def get_pagination_params(
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Dependency para parâmetros de paginação.
    
    Args:
        page: Número da página (1-indexed)
        page_size: Tamanho da página
    
    Returns:
        dict: Parâmetros de paginação
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100
    
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
    }
