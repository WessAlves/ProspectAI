"""
Endpoints de Administração (apenas para admins).
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.plan import ServicePlan
from app.db.models.campaign import Campaign
from app.db.models.agent import Agent
from app.schemas.common import MessageResponse
from app.dependencies import get_current_admin_user

router = APIRouter()


# =====================
# Dashboard Admin
# =====================

@router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Retorna estatísticas gerais da plataforma (apenas admin).
    """
    # Total de usuários
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar()
    
    # Usuários por role
    admin_result = await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN)
    )
    total_admins = admin_result.scalar()
    
    # Total de campanhas
    campaigns_result = await db.execute(select(func.count(Campaign.id)))
    total_campaigns = campaigns_result.scalar()
    
    # Total de agentes
    agents_result = await db.execute(select(func.count(Agent.id)))
    total_agents = agents_result.scalar()
    
    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_common_users": total_users - total_admins,
        "total_campaigns": total_campaigns,
        "total_agents": total_agents,
    }


# =====================
# Gerenciamento de Usuários
# =====================

@router.get("/users")
async def list_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    page: int = 1,
    page_size: int = 20,
):
    """
    Lista todos os usuários da plataforma (apenas admin).
    """
    offset = (page - 1) * page_size
    
    result = await db.execute(
        select(User)
        .offset(offset)
        .limit(page_size)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    # Conta total
    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar()
    
    return {
        "items": [
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "plan_tier": user.plan_tier.value,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    role: UserRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Atualiza o perfil (role) de um usuário (apenas admin).
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode alterar seu próprio perfil",
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    
    user.role = role
    await db.commit()
    
    return {
        "message": f"Perfil do usuário atualizado para {role.value}",
        "user_id": str(user_id),
        "new_role": role.value,
    }


@router.patch("/users/{user_id}/status")
async def toggle_user_status(
    user_id: UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Ativa ou desativa um usuário (apenas admin).
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar sua própria conta",
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    
    user.is_active = is_active
    await db.commit()
    
    status_text = "ativado" if is_active else "desativado"
    return {
        "message": f"Usuário {status_text} com sucesso",
        "user_id": str(user_id),
        "is_active": is_active,
    }
