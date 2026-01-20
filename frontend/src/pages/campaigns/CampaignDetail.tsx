import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Play, Pause, Users, MessageSquare, Mail, Phone, Globe, ExternalLink, Search, ChevronUp, ChevronDown, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'

interface Campaign {
  id: string
  name: string
  description: string | null
  status: 'draft' | 'active' | 'paused' | 'completed'
  agent_id: string | null
  prospecting_source: string
  niche: string | null
  location: string | null
  hashtags: string[]
  keywords: string[]
  channel: string
  rate_limit: number
  prospects_count: number
  messages_count: number
  created_at: string
  updated_at: string
  agent?: {
    id: string
    name: string
  } | null
  plans?: Array<{
    id: string
    name: string
  }>
}

interface Prospect {
  id: string
  name: string | null
  username: string
  platform: string
  profile_url: string | null
  followers_count: number | null
  has_website: boolean
  website_url: string | null
  status: string
  score: number
  extra_data: Record<string, any>
  last_post_date: string | null
  created_at: string
  updated_at: string
  email: string | null
  phone: string | null
  company: string | null
  position: string | null
}

const statusConfig = {
  draft: { label: 'Rascunho', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  active: { label: 'Ativa', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  paused: { label: 'Pausada', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' },
  completed: { label: 'Concluída', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
}

export default function CampaignDetail() {
  const { id } = useParams<{ id: string }>()
  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [prospects, setProspects] = useState<Prospect[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingProspects, setIsLoadingProspects] = useState(false)
  const navigate = useNavigate()
  const { toast } = useToast()

  // Estados de paginação
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalProspects, setTotalProspects] = useState(0)
  const pageSize = 10

  // Estados de busca e ordenação
  const [searchTerm, setSearchTerm] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [sortBy, setSortBy] = useState<string>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Função para buscar prospects com paginação
  const fetchProspects = useCallback(async (page: number, search: string, sortField: string, sortDirection: string) => {
    if (!id) return
    setIsLoadingProspects(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortField,
        sort_order: sortDirection,
      })
      if (search) {
        params.append('search', search)
      }
      const response = await api.get(`/campaigns/${id}/prospects?${params.toString()}`)
      setProspects(response.data.items || [])
      setTotalProspects(response.data.total || 0)
      setTotalPages(response.data.total_pages || 1)
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao carregar leads',
        description: 'Não foi possível carregar os leads da campanha.',
      })
    } finally {
      setIsLoadingProspects(false)
    }
  }, [id, toast])

  useEffect(() => {
    const fetchCampaign = async () => {
      try {
        const campaignRes = await api.get(`/campaigns/${id}`)
        setCampaign(campaignRes.data)
      } catch (error: any) {
        toast({
          variant: 'destructive',
          title: 'Erro ao carregar campanha',
          description: 'Não foi possível carregar os dados da campanha.',
        })
        navigate('/campaigns')
      } finally {
        setIsLoading(false)
      }
    }

    if (id) {
      fetchCampaign()
    }
  }, [id, navigate, toast])

  // Carregar prospects quando mudar página, busca ou ordenação
  useEffect(() => {
    if (id && !isLoading) {
      fetchProspects(currentPage, searchTerm, sortBy, sortOrder)
    }
  }, [id, currentPage, searchTerm, sortBy, sortOrder, isLoading, fetchProspects])

  // Debounce para busca
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== searchTerm) {
        setSearchTerm(searchInput)
        setCurrentPage(1) // Reset para primeira página ao buscar
      }
    }, 500)
    return () => clearTimeout(timer)
  }, [searchInput, searchTerm])

  // Função para alternar ordenação
  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
    setCurrentPage(1) // Reset para primeira página ao ordenar
  }

  // Componente de ícone de ordenação
  const SortIcon = ({ field }: { field: string }) => {
    if (sortBy !== field) return null
    return sortOrder === 'asc' ? (
      <ChevronUp className="h-4 w-4 inline ml-1" />
    ) : (
      <ChevronDown className="h-4 w-4 inline ml-1" />
    )
  }

  const toggleCampaignStatus = async () => {
    if (!campaign) return
    const endpoint = campaign.status === 'active' ? 'pause' : 'start'
    try {
      const response = await api.post(`/campaigns/${id}/${endpoint}`)
      setCampaign(response.data)
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

  const startCampaign = async () => {
    if (!campaign) return
    try {
      const response = await api.post(`/campaigns/${id}/start`)
      setCampaign(response.data)
      toast({
        title: 'Campanha iniciada!',
        description: 'A campanha foi iniciada com sucesso.',
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao iniciar campanha',
        description: error.response?.data?.detail || 'Não foi possível iniciar a campanha.',
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

  if (!campaign) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/campaigns')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">{campaign.name}</h1>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig[campaign.status].color}`}>
                {statusConfig[campaign.status].label}
              </span>
            </div>
            <p className="text-muted-foreground">
              {campaign.description || 'Sem descrição'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {campaign.status === 'draft' && (
            <Button onClick={startCampaign}>
              <Play className="h-4 w-4 mr-2" />
              Iniciar Campanha
            </Button>
          )}
          {(campaign.status === 'active' || campaign.status === 'paused') && (
            <Button onClick={toggleCampaignStatus}>
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
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Leads</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{campaign.prospects_count}</div>
            <p className="text-xs text-muted-foreground">Total na campanha</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mensagens</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{campaign.messages_count}</div>
            <p className="text-xs text-muted-foreground">Enviadas</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Configurações</CardTitle>
            <CardDescription>Parâmetros da campanha</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">Agente</p>
              <p className="text-sm text-muted-foreground">{campaign.agent?.name || 'Não definido'}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Limite Diário</p>
              <p className="text-sm text-muted-foreground">{campaign.rate_limit} mensagens/hora</p>
            </div>
            <div>
              <p className="text-sm font-medium">Criada em</p>
              <p className="text-sm text-muted-foreground">
                {new Date(campaign.created_at).toLocaleDateString('pt-BR', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configurações de Prospecção</CardTitle>
            <CardDescription>Parâmetros de busca da campanha</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">Fonte de Prospecção</p>
              <p className="text-sm text-muted-foreground capitalize">{campaign.prospecting_source?.replace('_', ' ')}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Nicho</p>
              <p className="text-sm text-muted-foreground">{campaign.niche || 'Não definido'}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Localização</p>
              <p className="text-sm text-muted-foreground">{campaign.location || 'Não definida'}</p>
            </div>
            {campaign.hashtags && campaign.hashtags.length > 0 && (
              <div>
                <p className="text-sm font-medium">Hashtags</p>
                <p className="text-sm text-muted-foreground">{campaign.hashtags.map(h => `#${h}`).join(', ')}</p>
              </div>
            )}
            {campaign.keywords && campaign.keywords.length > 0 && (
              <div>
                <p className="text-sm font-medium">Palavras-chave</p>
                <p className="text-sm text-muted-foreground">{campaign.keywords.join(', ')}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Leads da Campanha</CardTitle>
              <CardDescription>
                {totalProspects > 0 
                  ? `${totalProspects} leads nesta campanha`
                  : 'Lista de leads nesta campanha'
                }
              </CardDescription>
            </div>
          </div>
          {/* Barra de busca */}
          <div className="mt-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nome, username ou empresa..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingProspects ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : prospects.length === 0 && !searchTerm ? (
            <div className="text-center py-8">
              <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Nenhum lead nesta campanha</p>
              <Button variant="outline" className="mt-4" onClick={() => navigate('/prospects')}>
                Adicionar Leads
              </Button>
            </div>
          ) : prospects.length === 0 && searchTerm ? (
            <div className="text-center py-8">
              <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Nenhum lead encontrado para "{searchTerm}"</p>
              <Button variant="outline" className="mt-4" onClick={() => { setSearchInput(''); setSearchTerm(''); }}>
                Limpar busca
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th 
                        className="text-left py-3 px-4 font-medium cursor-pointer hover:bg-muted/50 select-none"
                        onClick={() => handleSort('name')}
                      >
                        Nome
                        <SortIcon field="name" />
                      </th>
                      <th className="text-left py-3 px-4 font-medium">Contatos</th>
                      <th 
                        className="text-left py-3 px-4 font-medium cursor-pointer hover:bg-muted/50 select-none"
                        onClick={() => handleSort('website_url')}
                      >
                        Site
                        <SortIcon field="website_url" />
                      </th>
                      <th className="text-left py-3 px-4 font-medium">Plataforma</th>
                      <th className="text-left py-3 px-4 font-medium">Status</th>
                      <th className="text-left py-3 px-4 font-medium">Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {prospects.map((prospect) => (
                      <tr key={prospect.id} className="border-b hover:bg-muted/50">
                        <td className="py-3 px-4">
                          <div>
                            <p className="font-medium">{prospect.name || prospect.username}</p>
                            {prospect.company && (
                              <p className="text-sm text-muted-foreground">{prospect.company}</p>
                            )}
                            {prospect.profile_url && (
                              <a 
                                href={prospect.profile_url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-xs text-blue-500 hover:underline inline-flex items-center gap-1"
                              >
                                <ExternalLink className="h-3 w-3" />
                                Ver perfil
                              </a>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="space-y-1">
                            {prospect.phone && (
                              <a 
                                href={`tel:${prospect.phone}`}
                                className="flex items-center gap-1.5 text-sm text-green-600 hover:underline"
                              >
                                <Phone className="h-3.5 w-3.5" />
                                {prospect.phone}
                              </a>
                            )}
                            {prospect.email && (
                              <a 
                                href={`mailto:${prospect.email}`}
                                className="flex items-center gap-1.5 text-sm text-blue-600 hover:underline"
                              >
                                <Mail className="h-3.5 w-3.5" />
                                {prospect.email}
                              </a>
                            )}
                            {!prospect.phone && !prospect.email && (
                              <span className="text-sm text-muted-foreground">-</span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          {prospect.website_url ? (
                            <a 
                              href={prospect.website_url.startsWith('http') ? prospect.website_url : `https://${prospect.website_url}`}
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="flex items-center gap-1.5 text-sm text-purple-600 hover:underline"
                            >
                              <Globe className="h-3.5 w-3.5" />
                              {prospect.website_url.replace(/^https?:\/\//, '').substring(0, 25)}
                              {prospect.website_url.length > 30 ? '...' : ''}
                            </a>
                          ) : (
                            <span className="text-sm text-muted-foreground">-</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className="capitalize text-sm">{prospect.platform}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-1 rounded-full text-xs bg-muted capitalize">
                            {prospect.status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-xs ${
                            prospect.score >= 70 ? 'bg-green-100 text-green-700' :
                            prospect.score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {prospect.score}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Paginação */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <div className="text-sm text-muted-foreground">
                    Mostrando {((currentPage - 1) * pageSize) + 1} a {Math.min(currentPage * pageSize, totalProspects)} de {totalProspects} leads
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                    >
                      <ChevronsLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm px-2">
                      Página {currentPage} de {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                    >
                      <ChevronsRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
