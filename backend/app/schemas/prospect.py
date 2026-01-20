"""
Schemas Pydantic para Prospect.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.db.models.prospect import ProspectPlatform, ProspectStatus


class ProspectBase(BaseModel):
    """Schema base de prospect."""
    name: Optional[str] = None
    username: str = Field(..., min_length=1, max_length=255)
    platform: ProspectPlatform
    profile_url: Optional[str] = None
    followers_count: Optional[int] = Field(None, ge=0)
    has_website: bool = False
    website_url: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    # Campos para leads manuais
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None


class ProspectCreate(BaseModel):
    """Schema para criação de prospect."""
    campaign_id: Optional[UUID] = None  # Opcional agora
    name: Optional[str] = None
    username: Optional[str] = None  # Será gerado se não fornecido
    platform: ProspectPlatform = ProspectPlatform.MANUAL
    profile_url: Optional[str] = None
    followers_count: Optional[int] = Field(None, ge=0)
    has_website: bool = False
    website_url: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None


class ProspectUpdate(BaseModel):
    """Schema para atualização de prospect."""
    status: Optional[ProspectStatus] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    extra_data: Optional[Dict[str, Any]] = None


class ProspectResponse(ProspectBase):
    """Schema de resposta de prospect."""
    id: UUID
    campaign_id: Optional[UUID]
    status: ProspectStatus
    score: int
    last_post_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProspectBulkCreate(BaseModel):
    """Schema para importação em massa de prospects."""
    prospects: list[ProspectCreate]


class ProspectFilter(BaseModel):
    """Filtros para listagem de prospects."""
    status: Optional[ProspectStatus] = None
    platform: Optional[ProspectPlatform] = None
    min_score: Optional[int] = Field(None, ge=0)
    has_website: Optional[bool] = None
    campaign_id: Optional[UUID] = None
