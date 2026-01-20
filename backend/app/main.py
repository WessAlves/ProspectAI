"""
ProspectAI - SaaS de Prospecção Automatizada
Entry point da aplicação FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.events import create_start_app_handler, create_stop_app_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    await create_start_app_handler()
    yield
    # Shutdown
    await create_stop_app_handler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para automação de prospecção de clientes via Instagram e WhatsApp",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas da API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de health check para monitoramento."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": settings.PROJECT_NAME,
    }


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz com informações básicas da API."""
    return {
        "message": f"Bem-vindo à API do {settings.PROJECT_NAME}",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
    }
