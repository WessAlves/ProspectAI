"""
Schemas Pydantic para Agent.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    """Schema base de agente."""
    name: str = Field(..., min_length=1, max_length=255, description="Nome do agente/representante")
    description: Optional[str] = Field(None, description="Descrição do propósito do agente")
    personality: str = Field(..., min_length=10, description="Personalidade e tom de voz do agente")
    communication_style: Optional[str] = Field(None, description="Estilo de comunicação")
    knowledge_base: Optional[str] = Field(None, description="Base de conhecimento sobre produtos/serviços")
    model_name: str = Field(default="gpt-4o-mini", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=500, ge=50, le=4000)


class AgentCreate(AgentBase):
    """Schema para criação de agente."""
    pass


class AgentUpdate(BaseModel):
    """Schema para atualização de agente."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    personality: Optional[str] = Field(None, min_length=10)
    communication_style: Optional[str] = None
    knowledge_base: Optional[str] = None
    model_name: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=50, le=4000)
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    """Schema de resposta de agente."""
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentTestRequest(BaseModel):
    """Schema para teste de geração do agente."""
    prospect_name: str = Field(..., min_length=1)
    prospect_context: Optional[str] = None
    plan_name: Optional[str] = None


class AgentTestResponse(BaseModel):
    """Schema de resposta do teste de geração."""
    generated_message: str
    tokens_used: int
    model_name: str
