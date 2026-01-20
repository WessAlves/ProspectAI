import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Target, Play, Pause, Eye, Trash2, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import api from '@/lib/api'

interface Campaign {
  id: string
  name: string
  description: string | null
  status: 'draft' | 'active' | 'paused' | 'completed'
  agent_id: string | null
  agent_name: string | null
  prospects_count: number
  messages_count: number
  responses_count: number
  created_at: string
}

const statusConfig = {
  draft: { label: 'Rascunho', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  active: { label: 'Ativa', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  paused: { label: 'Pausada', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' },
  completed: { label: 'Concluída', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [campaignToDelete, setCampaignToDelete] = useState<Campaign | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const { toast } = useToast()

  const fetchCampaigns = async () => {
    try {
      const response = await api.get('/campaigns')
      setCampaigns(response.data)
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao carregar campanhas',
        description: 'Não foi possível carregar a lista de campanhas.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const toggleCampaignStatus = async (campaignId: string, currentStatus: string) => {
    const endpoint = currentStatus === 'active' ? 'pause' : 'start'
    try {
      await api.post(`/campaigns/${campaignId}/${endpoint}`)
      // Recarregar lista para obter dados atualizados
      await fetchCampaigns()
      toast({
        title: 'Status atualizado',
        description: `Campanha ${endpoint === 'start' ? 'ativada' : 'pausada'} com sucesso.`,
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao atualizar status',
        description: error.response?.data?.detail || 'Não foi possível atualizar o status da campanha.',
      })
    }
  }

  const handleDeleteClick = (campaign: Campaign) => {
    if (campaign.status === 'active') {
      toast({
        variant: 'destructive',
        title: 'Não é possível excluir',
        description: 'Pause a campanha antes de excluí-la.',
      })
      return
    }
    setCampaignToDelete(campaign)
    setDeleteDialogOpen(true)
  }

  const confirmDelete = async () => {
    if (!campaignToDelete) return
    
    setIsDeleting(true)
    try {
      await api.delete(`/campaigns/${campaignToDelete.id}`)
      await fetchCampaigns()
      toast({
        title: 'Campanha excluída',
        description: 'A campanha foi excluída com sucesso.',
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao excluir campanha',
        description: error.response?.data?.detail || 'Não foi possível excluir a campanha.',
      })
    } finally {
      setIsDeleting(false)
      setDeleteDialogOpen(false)
      setCampaignToDelete(null)
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
          <h1 className="text-3xl font-bold tracking-tight">Campanhas</h1>
          <p className="text-muted-foreground">
            Gerencie suas campanhas de prospecção
          </p>
        </div>
        <Link to="/campaigns/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Nova Campanha
          </Button>
        </Link>
      </div>

      {campaigns.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Nenhuma campanha cadastrada</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Crie sua primeira campanha para começar a prospectar
            </p>
            <Link to="/campaigns/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Criar primeira campanha
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {campaigns.map((campaign) => (
            <Card key={campaign.id}>
              <CardHeader className="flex flex-row items-start justify-between space-y-0">
                <div className="space-y-1">
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    {campaign.name}
                  </CardTitle>
                  <CardDescription>
                    {campaign.description || 'Sem descrição'}
                  </CardDescription>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig[campaign.status].color}`}>
                  {statusConfig[campaign.status].label}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4 mb-4">
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{campaign.prospects_count}</p>
                    <p className="text-xs text-muted-foreground">Leads</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{campaign.messages_count}</p>
                    <p className="text-xs text-muted-foreground">Mensagens Enviadas</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{campaign.responses_count}</p>
                    <p className="text-xs text-muted-foreground">Respostas</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">
                      {campaign.messages_count > 0 
                        ? Math.round((campaign.responses_count / campaign.messages_count) * 100) 
                        : 0}%
                    </p>
                    <p className="text-xs text-muted-foreground">Taxa de Resposta</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="flex gap-2">
                    <Link to={`/campaigns/${campaign.id}`}>
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-2" />
                        Detalhes
                      </Button>
                    </Link>
                    {campaign.status === 'draft' && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => toggleCampaignStatus(campaign.id, campaign.status)}
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Iniciar
                      </Button>
                    )}
                    {(campaign.status === 'active' || campaign.status === 'paused') && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => toggleCampaignStatus(campaign.id, campaign.status)}
                      >
                        {campaign.status === 'active' ? (
                          <>
                            <Pause className="h-4 w-4 mr-2" />
                            Pausar
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4 mr-2" />
                            Retomar
                          </>
                        )}
                      </Button>
                    )}
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleDeleteClick(campaign)}
                      className={campaign.status === 'active' 
                        ? "text-muted-foreground cursor-not-allowed" 
                        : "text-destructive hover:text-destructive"}
                      title={campaign.status === 'active' ? 'Pause a campanha para excluir' : 'Excluir campanha'}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {campaign.agent_name && <span>Agente: {campaign.agent_name} • </span>}
                    Criada em {new Date(campaign.created_at).toLocaleDateString('pt-BR')}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal de Confirmação de Exclusão */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Excluir Campanha
            </AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir a campanha{' '}
              <strong>"{campaignToDelete?.name}"</strong>?
              <br /><br />
              Esta ação não pode ser desfeita. Todos os leads e dados associados 
              a esta campanha serão permanentemente removidos.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? 'Excluindo...' : 'Sim, excluir campanha'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
