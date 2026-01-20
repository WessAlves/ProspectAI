"""
Eventos de startup e shutdown da aplicação.
"""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def create_start_app_handler():
    """Handler executado na inicialização da aplicação."""
    logger.info(f"Iniciando {settings.PROJECT_NAME}...")
    logger.info(f"Documentação disponível em: {settings.API_V1_STR}/docs")
    # Aqui podemos inicializar conexões, caches, etc.


async def create_stop_app_handler():
    """Handler executado no encerramento da aplicação."""
    logger.info(f"Encerrando {settings.PROJECT_NAME}...")
    # Aqui podemos fechar conexões, limpar recursos, etc.
