"""
Endpoints de Agentes LLM.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentTestRequest, AgentTestResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.dependencies import get_current_user, get_pagination_params

router = APIRouter()


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria um novo agente (representante virtual) para prospecção.
    
    - **name**: Nome do agente/representante
    - **description**: Descrição do propósito do agente
    - **personality**: Personalidade e tom de voz
    - **communication_style**: Estilo de comunicação
    - **knowledge_base**: Base de conhecimento sobre produtos/serviços
    - **model_name**: Modelo LLM (default: gpt-4o-mini)
    - **temperature**: Criatividade das respostas (0.0 - 2.0)
    - **max_tokens**: Máximo de tokens na resposta
    """
    agent = Agent(
        user_id=current_user.id,
        name=agent_data.name,
        description=agent_data.description,
        personality=agent_data.personality,
        communication_style=agent_data.communication_style,
        knowledge_base=agent_data.knowledge_base,
        model_name=agent_data.model_name,
        temperature=agent_data.temperature,
        max_tokens=agent_data.max_tokens,
    )
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    return agent


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
):
    """
    Lista todos os agentes do usuário.
    """
    result = await db.execute(
        select(Agent)
        .where(Agent.user_id == current_user.id)
        .offset(pagination["offset"])
        .limit(pagination["page_size"])
        .order_by(Agent.created_at.desc())
    )
    agents = result.scalars().all()
    
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os detalhes de um agente específico.
    """
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado",
        )
    
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza um agente existente.
    """
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado",
        )
    
    # Atualizar campos fornecidos
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    await db.commit()
    await db.refresh(agent)
    
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def patch_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza parcialmente um agente (útil para toggle de status).
    """
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado",
        )
    
    # Atualizar campos fornecidos
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    await db.commit()
    await db.refresh(agent)
    
    return agent


@router.delete("/{agent_id}", response_model=MessageResponse)
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deleta um agente.
    """
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado",
        )
    
    await db.delete(agent)
    await db.commit()
    
    return MessageResponse(message="Agente deletado com sucesso")


@router.post("/{agent_id}/test", response_model=AgentTestResponse)
async def test_agent(
    agent_id: UUID,
    test_data: AgentTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Testa a geração de mensagem do agente.
    
    - **prospect_name**: Nome do prospect para teste
    - **prospect_context**: Contexto adicional do prospect
    - **plan_name**: Nome do plano a ser oferecido
    """
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado",
        )
    
    # TODO: Integrar com OpenAI API
    # Por enquanto, retornar mensagem de exemplo
    generated_message = f"""Olá {test_data.prospect_name}!

Vi seu perfil e achei muito interessante seu trabalho. {test_data.prospect_context or ''}

Gostaria de apresentar nosso serviço {test_data.plan_name or 'exclusivo'} que pode ajudar você a alcançar novos patamares.

Posso te contar mais sobre isso?"""

    return AgentTestResponse(
        generated_message=generated_message,
        tokens_used=len(generated_message.split()) * 2,  # Estimativa
        model_name=agent.model_name,
    )
