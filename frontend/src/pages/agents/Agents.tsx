import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Bot, Edit, Trash2, Power, PowerOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'

interface Agent {
  id: string
  name: string
  description: string | null
  personality: string
  communication_style: string | null
  knowledge_base: string | null
  model_name: string
  temperature: number
  max_tokens: number
  is_active: boolean
  created_at: string
}

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  const fetchAgents = async () => {
    try {
      const response = await api.get('/agents')
      setAgents(response.data)
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao carregar agentes',
        description: 'Não foi possível carregar a lista de agentes.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
  }, [])

  const toggleAgentStatus = async (agentId: string, currentStatus: boolean) => {
    try {
      await api.patch(`/agents/${agentId}`, { is_active: !currentStatus })
      setAgents(agents.map(agent => 
        agent.id === agentId ? { ...agent, is_active: !currentStatus } : agent
      ))
      toast({
        title: 'Status atualizado',
        description: `Agente ${!currentStatus ? 'ativado' : 'desativado'} com sucesso.`,
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao atualizar status',
        description: 'Não foi possível atualizar o status do agente.',
      })
    }
  }

  const deleteAgent = async (agentId: string) => {
    if (!confirm('Tem certeza que deseja excluir este agente?')) return
    
    try {
      await api.delete(`/agents/${agentId}`)
      setAgents(agents.filter(agent => agent.id !== agentId))
      toast({
        title: 'Agente excluído',
        description: 'O agente foi excluído com sucesso.',
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao excluir agente',
        description: 'Não foi possível excluir o agente.',
      })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agentes</h1>
          <p className="text-muted-foreground">
            Gerencie seus agentes de prospecção automatizada
          </p>
        </div>
        <Link to="/agents/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Novo Agente
          </Button>
        </Link>
      </div>

      {agents.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Bot className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Nenhum agente cadastrado</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Crie seu primeiro agente para começar a prospectar
            </p>
            <Link to="/agents/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Criar primeiro agente
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <Card key={agent.id} className={!agent.is_active ? 'opacity-60' : ''}>
              <CardHeader className="flex flex-row items-start justify-between space-y-0">
                <div className="space-y-1">
                  <CardTitle className="flex items-center gap-2">
                    <Bot className="h-5 w-5" />
                    {agent.name}
                  </CardTitle>
                  <CardDescription>
                    {agent.description || agent.model_name}
                  </CardDescription>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                  agent.is_active 
                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' 
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                }`}>
                  {agent.is_active ? 'Ativo' : 'Inativo'}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm font-medium">Personalidade</p>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {agent.personality}
                    </p>
                  </div>
                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="flex gap-2">
                      <Link to={`/agents/${agent.id}/edit`}>
                        <Button variant="outline" size="sm">
                          <Edit className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => toggleAgentStatus(agent.id, agent.is_active)}
                      >
                        {agent.is_active ? (
                          <PowerOff className="h-4 w-4" />
                        ) : (
                          <Power className="h-4 w-4" />
                        )}
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => deleteAgent(agent.id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Criado em {new Date(agent.created_at).toLocaleDateString('pt-BR')}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
