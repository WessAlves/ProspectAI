"""
Modelo de Agente LLM.
"""

from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Agent(BaseModel):
    """
    Modelo de agente LLM para geração de mensagens de prospecção.
    
    O agente representa um "representante virtual" da empresa do usuário,
    que irá se comunicar com os prospects durante a prospecção.
    
    Attributes:
        user_id: ID do usuário proprietário
        name: Nome do agente (ex: "João - Consultor de Vendas")
        description: Descrição do propósito do agente
        personality: Personalidade e tom de voz do agente
        communication_style: Estilo de comunicação (formal, informal, etc)
        knowledge_base: Base de conhecimento sobre produtos/serviços
        model_name: Nome do modelo LLM (ex: gpt-4o-mini)
        temperature: Temperatura para geração (0.0 - 2.0)
        max_tokens: Máximo de tokens na resposta
        is_active: Se o agente está ativo
    """
    
    __tablename__ = "agents"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    personality = Column(Text, nullable=False)
    communication_style = Column(Text, nullable=True)
    knowledge_base = Column(Text, nullable=True)
    model_name = Column(String(100), default="gpt-4o-mini", nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    max_tokens = Column(Integer, default=500, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relacionamentos
    user = relationship("User", back_populates="agents")
    campaigns = relationship("Campaign", back_populates="agent", lazy="dynamic")
    
    def generate_system_prompt(self) -> str:
        """
        Gera o system prompt para o LLM baseado nos atributos do agente.
        """
        prompt_parts = [
            f"Você é {self.name}, um representante virtual de uma empresa.",
            "",
            "PERSONALIDADE:",
            self.personality,
        ]
        
        if self.communication_style:
            prompt_parts.extend([
                "",
                "ESTILO DE COMUNICAÇÃO:",
                self.communication_style,
            ])
        
        if self.knowledge_base:
            prompt_parts.extend([
                "",
                "BASE DE CONHECIMENTO:",
                self.knowledge_base,
            ])
        
        prompt_parts.extend([
            "",
            "INSTRUÇÕES:",
            "- Crie mensagens personalizadas para prospecção",
            "- Seja natural e humanizado, evite parecer um robô",
            "- Adapte a mensagem ao contexto do prospect",
            "- Seja breve e objetivo (máximo 3-4 parágrafos)",
            "- Inclua uma chamada para ação clara",
        ])
        
        return "\n".join(prompt_parts)
    
    def __repr__(self):
        return f"<Agent {self.name}>"
    
    # Relacionamentos
    user = relationship("User", back_populates="agents")
    campaigns = relationship("Campaign", back_populates="agent", lazy="dynamic")
    
    def __repr__(self):
        return f"<Agent {self.name}>"
