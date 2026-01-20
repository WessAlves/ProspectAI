"""
Serviço de notificações em tempo real.

Usa Redis PubSub para comunicar entre Celery workers e o servidor FastAPI.
"""

import json
import asyncio
import logging
from typing import Optional
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Canais Redis para notificações
CHANNEL_SCRAPING = "notifications:scraping"
CHANNEL_LEADS = "notifications:leads"
CHANNEL_USER = "notifications:user:{user_id}"


def get_redis_sync():
    """Obtém conexão Redis síncrona (para uso no Celery)."""
    redis_url = str(settings.REDIS_URL)
    return redis.from_url(redis_url)


def publish_scraping_progress(
    campaign_id: str,
    user_id: str,
    found: int,
    saved: int,
    current_name: str = None,
):
    """Publica progresso do scraping (chamado do Celery worker)."""
    try:
        r = get_redis_sync()
        message = {
            "type": "scraping_progress",
            "campaign_id": campaign_id,
            "user_id": user_id,
            "found": found,
            "saved": saved,
            "current": current_name,
        }
        r.publish(CHANNEL_SCRAPING, json.dumps(message))
        logger.debug(f"Publicado progresso: {found} encontrados, {saved} salvos")
    except Exception as e:
        logger.debug(f"Erro ao publicar progresso: {e}")


def publish_lead_found(
    campaign_id: str,
    user_id: str,
    lead_data: dict,
):
    """Publica quando um novo lead é encontrado (chamado do Celery worker)."""
    try:
        r = get_redis_sync()
        message = {
            "type": "lead_found",
            "campaign_id": campaign_id,
            "user_id": user_id,
            "lead": {
                "name": lead_data.get("name"),
                "phone": lead_data.get("phone"),
                "website": lead_data.get("website"),
                "email": lead_data.get("email"),
                "category": lead_data.get("category"),
                "rating": lead_data.get("rating"),
            },
        }
        r.publish(CHANNEL_LEADS, json.dumps(message))
    except Exception as e:
        logger.debug(f"Erro ao publicar lead: {e}")


def publish_scraping_completed(
    campaign_id: str,
    user_id: str,
    total_found: int,
    total_saved: int,
    duration_seconds: float,
):
    """Publica quando o scraping é concluído (chamado do Celery worker)."""
    try:
        r = get_redis_sync()
        message = {
            "type": "scraping_completed",
            "campaign_id": campaign_id,
            "user_id": user_id,
            "total_found": total_found,
            "total_saved": total_saved,
            "duration_seconds": duration_seconds,
        }
        r.publish(CHANNEL_SCRAPING, json.dumps(message))
        logger.info(f"Scraping concluído: {total_found} encontrados, {total_saved} salvos")
    except Exception as e:
        logger.debug(f"Erro ao publicar conclusão: {e}")


def publish_scraping_error(
    campaign_id: str,
    user_id: str,
    error_message: str,
):
    """Publica quando ocorre erro no scraping (chamado do Celery worker)."""
    try:
        r = get_redis_sync()
        message = {
            "type": "scraping_error",
            "campaign_id": campaign_id,
            "user_id": user_id,
            "error": error_message,
        }
        r.publish(CHANNEL_SCRAPING, json.dumps(message))
    except Exception as e:
        logger.debug(f"Erro ao publicar erro: {e}")


def publish_limit_reached(
    user_id: str,
    campaign_id: str = None,
):
    """Publica quando o limite de leads é atingido (chamado do Celery worker)."""
    try:
        r = get_redis_sync()
        message = {
            "type": "limit_reached",
            "campaign_id": campaign_id,
            "user_id": user_id,
            "message": "Limite de leads atingido",
        }
        r.publish(CHANNEL_USER.format(user_id=user_id), json.dumps(message))
    except Exception as e:
        logger.debug(f"Erro ao publicar limite: {e}")
