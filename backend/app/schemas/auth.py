"""
Schemas Pydantic para autenticação.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Schema de resposta do token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema para refresh de token."""
    refresh_token: str


class LoginRequest(BaseModel):
    """Schema de requisição de login."""
    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    """Schema para alteração de senha."""
    current_password: str
    new_password: str
