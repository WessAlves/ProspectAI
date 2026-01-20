"""
Schemas Pydantic para ServicePlan.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field


class ServicePlanBase(BaseModel):
    """Schema base de plano de serviço."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    features: List[str] = Field(default_factory=list)


class ServicePlanCreate(ServicePlanBase):
    """Schema para criação de plano de serviço."""
    pass


class ServicePlanUpdate(BaseModel):
    """Schema para atualização de plano de serviço."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    features: Optional[List[str]] = None


class ServicePlanResponse(ServicePlanBase):
    """Schema de resposta de plano de serviço."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
