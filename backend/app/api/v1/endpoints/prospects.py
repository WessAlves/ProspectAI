"""
Endpoints de Prospects.
"""

import csv
import io
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.campaign import Campaign
from app.db.models.prospect import Prospect, ProspectStatus, ProspectPlatform
from app.schemas.prospect import ProspectResponse, ProspectUpdate, ProspectCreate, ProspectBulkCreate
from app.schemas.common import PaginatedResponse, MessageResponse
from app.dependencies import get_current_user, get_pagination_params

router = APIRouter()


@router.get("", response_model=List[ProspectResponse])
async def list_prospects(
    campaign_id: Optional[UUID] = None,
    status_filter: Optional[ProspectStatus] = None,
    platform: Optional[ProspectPlatform] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    has_website: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    """
    Lista prospects com filtros.
    
    - **campaign_id**: Filtrar por campanha
    - **status_filter**: Filtrar por status
    - **platform**: Filtrar por plataforma
    - **min_score**: Score mínimo de qualificação
    - **has_website**: Filtrar por presença de website
    - **search**: Buscar por nome, email, empresa ou username
    """
    # Verificar campanhas do usuário
    campaigns_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    user_campaign_ids = [c[0] for c in campaigns_result.fetchall()]
    
    # Incluir prospects sem campanha (cadastro manual) ou de campanhas do usuário
    query = select(Prospect).where(
        or_(
            Prospect.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False,
            Prospect.campaign_id.is_(None)
        )
    )
    
    if campaign_id:
        if campaign_id not in user_campaign_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
        query = select(Prospect).where(Prospect.campaign_id == campaign_id)
    
    if status_filter:
        query = query.where(Prospect.status == status_filter)
    
    if platform:
        query = query.where(Prospect.platform == platform)
    
    if min_score is not None:
        query = query.where(Prospect.score >= min_score)
    
    if has_website is not None:
        query = query.where(Prospect.has_website == has_website)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Prospect.name.ilike(search_term),
                Prospect.email.ilike(search_term),
                Prospect.company.ilike(search_term),
                Prospect.username.ilike(search_term),
            )
        )
    
    query = query.offset(pagination["offset"]).limit(pagination["page_size"]).order_by(Prospect.created_at.desc())
    
    result = await db.execute(query)
    prospects = result.scalars().all()
    
    return prospects


@router.post("", response_model=ProspectResponse, status_code=status.HTTP_201_CREATED)
async def create_prospect(
    prospect_data: ProspectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria um novo prospect/lead manualmente.
    """
    # Se campaign_id fornecido, verificar se pertence ao usuário
    if prospect_data.campaign_id:
        campaign_result = await db.execute(
            select(Campaign).where(
                Campaign.id == prospect_data.campaign_id,
                Campaign.user_id == current_user.id
            )
        )
        if not campaign_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
    
    # Gerar username se não fornecido
    username = prospect_data.username
    if not username:
        if prospect_data.email:
            username = prospect_data.email.split('@')[0]
        elif prospect_data.name:
            username = prospect_data.name.lower().replace(' ', '_')
        else:
            username = f"lead_{uuid4().hex[:8]}"
    
    prospect = Prospect(
        campaign_id=prospect_data.campaign_id,
        name=prospect_data.name,
        username=username,
        platform=prospect_data.platform,
        profile_url=prospect_data.profile_url,
        followers_count=prospect_data.followers_count,
        has_website=prospect_data.has_website,
        website_url=prospect_data.website_url,
        extra_data=prospect_data.extra_data,
        email=prospect_data.email,
        phone=prospect_data.phone,
        company=prospect_data.company,
        position=prospect_data.position,
        status=ProspectStatus.FOUND,
        score=0,
    )
    
    db.add(prospect)
    await db.commit()
    await db.refresh(prospect)
    
    return prospect


@router.post("/bulk", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_prospects_bulk(
    data: ProspectBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importa múltiplos prospects/leads de uma vez.
    """
    created = 0
    errors = []
    
    for idx, prospect_data in enumerate(data.prospects):
        try:
            # Se campaign_id fornecido, verificar se pertence ao usuário
            if prospect_data.campaign_id:
                campaign_result = await db.execute(
                    select(Campaign).where(
                        Campaign.id == prospect_data.campaign_id,
                        Campaign.user_id == current_user.id
                    )
                )
                if not campaign_result.scalar_one_or_none():
                    errors.append({"row": idx + 1, "error": "Campanha não encontrada"})
                    continue
            
            # Gerar username se não fornecido
            username = prospect_data.username
            if not username:
                if prospect_data.email:
                    username = prospect_data.email.split('@')[0]
                elif prospect_data.name:
                    username = prospect_data.name.lower().replace(' ', '_')
                else:
                    username = f"lead_{uuid4().hex[:8]}"
            
            prospect = Prospect(
                campaign_id=prospect_data.campaign_id,
                name=prospect_data.name,
                username=username,
                platform=prospect_data.platform or ProspectPlatform.IMPORT,
                profile_url=prospect_data.profile_url,
                followers_count=prospect_data.followers_count,
                has_website=prospect_data.has_website,
                website_url=prospect_data.website_url,
                extra_data=prospect_data.extra_data,
                email=prospect_data.email,
                phone=prospect_data.phone,
                company=prospect_data.company,
                position=prospect_data.position,
                status=ProspectStatus.FOUND,
                score=0,
            )
            
            db.add(prospect)
            created += 1
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)})
    
    await db.commit()
    
    return {
        "created": created,
        "errors": errors,
        "total": len(data.prospects),
    }


@router.delete("/{prospect_id}", response_model=MessageResponse)
async def delete_prospect(
    prospect_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exclui um prospect.
    """
    # Verificar campanhas do usuário
    campaigns_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    user_campaign_ids = [c[0] for c in campaigns_result.fetchall()]
    
    result = await db.execute(
        select(Prospect)
        .where(
            Prospect.id == prospect_id,
            or_(
                Prospect.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False,
                Prospect.campaign_id.is_(None)
            )
        )
    )
    prospect = result.scalar_one_or_none()
    
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospect não encontrado",
        )
    
    await db.delete(prospect)
    await db.commit()
    
    return {"message": "Lead excluído com sucesso"}


@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(
    prospect_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os detalhes de um prospect específico.
    """
    # Verificar campanhas do usuário
    campaigns_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    user_campaign_ids = [c[0] for c in campaigns_result.fetchall()]
    
    result = await db.execute(
        select(Prospect)
        .where(
            Prospect.id == prospect_id,
            Prospect.campaign_id.in_(user_campaign_ids)
        )
    )
    prospect = result.scalar_one_or_none()
    
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospect não encontrado",
        )
    
    return prospect


@router.patch("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: UUID,
    prospect_data: ProspectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza o status ou score de um prospect.
    """
    # Verificar campanhas do usuário
    campaigns_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    user_campaign_ids = [c[0] for c in campaigns_result.fetchall()]
    
    result = await db.execute(
        select(Prospect)
        .where(
            Prospect.id == prospect_id,
            Prospect.campaign_id.in_(user_campaign_ids)
        )
    )
    prospect = result.scalar_one_or_none()
    
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospect não encontrado",
        )
    
    # Atualizar campos fornecidos
    update_data = prospect_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prospect, field, value)
    
    await db.commit()
    await db.refresh(prospect)
    
    return prospect


@router.get("/stats/summary")
async def get_prospects_summary(
    campaign_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna um resumo estatístico dos prospects.
    """
    # Verificar campanhas do usuário
    campaigns_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    user_campaign_ids = [c[0] for c in campaigns_result.fetchall()]
    
    if not user_campaign_ids:
        return {
            "total": 0,
            "by_status": {},
            "by_platform": {},
        }
    
    base_filter = Prospect.campaign_id.in_(user_campaign_ids)
    if campaign_id:
        if campaign_id not in user_campaign_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
        base_filter = Prospect.campaign_id == campaign_id
    
    # Total
    total_result = await db.execute(
        select(func.count(Prospect.id)).where(base_filter)
    )
    total = total_result.scalar()
    
    # Por status
    status_result = await db.execute(
        select(Prospect.status, func.count(Prospect.id))
        .where(base_filter)
        .group_by(Prospect.status)
    )
    by_status = {status.value: count for status, count in status_result.fetchall()}
    
    # Por plataforma
    platform_result = await db.execute(
        select(Prospect.platform, func.count(Prospect.id))
        .where(base_filter)
        .group_by(Prospect.platform)
    )
    by_platform = {platform.value: count for platform, count in platform_result.fetchall()}
    
    return {
        "total": total,
        "by_status": by_status,
        "by_platform": by_platform,
    }


@router.post("/import/csv", response_model=dict)
async def import_prospects_csv(
    file: UploadFile = File(..., description="Arquivo CSV com prospects"),
    campaign_id: Optional[UUID] = Form(None, description="ID da campanha para associar"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importa prospects/leads a partir de um arquivo CSV.
    
    O CSV deve ter as seguintes colunas (cabeçalho):
    - name: Nome do lead (obrigatório)
    - email: Email do lead
    - phone: Telefone
    - company: Empresa
    - position: Cargo
    - website_url: URL do site
    - profile_url: URL do perfil em rede social
    - platform: Plataforma (instagram, google, manual, import)
    
    Exemplo de CSV:
    ```
    name,email,phone,company,position,website_url
    João Silva,joao@empresa.com,(11) 99999-9999,Empresa X,Diretor,https://empresax.com
    Maria Santos,maria@email.com,(11) 88888-8888,Empresa Y,Gerente,
    ```
    """
    # Verificar tipo de arquivo
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve ser um CSV",
        )
    
    # Verificar campanha se fornecida
    if campaign_id:
        campaign_result = await db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.user_id == current_user.id
            )
        )
        if not campaign_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
    
    # Ler e processar CSV
    try:
        content = await file.read()
        # Tentar decodificar com diferentes encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                decoded_content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível decodificar o arquivo. Use encoding UTF-8.",
            )
        
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        # Verificar se tem cabeçalho válido
        if not csv_reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo CSV vazio ou sem cabeçalho",
            )
        
        # Mapear colunas (case insensitive)
        field_map = {}
        valid_fields = ['name', 'email', 'phone', 'company', 'position', 'website_url', 'profile_url', 'platform', 'username']
        for field in csv_reader.fieldnames:
            field_lower = field.lower().strip()
            # Tratar variações comuns
            if field_lower in ['nome', 'name']:
                field_map[field] = 'name'
            elif field_lower in ['email', 'e-mail', 'e_mail']:
                field_map[field] = 'email'
            elif field_lower in ['phone', 'telefone', 'tel', 'celular', 'whatsapp']:
                field_map[field] = 'phone'
            elif field_lower in ['company', 'empresa', 'companhia', 'organization']:
                field_map[field] = 'company'
            elif field_lower in ['position', 'cargo', 'titulo', 'title', 'job', 'job_title']:
                field_map[field] = 'position'
            elif field_lower in ['website', 'website_url', 'site', 'url']:
                field_map[field] = 'website_url'
            elif field_lower in ['profile_url', 'perfil', 'social', 'instagram', 'linkedin']:
                field_map[field] = 'profile_url'
            elif field_lower in ['platform', 'plataforma', 'fonte', 'source']:
                field_map[field] = 'platform'
            elif field_lower in ['username', 'usuario', 'user']:
                field_map[field] = 'username'
        
        created = 0
        skipped = 0
        errors = []
        
        for row_idx, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
            try:
                # Mapear dados
                data = {}
                for csv_field, mapped_field in field_map.items():
                    value = row.get(csv_field, '').strip()
                    if value:
                        data[mapped_field] = value
                
                # Verificar se tem pelo menos nome ou email
                if not data.get('name') and not data.get('email'):
                    skipped += 1
                    continue
                
                # Gerar nome se não tiver
                if not data.get('name') and data.get('email'):
                    data['name'] = data['email'].split('@')[0].replace('.', ' ').title()
                
                # Gerar username
                username = data.get('username')
                if not username:
                    if data.get('email'):
                        username = data['email'].split('@')[0]
                    elif data.get('name'):
                        username = data['name'].lower().replace(' ', '_')
                    else:
                        username = f"lead_{uuid4().hex[:8]}"
                
                # Determinar plataforma
                platform_str = data.get('platform', 'import').lower()
                try:
                    platform = ProspectPlatform(platform_str)
                except ValueError:
                    platform = ProspectPlatform.IMPORT
                
                # Determinar se tem website
                has_website = bool(data.get('website_url'))
                
                # Criar prospect
                prospect = Prospect(
                    campaign_id=campaign_id,
                    name=data.get('name', ''),
                    username=username,
                    platform=platform,
                    profile_url=data.get('profile_url'),
                    has_website=has_website,
                    website_url=data.get('website_url'),
                    email=data.get('email'),
                    phone=data.get('phone'),
                    company=data.get('company'),
                    position=data.get('position'),
                    status=ProspectStatus.FOUND,
                    score=0,
                )
                
                db.add(prospect)
                created += 1
                
            except Exception as e:
                errors.append({"row": row_idx, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Importação concluída: {created} leads criados",
            "created": created,
            "skipped": skipped,
            "errors": errors[:20],  # Limitar erros retornados
            "total_errors": len(errors),
        }
        
    except csv.Error as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar CSV: {str(e)}",
        )


@router.delete("/bulk", response_model=MessageResponse)
async def delete_prospects_bulk(
    prospect_ids: List[UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exclui múltiplos prospects de uma vez.
    """
    # Verificar campanhas do usuário
    campaigns_result = await db.execute(
        select(Campaign.id).where(Campaign.user_id == current_user.id)
    )
    user_campaign_ids = [c[0] for c in campaigns_result.fetchall()]
    
    deleted = 0
    for prospect_id in prospect_ids:
        result = await db.execute(
            select(Prospect)
            .where(
                Prospect.id == prospect_id,
                or_(
                    Prospect.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False,
                    Prospect.campaign_id.is_(None)
                )
            )
        )
        prospect = result.scalar_one_or_none()
        
        if prospect:
            await db.delete(prospect)
            deleted += 1
    
    await db.commit()
    
    return {"message": f"{deleted} leads excluídos com sucesso"}
