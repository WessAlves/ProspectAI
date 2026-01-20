"""
Endpoints de Planos de Serviço.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.user import User, PlanTier, PLAN_LIMITS
from app.db.models.plan import ServicePlan
from app.schemas.plan import ServicePlanCreate, ServicePlanUpdate, ServicePlanResponse
from app.schemas.common import MessageResponse
from app.dependencies import get_current_user, get_pagination_params

router = APIRouter()


# ============================================
# Endpoints de Planos de Assinatura da Plataforma
# ============================================

class SubscriptionPlanResponse(BaseModel):
    """Schema de resposta para planos de assinatura."""
    id: str
    name: str
    price: float
    price_label: str
    description: str
    limits: dict
    features: dict


SUBSCRIPTION_PLANS = [
    {
        "id": "free",
        "name": "Free",
        "price": 0,
        "price_label": "Grátis",
        "description": "Teste a qualidade da prospecção e da IA",
    },
    {
        "id": "starter",
        "name": "Starter",
        "price": 199.90,
        "price_label": "R$ 199,90/mês",
        "description": "Ideal para empreendedores iniciando a prospecção",
    },
    {
        "id": "pro",
        "name": "Pro",
        "price": 399.90,
        "price_label": "R$ 399,90/mês",
        "description": "Para pequenas agências e empresas que buscam escala",
    },
    {
        "id": "scale",
        "name": "Scale",
        "price": 799.90,
        "price_label": "R$ 799,90/mês",
        "description": "Para grandes agências com alto volume",
    },
]


@router.get("/subscription-plans", response_model=List[SubscriptionPlanResponse])
async def list_subscription_plans():
    """
    Lista todos os planos de assinatura disponíveis da plataforma.
    Não requer autenticação.
    """
    result = []
    for plan in SUBSCRIPTION_PLANS:
        plan_tier = PlanTier(plan["id"])
        limits = PLAN_LIMITS[plan_tier]
        result.append(
            SubscriptionPlanResponse(
                id=plan["id"],
                name=plan["name"],
                price=plan["price"],
                price_label=plan["price_label"],
                description=plan["description"],
                limits={
                    "prospects_per_month": limits["prospects_per_month"],
                    "agents": limits["agents"],
                    "campaigns": limits["campaigns"],
                },
                features={
                    "whatsapp_enabled": limits["whatsapp_enabled"],
                    "whatsapp_official_api": limits["whatsapp_official_api"],
                    "advanced_filters": limits["advanced_filters"],
                    "funnel_reports": limits["funnel_reports"],
                    "campaign_comparison": limits["campaign_comparison"],
                    "crm_integration": limits["crm_integration"],
                    "priority_support": limits["priority_support"],
                    "sso": limits["sso"],
                },
            )
        )
    return result


# ============================================
# Endpoints de Planos de Serviço do Usuário
# ============================================

@router.post("", response_model=ServicePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: ServicePlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria um novo plano de serviço.
    
    - **name**: Nome do plano/serviço
    - **description**: Descrição detalhada
    - **price**: Preço do serviço
    - **features**: Lista de características
    """
    plan = ServicePlan(
        user_id=current_user.id,
        name=plan_data.name,
        description=plan_data.description,
        price=plan_data.price,
        features=plan_data.features,
    )
    
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    
    return plan


@router.get("", response_model=List[ServicePlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    """
    Lista todos os planos de serviço do usuário.
    """
    result = await db.execute(
        select(ServicePlan)
        .where(ServicePlan.user_id == current_user.id)
        .offset(pagination["offset"])
        .limit(pagination["page_size"])
        .order_by(ServicePlan.created_at.desc())
    )
    plans = result.scalars().all()
    
    return plans


@router.get("/{plan_id}", response_model=ServicePlanResponse)
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os detalhes de um plano específico.
    """
    result = await db.execute(
        select(ServicePlan)
        .where(ServicePlan.id == plan_id, ServicePlan.user_id == current_user.id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano não encontrado",
        )
    
    return plan


@router.put("/{plan_id}", response_model=ServicePlanResponse)
async def update_plan(
    plan_id: UUID,
    plan_data: ServicePlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza um plano existente.
    """
    result = await db.execute(
        select(ServicePlan)
        .where(ServicePlan.id == plan_id, ServicePlan.user_id == current_user.id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano não encontrado",
        )
    
    # Atualizar campos fornecidos
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    await db.commit()
    await db.refresh(plan)
    
    return plan


@router.delete("/{plan_id}", response_model=MessageResponse)
async def delete_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deleta um plano de serviço.
    """
    result = await db.execute(
        select(ServicePlan)
        .where(ServicePlan.id == plan_id, ServicePlan.user_id == current_user.id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano não encontrado",
        )
    
    await db.delete(plan)
    await db.commit()
    
    return MessageResponse(message="Plano deletado com sucesso")
