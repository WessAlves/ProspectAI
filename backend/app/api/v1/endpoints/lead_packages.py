"""
Endpoints para gerenciamento de pacotes de leads.

Permite:
- Listar pacotes disponíveis para compra
- Ver resumo de uso de leads
- Comprar pacotes adicionais
- Confirmar pagamentos
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User, PLAN_LIMITS
from app.db.models.lead_package import LeadPackage, PackageType, PaymentStatus
from app.schemas.lead_package import (
    AvailablePackagesResponse,
    PackageInfo,
    PurchasePackageRequest,
    LeadPackageResponse,
    LeadUsageSummary,
    LeadLimitReachedResponse,
    PackageTypeEnum,
)
from app.services.lead_limits import (
    get_lead_usage_summary,
    purchase_package,
    confirm_package_payment,
    get_available_packages,
    get_user_lead_limits,
)
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/available", response_model=AvailablePackagesResponse)
async def list_available_packages(
    current_user: User = Depends(get_current_user),
):
    """
    Lista os pacotes de leads disponíveis para compra.
    
    Retorna informações sobre cada pacote:
    - Quantidade de leads
    - Preço
    - Preço por lead
    """
    packages = get_available_packages()
    return AvailablePackagesResponse(packages=packages)


@router.get("/usage", response_model=LeadUsageSummary)
async def get_usage_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o resumo de uso de leads do usuário.
    
    Inclui:
    - Limite do plano atual
    - Leads usados no mês
    - Leads disponíveis de pacotes
    - Porcentagem de uso
    - Status de limite atingido
    - Pacotes ativos
    """
    return await get_lead_usage_summary(db, current_user.id)


@router.get("/check-limit")
async def check_lead_limit(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verifica rapidamente se o usuário ainda tem leads disponíveis.
    
    Útil para verificar antes de iniciar uma campanha.
    """
    limits = await get_user_lead_limits(db, current_user.id)
    
    return {
        "can_add_leads": limits["remaining"] > 0 or limits["is_unlimited"],
        "remaining": limits["remaining"],
        "is_unlimited": limits["is_unlimited"],
        "plan": limits["plan_name"],
    }


@router.post("/purchase", response_model=LeadPackageResponse)
async def purchase_lead_package(
    request: PurchasePackageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia a compra de um pacote de leads.
    
    O pacote fica como PENDENTE até o pagamento ser confirmado.
    Em ambiente de desenvolvimento, use `auto_confirm=true` para 
    confirmar automaticamente.
    
    Para produção, integrar com gateway de pagamento que chamará
    o endpoint de confirmação via webhook.
    """
    try:
        # Converter o enum do schema para o enum do model
        package_type = PackageType(request.package_type.value)
        
        package = await purchase_package(
            db=db,
            user_id=current_user.id,
            package_type=package_type,
            payment_method=request.payment_method,
            auto_confirm=False,  # Em produção, esperar webhook
        )
        
        # Converter para response
        return LeadPackageResponse(
            id=package.id,
            user_id=package.user_id,
            package_type=PackageTypeEnum(package.package_type.value),
            leads_purchased=package.leads_purchased,
            leads_used=package.leads_used,
            leads_remaining=package.leads_remaining,
            price_paid=float(package.price_paid),
            payment_status=package.payment_status.value,
            payment_id=package.payment_id,
            payment_method=package.payment_method,
            purchase_month=package.purchase_month,
            is_active=package.is_active,
            created_at=package.created_at,
        )
        
    except Exception as e:
        logger.error(f"Erro ao criar pacote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar compra: {str(e)}"
        )


@router.post("/purchase/dev", response_model=LeadPackageResponse)
async def purchase_lead_package_dev(
    request: PurchasePackageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    [DEV ONLY] Compra um pacote com confirmação automática.
    
    Use apenas em ambiente de desenvolvimento/testes.
    Em produção, este endpoint deve ser desabilitado.
    """
    try:
        package_type = PackageType(request.package_type.value)
        
        package = await purchase_package(
            db=db,
            user_id=current_user.id,
            package_type=package_type,
            payment_method=request.payment_method or "dev_auto",
            auto_confirm=True,  # Confirma automaticamente
        )
        
        logger.info(f"[DEV] Pacote {package.id} criado e confirmado para usuário {current_user.id}")
        
        return LeadPackageResponse(
            id=package.id,
            user_id=package.user_id,
            package_type=PackageTypeEnum(package.package_type.value),
            leads_purchased=package.leads_purchased,
            leads_used=package.leads_used,
            leads_remaining=package.leads_remaining,
            price_paid=float(package.price_paid),
            payment_status=package.payment_status.value,
            payment_id=package.payment_id,
            payment_method=package.payment_method,
            purchase_month=package.purchase_month,
            is_active=package.is_active,
            created_at=package.created_at,
        )
        
    except Exception as e:
        logger.error(f"Erro ao criar pacote (dev): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar compra: {str(e)}"
        )


@router.post("/confirm/{package_id}", response_model=LeadPackageResponse)
async def confirm_payment(
    package_id: str,
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirma o pagamento de um pacote pendente.
    
    Normalmente chamado por webhook do gateway de pagamento.
    Também pode ser usado pelo admin para confirmar manualmente.
    """
    from uuid import UUID as UUIDType
    
    try:
        package_uuid = UUIDType(package_id)
        
        # Verificar se o pacote pertence ao usuário (ou é admin)
        from sqlalchemy import select
        query = select(LeadPackage).where(LeadPackage.id == package_uuid)
        result = await db.execute(query)
        package = result.scalar_one_or_none()
        
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pacote não encontrado"
            )
        
        # Verificar propriedade ou admin
        if package.user_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para confirmar este pacote"
            )
        
        package = await confirm_package_payment(db, package_uuid, payment_id)
        
        return LeadPackageResponse(
            id=package.id,
            user_id=package.user_id,
            package_type=PackageTypeEnum(package.package_type.value),
            leads_purchased=package.leads_purchased,
            leads_used=package.leads_used,
            leads_remaining=package.leads_remaining,
            price_paid=float(package.price_paid),
            payment_status=package.payment_status.value,
            payment_id=package.payment_id,
            payment_method=package.payment_method,
            purchase_month=package.purchase_month,
            is_active=package.is_active,
            created_at=package.created_at,
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao confirmar pagamento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao confirmar pagamento: {str(e)}"
        )


@router.get("/my-packages", response_model=List[LeadPackageResponse])
async def list_my_packages(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista os pacotes de leads do usuário.
    
    - **active_only**: Se True, retorna apenas pacotes ativos (com leads disponíveis)
    """
    from sqlalchemy import select, and_
    
    query = select(LeadPackage).where(LeadPackage.user_id == current_user.id)
    
    if active_only:
        query = query.where(
            and_(
                LeadPackage.is_active == True,
                LeadPackage.payment_status == PaymentStatus.PAID,
                LeadPackage.leads_used < LeadPackage.leads_purchased
            )
        )
    
    query = query.order_by(LeadPackage.created_at.desc())
    
    result = await db.execute(query)
    packages = result.scalars().all()
    
    return [
        LeadPackageResponse(
            id=pkg.id,
            user_id=pkg.user_id,
            package_type=PackageTypeEnum(pkg.package_type.value),
            leads_purchased=pkg.leads_purchased,
            leads_used=pkg.leads_used,
            leads_remaining=pkg.leads_remaining,
            price_paid=float(pkg.price_paid),
            payment_status=pkg.payment_status.value,
            payment_id=pkg.payment_id,
            payment_method=pkg.payment_method,
            purchase_month=pkg.purchase_month,
            is_active=pkg.is_active,
            created_at=pkg.created_at,
        )
        for pkg in packages
    ]


@router.get("/limit-reached", response_model=LeadLimitReachedResponse)
async def get_limit_reached_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna informações quando o limite é atingido.
    
    Inclui:
    - Resumo de uso atual
    - Pacotes disponíveis para compra
    - Opções de upgrade de plano
    """
    usage = await get_lead_usage_summary(db, current_user.id)
    available_packages = get_available_packages()
    
    # Opções de upgrade baseadas no plano atual
    upgrade_options = []
    current_plan = current_user.plan_tier.value
    
    plan_upgrades = {
        "free": [
            {"plan": "starter", "leads": 500, "price": 97},
            {"plan": "pro", "leads": 2000, "price": 297},
            {"plan": "scale", "leads": "ilimitado", "price": 597},
        ],
        "starter": [
            {"plan": "pro", "leads": 2000, "price": 297},
            {"plan": "scale", "leads": "ilimitado", "price": 597},
        ],
        "pro": [
            {"plan": "scale", "leads": "ilimitado", "price": 597},
        ],
        "scale": [],  # Já está no plano máximo
    }
    
    upgrade_options = plan_upgrades.get(current_plan, [])
    
    return LeadLimitReachedResponse(
        message=f"Você atingiu o limite de {usage.plan_monthly_limit} leads do plano {usage.plan_name}.",
        usage=usage,
        available_packages=available_packages,
        upgrade_options=upgrade_options,
    )
