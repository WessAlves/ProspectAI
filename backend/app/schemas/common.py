"""
Schemas Pydantic comuns e utilitários.
"""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Parâmetros de paginação."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """Resposta simples com mensagem."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Resposta de erro."""
    detail: str
    error_code: Optional[str] = None
