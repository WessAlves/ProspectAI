"""
Módulo de segurança: JWT, hashing de senhas e verificação.
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


# Contexto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    """Schema do payload do token JWT."""
    sub: str
    exp: datetime
    type: str  # "access" ou "refresh"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera o hash de uma senha."""
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token de acesso JWT.
    
    Args:
        subject: Identificador do usuário (geralmente user_id)
        expires_delta: Tempo de expiração personalizado
    
    Returns:
        Token JWT codificado
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token de refresh JWT.
    
    Args:
        subject: Identificador do usuário (geralmente user_id)
        expires_delta: Tempo de expiração personalizado
    
    Returns:
        Token JWT codificado
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: Token JWT a ser decodificado
    
    Returns:
        TokenPayload se válido, None se inválido
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verifica se o token é válido e retorna o subject.
    
    Args:
        token: Token JWT a ser verificado
        token_type: Tipo esperado ("access" ou "refresh")
    
    Returns:
        Subject (user_id) se válido, None se inválido
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.type != token_type:
        return None
    
    # Comparar com datetime naive (sem timezone)
    now = datetime.utcnow()
    exp_naive = payload.exp.replace(tzinfo=None) if payload.exp.tzinfo else payload.exp
    if exp_naive < now:
        return None
    
    return payload.sub
