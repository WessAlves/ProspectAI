"""
Configuração do Celery para tarefas assíncronas.
"""

import os
from celery import Celery

# Usar variável de ambiente REDIS_URL, fallback para localhost
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Criar instância do Celery
celery_app = Celery(
    "prospectai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.scraping",
        "app.tasks.messaging",
        "app.tasks.campaigns",
        "app.tasks.maintenance",
        "app.tasks.continuous_scraping",
    ]
)

# Configurações do Celery
celery_app.conf.update(
    # Serialização
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="America/Sao_Paulo",
    enable_utc=True,
    
    # Resultados
    result_expires=3600,  # 1 hora
    
    # Tarefas
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    
    # Worker
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Conexão com broker - IMPORTANTE para evitar Connection Refused
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_connection_timeout=30,
    
    # Beat schedule para tarefas agendadas
    beat_schedule={
        "check-scheduled-campaigns": {
            "task": "app.tasks.campaigns.check_scheduled_campaigns",
            "schedule": 60.0,  # A cada 1 minuto
        },
        "cleanup-expired-tokens": {
            "task": "app.tasks.maintenance.cleanup_expired_tokens",
            "schedule": 3600.0,  # A cada 1 hora
        },
        # NOTA: O scraping contínuo NÃO precisa de schedule aqui.
        # Ele é iniciado por start_campaign_scraping() quando uma campanha é ativada
        # e se auto-reagenda após cada execução até atingir o limite ou ser pausada.
    },
)

# Autodiscover tasks (opcional)
# celery_app.autodiscover_tasks()
