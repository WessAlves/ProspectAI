"""
Endpoints de Scraping.

Endpoints para iniciar e monitorar tarefas de scraping.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.campaign import Campaign
from app.dependencies import get_current_user
from app.tasks.scraping import (
    scrape_google_maps,
    scrape_google_search,
    scrape_instagram,
    scrape_instagram_profile,
    scrape_instagram_hashtag,
    batch_scrape_prospects,
    extract_website_contacts,
)

router = APIRouter()


# Schemas
class ScrapeRequest(BaseModel):
    """Request para iniciar scraping."""
    query: str = Field(..., description="Termo de busca", min_length=2, max_length=200)
    location: str = Field(..., description="Localização", min_length=2, max_length=200)
    source: str = Field(
        default="google_maps",
        description="Fonte do scraping",
        pattern="^(google|google_maps|instagram)$"
    )
    limit: int = Field(default=50, ge=10, le=500, description="Limite de resultados")
    campaign_id: Optional[UUID] = Field(None, description="ID da campanha para associar prospects")
    extract_contacts: bool = Field(
        default=False,
        description="Extrair contatos dos sites (apenas para Google Search)"
    )


class InstagramScrapeRequest(BaseModel):
    """Request para scraping no Instagram."""
    query: str = Field(..., description="Termo de busca ou hashtag", min_length=2, max_length=100)
    location: str = Field(default="", description="Localização (para contexto)")
    limit: int = Field(default=30, ge=5, le=100, description="Limite de resultados")
    campaign_id: Optional[UUID] = Field(None, description="ID da campanha")


class InstagramProfileRequest(BaseModel):
    """Request para extrair perfil do Instagram."""
    username: str = Field(..., description="Nome de usuário (sem @)", min_length=1, max_length=30)


class InstagramHashtagRequest(BaseModel):
    """Request para buscar por hashtag no Instagram."""
    hashtag: str = Field(..., description="Hashtag (sem #)", min_length=1, max_length=100)
    limit: int = Field(default=30, ge=5, le=100, description="Limite de perfis")
    campaign_id: Optional[UUID] = Field(None, description="ID da campanha")


class BatchScrapeRequest(BaseModel):
    """Request para scraping em múltiplas fontes."""
    query: str = Field(..., description="Termo de busca", min_length=2, max_length=200)
    location: str = Field(..., description="Localização", min_length=2, max_length=200)
    sources: List[str] = Field(
        default=["google", "google_maps", "instagram"],
        description="Fontes de scraping"
    )
    limit_per_source: int = Field(default=30, ge=10, le=200, description="Limite por fonte")
    campaign_id: Optional[UUID] = Field(None, description="ID da campanha")


class ExtractContactsRequest(BaseModel):
    """Request para extrair contatos de um website."""
    website_url: str = Field(..., description="URL do website")


class ScrapeResponse(BaseModel):
    """Response de tarefa de scraping iniciada."""
    task_id: str
    status: str
    message: str
    query: str
    location: str
    source: Optional[str] = None
    sources: Optional[List[str]] = None


class TaskStatusResponse(BaseModel):
    """Response de status de tarefa."""
    task_id: str
    status: str
    result: Optional[dict] = None

@router.post("/google-maps", response_model=ScrapeResponse)
async def start_google_maps_scrape(
    request: ScrapeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia scraping no Google Maps.
    
    Busca empresas no Google Maps baseado na query e localização.
    Os resultados podem ser associados a uma campanha.
    """
    # Validar campanha se fornecida
    if request.campaign_id:
        campaign_result = await db.execute(
            select(Campaign).where(
                Campaign.id == request.campaign_id,
                Campaign.user_id == current_user.id,
            )
        )
        campaign = campaign_result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
    
    # Iniciar task assíncrona
    task = scrape_google_maps.delay(
        query=request.query,
        location=request.location,
        limit=request.limit,
        campaign_id=str(request.campaign_id) if request.campaign_id else None,
        save_progressive=True,
        detailed_mode=True,  # Extrair telefone/website
        extract_emails=False,  # Não extrair emails por padrão
    )
    
    return ScrapeResponse(
        task_id=task.id,
        status="dispatched",
        message="Scraping do Google Maps iniciado",
        query=request.query,
        location=request.location,
        source="google_maps",
    )


@router.post("/google-search", response_model=ScrapeResponse)
async def start_google_search_scrape(
    request: ScrapeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia scraping no Google Search.
    
    Busca sites nos resultados do Google e opcionalmente extrai contatos.
    """
    # Validar campanha se fornecida
    if request.campaign_id:
        campaign_result = await db.execute(
            select(Campaign).where(
                Campaign.id == request.campaign_id,
                Campaign.user_id == current_user.id,
            )
        )
        campaign = campaign_result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
    
    # Iniciar task assíncrona
    task = scrape_google_search.delay(
        query=request.query,
        location=request.location,
        limit=request.limit,
        extract_contacts=request.extract_contacts,
        campaign_id=str(request.campaign_id) if request.campaign_id else None,
    )
    
    return ScrapeResponse(
        task_id=task.id,
        status="dispatched",
        message="Scraping do Google Search iniciado",
        query=request.query,
        location=request.location,
        source="google",
    )


@router.post("/batch", response_model=ScrapeResponse)
async def start_batch_scrape(
    request: BatchScrapeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia scraping em múltiplas fontes.
    
    Dispara tasks de scraping para todas as fontes especificadas.
    """
    # Validar fontes
    valid_sources = {"google", "google_maps", "instagram"}
    for source in request.sources:
        if source not in valid_sources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fonte inválida: {source}. Use: {valid_sources}",
            )
    
    # Validar campanha se fornecida
    if request.campaign_id:
        campaign_result = await db.execute(
            select(Campaign).where(
                Campaign.id == request.campaign_id,
                Campaign.user_id == current_user.id,
            )
        )
        campaign = campaign_result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
    
    # Iniciar batch
    task = batch_scrape_prospects.delay(
        sources=request.sources,
        query=request.query,
        location=request.location,
        limit_per_source=request.limit_per_source,
        campaign_id=str(request.campaign_id) if request.campaign_id else None,
    )
    
    return ScrapeResponse(
        task_id=task.id,
        status="dispatched",
        message=f"Batch scraping iniciado em {len(request.sources)} fontes",
        query=request.query,
        location=request.location,
        sources=request.sources,
    )


# ===== INSTAGRAM ENDPOINTS =====

@router.post("/instagram", response_model=ScrapeResponse)
async def start_instagram_scrape(
    request: InstagramScrapeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia scraping no Instagram.
    
    Busca perfis de negócios por termo de busca ou hashtag.
    O Instagram tem proteções robustas, então use com moderação.
    """
    # Validar campanha se fornecida
    if request.campaign_id:
        campaign_result = await db.execute(
            select(Campaign).where(
                Campaign.id == request.campaign_id,
                Campaign.user_id == current_user.id,
            )
        )
        campaign = campaign_result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
    
    # Iniciar task assíncrona
    task = scrape_instagram.delay(
        query=request.query,
        location=request.location,
        limit=request.limit,
        campaign_id=str(request.campaign_id) if request.campaign_id else None,
    )
    
    return ScrapeResponse(
        task_id=task.id,
        status="dispatched",
        message="Scraping do Instagram iniciado",
        query=request.query,
        location=request.location,
        source="instagram",
    )


@router.post("/instagram/profile")
async def get_instagram_profile(
    request: InstagramProfileRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Extrai dados de um perfil específico do Instagram.
    
    Retorna informações como nome, bio, website, seguidores, etc.
    """
    # Remover @ se presente
    username = request.username.lstrip('@')
    
    task = scrape_instagram_profile.delay(username=username)
    
    return {
        "task_id": task.id,
        "status": "dispatched",
        "message": f"Extração do perfil @{username} iniciada",
        "username": username,
    }


@router.post("/instagram/hashtag")
async def search_instagram_hashtag(
    request: InstagramHashtagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Busca perfis de negócios por hashtag no Instagram.
    
    Extrai perfis dos autores de posts com a hashtag especificada.
    """
    # Remover # se presente
    hashtag = request.hashtag.lstrip('#')
    
    # Validar campanha se fornecida
    if request.campaign_id:
        campaign_result = await db.execute(
            select(Campaign).where(
                Campaign.id == request.campaign_id,
                Campaign.user_id == current_user.id,
            )
        )
        campaign = campaign_result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
    
    task = scrape_instagram_hashtag.delay(
        hashtag=hashtag,
        limit=request.limit,
        campaign_id=str(request.campaign_id) if request.campaign_id else None,
    )
    
    return {
        "task_id": task.id,
        "status": "dispatched",
        "message": f"Busca por #{hashtag} iniciada",
        "hashtag": hashtag,
    }


# ===== OUTROS ENDPOINTS =====

@router.post("/extract-contacts")
async def extract_contacts(
    request: ExtractContactsRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Extrai informações de contato de um website.
    
    Busca emails, telefones e redes sociais no site.
    """
    task = extract_website_contacts.delay(
        website_url=request.website_url,
    )
    
    return {
        "task_id": task.id,
        "status": "dispatched",
        "message": f"Extração de contatos iniciada para {request.website_url}",
    }


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Verifica o status de uma tarefa de scraping.
    """
    from celery.result import AsyncResult
    from app.celery_app import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "result": None,
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.get()
        elif result.failed():
            response["result"] = {"error": str(result.result)}
    
    return response
