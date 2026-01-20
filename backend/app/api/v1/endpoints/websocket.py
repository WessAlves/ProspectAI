"""
WebSocket endpoints para atualizações em tempo real.

Permite que o frontend receba atualizações de:
- Progresso do scraping
- Novos leads encontrados
- Status de campanhas
"""

import asyncio
import json
import logging
from typing import Dict, Set
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import jwt, JWTError
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Canais Redis
CHANNEL_SCRAPING = "notifications:scraping"
CHANNEL_LEADS = "notifications:leads"


class ConnectionManager:
    """Gerencia conexões WebSocket por usuário e campanha."""
    
    def __init__(self):
        # Conexões por usuário: {user_id: {websocket1, websocket2, ...}}
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Conexões por campanha: {campaign_id: {websocket1, websocket2, ...}}
        self.campaign_connections: Dict[str, Set[WebSocket]] = {}
        # Mapeamento websocket -> user_id
        self.websocket_users: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, campaign_id: str = None):
        """Conecta um websocket para um usuário e opcionalmente uma campanha."""
        await websocket.accept()
        
        # Adicionar à lista do usuário
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        self.websocket_users[websocket] = user_id
        
        # Adicionar à lista da campanha se fornecida
        if campaign_id:
            if campaign_id not in self.campaign_connections:
                self.campaign_connections[campaign_id] = set()
            self.campaign_connections[campaign_id].add(websocket)
        
        logger.info(f"WebSocket conectado: user={user_id}, campaign={campaign_id}")
    
    def disconnect(self, websocket: WebSocket, campaign_id: str = None):
        """Desconecta um websocket."""
        user_id = self.websocket_users.get(websocket)
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        if campaign_id and campaign_id in self.campaign_connections:
            self.campaign_connections[campaign_id].discard(websocket)
            if not self.campaign_connections[campaign_id]:
                del self.campaign_connections[campaign_id]
        
        if websocket in self.websocket_users:
            del self.websocket_users[websocket]
        
        logger.info(f"WebSocket desconectado: user={user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Envia mensagem para todas as conexões de um usuário."""
        if user_id in self.user_connections:
            dead_connections = set()
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.debug(f"Erro ao enviar para websocket: {e}")
                    dead_connections.add(websocket)
            
            # Limpar conexões mortas
            for ws in dead_connections:
                self.disconnect(ws)
    
    async def send_to_campaign(self, campaign_id: str, message: dict):
        """Envia mensagem para todas as conexões monitorando uma campanha."""
        if campaign_id in self.campaign_connections:
            dead_connections = set()
            for websocket in self.campaign_connections[campaign_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.debug(f"Erro ao enviar para websocket: {e}")
                    dead_connections.add(websocket)
            
            # Limpar conexões mortas
            for ws in dead_connections:
                self.disconnect(ws, campaign_id)


# Instância global do gerenciador de conexões
manager = ConnectionManager()


def verify_ws_token(token: str) -> str:
    """Verifica o token JWT e retorna o user_id."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


@router.websocket("/ws/scraping/{campaign_id}")
async def websocket_scraping(
    websocket: WebSocket,
    campaign_id: str,
    token: str = Query(...),
):
    """
    WebSocket para acompanhar o progresso do scraping de uma campanha.
    
    Conecte com: ws://localhost:8000/api/v1/ws/scraping/{campaign_id}?token={jwt_token}
    
    Mensagens recebidas:
    - {"type": "scraping_progress", "found": 10, "saved": 8, "current": "Nome do Negócio"}
    - {"type": "lead_found", "lead": {...dados do lead...}}
    - {"type": "scraping_completed", "total_found": 50, "total_saved": 45, "duration_seconds": 120}
    - {"type": "scraping_error", "error": "Erro..."}
    """
    # Verificar token
    user_id = verify_ws_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Token inválido")
        return
    
    await manager.connect(websocket, user_id, campaign_id)
    
    # Criar conexão Redis para subscribe
    redis_client = None
    pubsub = None
    listen_task = None
    
    try:
        # Conectar ao Redis
        redis_client = aioredis.from_url(str(settings.REDIS_URL))
        pubsub = redis_client.pubsub()
        
        # Subscrever nos canais de notificação
        await pubsub.subscribe(CHANNEL_SCRAPING, CHANNEL_LEADS)
        
        # Enviar confirmação de conexão
        await websocket.send_json({
            "type": "connected",
            "campaign_id": campaign_id,
            "message": "Conectado ao monitoramento de scraping"
        })
        
        async def listen_redis():
            """Task para escutar mensagens do Redis."""
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            # Filtrar mensagens apenas para esta campanha/usuário
                            if data.get("campaign_id") == campaign_id or data.get("user_id") == user_id:
                                await websocket.send_json(data)
                        except json.JSONDecodeError:
                            pass
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.debug(f"Erro no listener Redis: {e}")
        
        # Iniciar task de escuta do Redis
        listen_task = asyncio.create_task(listen_redis())
        
        # Loop principal - mantém conexão e processa mensagens do cliente
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                # Enviar ping para manter conexão viva
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"Cliente desconectou: campaign={campaign_id}")
    except Exception as e:
        logger.error(f"Erro no websocket: {e}")
    finally:
        # Cancelar task de escuta
        if listen_task:
            listen_task.cancel()
            try:
                await listen_task
            except asyncio.CancelledError:
                pass
        
        # Fechar pubsub e redis
        if pubsub:
            await pubsub.unsubscribe(CHANNEL_SCRAPING, CHANNEL_LEADS)
            await pubsub.close()
        if redis_client:
            await redis_client.close()
        
        manager.disconnect(websocket, campaign_id)


@router.websocket("/ws/user")
async def websocket_user(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket para receber todas as atualizações do usuário.
    
    Conecte com: ws://localhost:8000/api/v1/ws/user?token={jwt_token}
    
    Recebe atualizações de:
    - Progresso de scraping de todas as campanhas
    - Novos leads encontrados
    - Alterações de status de campanhas
    """
    # Verificar token
    user_id = verify_ws_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Token inválido")
        return
    
    await manager.connect(websocket, user_id)
    
    # Criar conexão Redis para subscribe
    redis_client = None
    pubsub = None
    listen_task = None
    
    try:
        # Conectar ao Redis
        redis_client = aioredis.from_url(str(settings.REDIS_URL))
        pubsub = redis_client.pubsub()
        
        # Subscrever nos canais de notificação
        user_channel = f"notifications:user:{user_id}"
        await pubsub.subscribe(CHANNEL_SCRAPING, CHANNEL_LEADS, user_channel)
        
        await websocket.send_json({
            "type": "connected",
            "message": "Conectado ao canal de atualizações"
        })
        
        async def listen_redis():
            """Task para escutar mensagens do Redis."""
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            # Filtrar mensagens apenas para este usuário
                            if data.get("user_id") == user_id:
                                await websocket.send_json(data)
                        except json.JSONDecodeError:
                            pass
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.debug(f"Erro no listener Redis: {e}")
        
        # Iniciar task de escuta do Redis
        listen_task = asyncio.create_task(listen_redis())
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"Cliente desconectou: user={user_id}")
    except Exception as e:
        logger.error(f"Erro no websocket: {e}")
    finally:
        # Cancelar task de escuta
        if listen_task:
            listen_task.cancel()
            try:
                await listen_task
            except asyncio.CancelledError:
                pass
        
        # Fechar pubsub e redis
        if pubsub:
            await pubsub.unsubscribe()
            await pubsub.close()
        if redis_client:
            await redis_client.close()
        
        manager.disconnect(websocket)
