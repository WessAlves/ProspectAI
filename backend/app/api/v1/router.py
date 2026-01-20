"""
Router principal da API v1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, agents, plans, campaigns, prospects, dashboard, scraping, admin, profile, lead_packages, websocket

api_router = APIRouter()

# Incluir rotas de cada módulo
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticação"],
)

api_router.include_router(
    profile.router,
    prefix="/user",
    tags=["Perfil do Usuário"],
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["Agentes LLM"],
)

api_router.include_router(
    plans.router,
    prefix="/plans",
    tags=["Planos de Serviço"],
)

api_router.include_router(
    campaigns.router,
    prefix="/campaigns",
    tags=["Campanhas"],
)

api_router.include_router(
    prospects.router,
    prefix="/prospects",
    tags=["Prospects"],
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)

api_router.include_router(
    scraping.router,
    prefix="/scraping",
    tags=["Scraping"],
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Administração"],
)

api_router.include_router(
    lead_packages.router,
    prefix="/lead-packages",
    tags=["Pacotes de Leads"],
)

# WebSocket para atualizações em tempo real
api_router.include_router(
    websocket.router,
    tags=["WebSocket"],
)
