"""
Service para gerenciamento de limites de leads.

Este módulo contém toda a lógica para:
- Verificar se usuário atingiu limite de leads
- Calcular leads disponíveis (plano + pacotes)
- Pausar campanhas quando limite é atingido
- Gerenciar compra de pacotes adicionais
"""

import logging
from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.user import User, PlanTier, PLAN_LIMITS
from app.db.models.prospect import Prospect
from app.db.models.campaign import Campaign, CampaignStatus
from app.db.models.lead_package import LeadPackage, PackageType, PaymentStatus, PACKAGE_CONFIG
from app.schemas.lead_package import (
    LeadUsageSummary, 
    LeadPackageResponse,
    PackageInfo,
    PackageTypeEnum,
    PACKAGE_CONFIG as SCHEMA_PACKAGE_CONFIG
)

logger = logging.getLogger(__name__)


async def get_leads_used_this_month(db: AsyncSession, user_id: int) -> int:
    """
    Conta quantos leads/prospects o usuário gerou no mês atual.
    
    Conta todos os prospects de todas as campanhas do usuário.
    """
    now = datetime.utcnow()
    first_day_of_month = datetime(now.year, now.month, 1)
    
    # Buscar todas as campanhas do usuário
    campaigns_query = select(Campaign.id).where(Campaign.user_id == user_id)
    campaigns_result = await db.execute(campaigns_query)
    campaign_ids = [row[0] for row in campaigns_result.fetchall()]
    
    if not campaign_ids:
        return 0
    
    # Contar prospects criados no mês atual
    count_query = select(func.count(Prospect.id)).where(
        and_(
            Prospect.campaign_id.in_(campaign_ids),
            Prospect.created_at >= first_day_of_month
        )
    )
    result = await db.execute(count_query)
    return result.scalar() or 0


async def get_active_packages(db: AsyncSession, user_id: int) -> List[LeadPackage]:
    """
    Busca todos os pacotes ativos do usuário.
    
    Pacotes ativos são aqueles que:
    - Estão marcados como is_active=True
    - Pagamento foi confirmado (paid)
    - Ainda têm leads disponíveis (leads_used < leads_purchased)
    """
    query = select(LeadPackage).where(
        and_(
            LeadPackage.user_id == user_id,
            LeadPackage.is_active == True,
            LeadPackage.payment_status == PaymentStatus.PAID,
            LeadPackage.leads_used < LeadPackage.leads_purchased
        )
    ).order_by(LeadPackage.created_at.asc())  # Usa os mais antigos primeiro
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_leads_from_packages(db: AsyncSession, user_id: int) -> int:
    """
    Calcula quantos leads disponíveis o usuário tem de pacotes.
    
    Retorna a soma de (leads_purchased - leads_used) de todos os pacotes ativos.
    """
    packages = await get_active_packages(db, user_id)
    return sum(pkg.leads_remaining for pkg in packages)


async def get_user_lead_limits(db: AsyncSession, user_id: int) -> dict:
    """
    Retorna informações detalhadas sobre os limites de leads do usuário.
    
    Returns:
        dict com:
        - plan_limit: limite mensal do plano
        - package_leads: leads disponíveis de pacotes
        - total_available: total disponível (plano + pacotes)
        - used_this_month: quantos foram usados no mês
        - remaining: quantos ainda podem ser usados
        - is_unlimited: se o plano é ilimitado
    """
    # Buscar usuário
    user_query = select(User).where(User.id == user_id)
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError(f"Usuário {user_id} não encontrado")
    
    # Limites do plano
    plan_limits = PLAN_LIMITS.get(user.plan_tier, PLAN_LIMITS[PlanTier.FREE])
    plan_limit = plan_limits["leads_per_month"]
    is_unlimited = plan_limit == -1
    
    # Se ilimitado, retorna sem contar
    if is_unlimited:
        return {
            "plan_limit": -1,
            "package_leads": 0,
            "total_available": -1,
            "used_this_month": await get_leads_used_this_month(db, user_id),
            "remaining": -1,
            "is_unlimited": True,
            "plan_name": user.plan_tier.value,
        }
    
    # Calcular valores
    used_this_month = await get_leads_used_this_month(db, user_id)
    package_leads = await get_leads_from_packages(db, user_id)
    total_available = plan_limit + package_leads
    remaining = max(0, total_available - used_this_month)
    
    return {
        "plan_limit": plan_limit,
        "package_leads": package_leads,
        "total_available": total_available,
        "used_this_month": used_this_month,
        "remaining": remaining,
        "is_unlimited": False,
        "plan_name": user.plan_tier.value,
    }


async def check_can_add_lead(db: AsyncSession, user_id: int) -> Tuple[bool, int]:
    """
    Verifica se o usuário pode adicionar mais um lead.
    
    Returns:
        Tuple[bool, int]: (pode_adicionar, leads_restantes)
    """
    limits = await get_user_lead_limits(db, user_id)
    
    if limits["is_unlimited"]:
        return True, -1
    
    can_add = limits["remaining"] > 0
    return can_add, limits["remaining"]


async def use_lead_from_package(db: AsyncSession, user_id: int) -> bool:
    """
    Consome um lead de um pacote (quando o limite do plano é excedido).
    
    Usa o pacote mais antigo primeiro (FIFO).
    
    Returns:
        bool: True se conseguiu usar de um pacote, False se não há pacotes disponíveis
    """
    packages = await get_active_packages(db, user_id)
    
    if not packages:
        return False
    
    # Usa o primeiro pacote disponível (mais antigo)
    package = packages[0]
    package.leads_used += 1
    
    # Desativa o pacote se acabaram os leads
    if package.leads_used >= package.leads_purchased:
        package.is_active = False
        logger.info(f"Pacote {package.id} do usuário {user_id} esgotado e desativado")
    
    await db.commit()
    return True


async def pause_user_campaigns(db: AsyncSession, user_id: int, reason: str = "Limite de leads atingido") -> int:
    """
    Pausa todas as campanhas ativas do usuário.
    
    Returns:
        int: Número de campanhas pausadas
    """
    # Buscar campanhas ativas
    query = select(Campaign).where(
        and_(
            Campaign.user_id == user_id,
            Campaign.status.in_([CampaignStatus.ACTIVE, CampaignStatus.SCRAPING])
        )
    )
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    count = 0
    for campaign in campaigns:
        campaign.status = CampaignStatus.PAUSED
        count += 1
        logger.warning(f"Campanha {campaign.id} pausada: {reason}")
    
    if count > 0:
        await db.commit()
        logger.warning(f"Pausadas {count} campanhas do usuário {user_id}: {reason}")
    
    return count


async def get_lead_usage_summary(db: AsyncSession, user_id: int) -> LeadUsageSummary:
    """
    Retorna um resumo completo do uso de leads do usuário.
    
    Usado para exibir no dashboard e quando limite é atingido.
    """
    limits = await get_user_lead_limits(db, user_id)
    packages = await get_active_packages(db, user_id)
    
    # Verificar se tem campanhas pausadas por limite
    paused_query = select(func.count(Campaign.id)).where(
        and_(
            Campaign.user_id == user_id,
            Campaign.status == CampaignStatus.PAUSED
        )
    )
    paused_result = await db.execute(paused_query)
    has_paused = (paused_result.scalar() or 0) > 0
    
    # Calcular porcentagem de uso
    if limits["is_unlimited"]:
        usage_percentage = 0.0
    elif limits["total_available"] > 0:
        usage_percentage = min(100.0, (limits["used_this_month"] / limits["total_available"]) * 100)
    else:
        usage_percentage = 100.0 if limits["used_this_month"] > 0 else 0.0
    
    # Converter pacotes para response
    package_responses = [
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
    
    return LeadUsageSummary(
        plan_name=limits["plan_name"].title(),
        plan_monthly_limit=limits["plan_limit"],
        leads_used_this_month=limits["used_this_month"],
        leads_from_plan=limits["plan_limit"] if not limits["is_unlimited"] else -1,
        leads_from_packages=limits["package_leads"],
        total_available=limits["total_available"],
        total_remaining=limits["remaining"],
        usage_percentage=round(usage_percentage, 1),
        is_limit_reached=limits["remaining"] == 0 and not limits["is_unlimited"],
        campaigns_paused=has_paused and limits["remaining"] == 0,
        active_packages=package_responses,
    )


async def purchase_package(
    db: AsyncSession, 
    user_id,  # UUID
    package_type: PackageType,
    payment_method: Optional[str] = None,
    auto_confirm: bool = False
) -> LeadPackage:
    """
    Cria uma compra de pacote de leads.
    
    Args:
        user_id: ID do usuário (UUID)
        package_type: Tipo do pacote
        payment_method: Método de pagamento (pix, card, boleto)
        auto_confirm: Se True, marca como pago automaticamente (para testes)
    
    Returns:
        LeadPackage criado
    """
    config = PACKAGE_CONFIG[package_type]
    now = datetime.utcnow()
    purchase_month = now.strftime("%Y-%m")  # Formato YYYY-MM
    
    package = LeadPackage(
        user_id=user_id,
        package_type=package_type,
        leads_purchased=config["leads"],
        leads_used=0,
        price_paid=config["price"],
        payment_status=PaymentStatus.PAID if auto_confirm else PaymentStatus.PENDING,
        payment_method=payment_method,
        purchase_month=purchase_month,
        is_active=auto_confirm,  # Só ativa se pagamento confirmado
    )
    
    db.add(package)
    await db.commit()
    await db.refresh(package)
    
    logger.info(
        f"Pacote {package_type.value} criado para usuário {user_id}. "
        f"Status: {'PAGO' if auto_confirm else 'PENDENTE'}"
    )
    
    return package


async def confirm_package_payment(db: AsyncSession, package_id, payment_id: str) -> LeadPackage:
    """
    Confirma o pagamento de um pacote.
    
    Chamado após webhook de pagamento confirmar.
    """
    query = select(LeadPackage).where(LeadPackage.id == package_id)
    result = await db.execute(query)
    package = result.scalar_one_or_none()
    
    if not package:
        raise ValueError(f"Pacote {package_id} não encontrado")
    
    if package.payment_status == PaymentStatus.PAID:
        logger.warning(f"Pacote {package_id} já estava confirmado")
        return package
    
    package.payment_status = PaymentStatus.PAID
    package.payment_id = payment_id
    package.is_active = True
    
    await db.commit()
    await db.refresh(package)
    
    logger.info(f"Pagamento do pacote {package_id} confirmado. Leads: {package.leads_purchased}")
    
    return package


def get_available_packages() -> List[PackageInfo]:
    """
    Retorna lista de pacotes disponíveis para compra.
    """
    return [
        PackageInfo(
            package_type=pkg_type,
            leads=config["leads"],
            price=config["price"],
            display_name=config["display_name"],
            price_per_lead=round(config["price"] / config["leads"], 2),
        )
        for pkg_type, config in SCHEMA_PACKAGE_CONFIG.items()
    ]


# ============================================================================
# Funções síncronas para uso em Celery tasks
# ============================================================================

def sync_check_can_add_lead(db_session, user_id: int) -> Tuple[bool, int]:
    """
    Versão síncrona de check_can_add_lead para uso em Celery tasks.
    
    Args:
        db_session: Session síncrona do SQLAlchemy
        user_id: ID do usuário
    
    Returns:
        Tuple[bool, int]: (pode_adicionar, leads_restantes)
    """
    from sqlalchemy import select, func, and_
    from app.db.models.user import User, PlanTier, PLAN_LIMITS
    from app.db.models.prospect import Prospect
    from app.db.models.campaign import Campaign
    from app.db.models.lead_package import LeadPackage, PaymentStatus
    
    now = datetime.utcnow()
    first_day_of_month = datetime(now.year, now.month, 1)
    
    # Buscar usuário
    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"Usuário {user_id} não encontrado")
        return False, 0
    
    # Verificar se plano é ilimitado
    plan_limits = PLAN_LIMITS.get(user.plan_tier, PLAN_LIMITS[PlanTier.FREE])
    plan_limit = plan_limits["leads_per_month"]
    
    if plan_limit == -1:
        return True, -1
    
    # Contar leads usados no mês
    campaign_ids = [c.id for c in db_session.query(Campaign.id).filter(Campaign.user_id == user_id).all()]
    
    if not campaign_ids:
        used_this_month = 0
    else:
        used_this_month = db_session.query(func.count(Prospect.id)).filter(
            and_(
                Prospect.campaign_id.in_(campaign_ids),
                Prospect.created_at >= first_day_of_month
            )
        ).scalar() or 0
    
    # Contar leads de pacotes ativos
    package_leads = db_session.query(
        func.sum(LeadPackage.leads_purchased - LeadPackage.leads_used)
    ).filter(
        and_(
            LeadPackage.user_id == user_id,
            LeadPackage.is_active == True,
            LeadPackage.payment_status == PaymentStatus.PAID,
            LeadPackage.leads_used < LeadPackage.leads_purchased
        )
    ).scalar() or 0
    
    total_available = plan_limit + package_leads
    remaining = max(0, total_available - used_this_month)
    
    return remaining > 0, remaining


def sync_pause_user_campaigns(db_session, user_id: int, reason: str = "Limite de leads atingido") -> int:
    """
    Versão síncrona de pause_user_campaigns para uso em Celery tasks.
    """
    from app.db.models.campaign import Campaign, CampaignStatus
    
    campaigns = db_session.query(Campaign).filter(
        and_(
            Campaign.user_id == user_id,
            Campaign.status.in_([CampaignStatus.ACTIVE, CampaignStatus.SCRAPING])
        )
    ).all()
    
    count = 0
    for campaign in campaigns:
        campaign.status = CampaignStatus.PAUSED
        count += 1
        logger.warning(f"Campanha {campaign.id} pausada: {reason}")
    
    if count > 0:
        db_session.commit()
        logger.warning(f"Pausadas {count} campanhas do usuário {user_id}: {reason}")
    
    return count
