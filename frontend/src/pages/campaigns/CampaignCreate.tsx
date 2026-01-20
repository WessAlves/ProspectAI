import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowLeft, Plus, X, Globe, MapPin, Instagram, Search, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'
import { usePlanLimits } from '@/hooks/usePlanLimits'

// Tipos de fonte de prospecção
const PROSPECTING_SOURCES = [
  { value: 'google_maps', label: 'Google Maps', icon: MapPin, description: 'Buscar empresas no Google Maps por localização' },
  { value: 'google', label: 'Google Search', icon: Globe, description: 'Buscar sites e empresas no Google' },
  { value: 'instagram', label: 'Instagram', icon: Instagram, description: 'Buscar perfis de negócios por hashtags' },
  { value: 'all', label: 'Todas as Fontes', icon: Sparkles, description: 'Buscar em todas as fontes disponíveis' },
]

// Canais de comunicação
const COMMUNICATION_CHANNELS = [
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'instagram', label: 'Instagram DM' },
  { value: 'email', label: 'E-mail' },
]

const campaignSchema = z.object({
  name: z.string().min(2, 'Nome deve ter no mínimo 2 caracteres'),
  description: z.string().optional(),
  prospecting_source: z.enum(['google', 'google_maps', 'instagram', 'all']),
  niche: z.string().min(2, 'Nicho deve ter no mínimo 2 caracteres'),
  location: z.string().optional(),
  hashtags: z.array(z.string()).optional(),
  keywords: z.array(z.string()).optional(),
  channel: z.enum(['whatsapp', 'instagram', 'email']),
  agent_id: z.string().optional(),
  rate_limit: z.number().min(1, 'Limite deve ser pelo menos 1').max(100, 'Limite máximo é 100'),
})

type CampaignForm = z.infer<typeof campaignSchema>

interface Agent {
  id: string
  name: string
}

export default function CampaignCreate() {
  const [isLoading, setIsLoading] = useState(false)
  const [agents, setAgents] = useState<Agent[]>([])
  const [newHashtag, setNewHashtag] = useState('')
  const [newKeyword, setNewKeyword] = useState('')
  const navigate = useNavigate()
  const { toast } = useToast()
  const { checkCampaignsLimit, checkWhatsApp } = usePlanLimits()

  const { register, handleSubmit, control, watch, setValue, formState: { errors } } = useForm<CampaignForm>({
    resolver: zodResolver(campaignSchema),
    defaultValues: {
      prospecting_source: 'google_maps',
      channel: 'whatsapp',
      rate_limit: 20,
      hashtags: [],
      keywords: [],
    },
  })

  const prospectingSource = watch('prospecting_source')
  const hashtags = watch('hashtags') || []
  const keywords = watch('keywords') || []

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await api.get('/agents')
        setAgents(response.data)
      } catch (error) {
        console.error('Erro ao carregar agentes:', error)
      }
    }
    fetchAgents()
  }, [])

  const addHashtag = () => {
    if (newHashtag.trim()) {
      const tag = newHashtag.trim().replace(/^#/, '')
      if (!hashtags.includes(tag)) {
        setValue('hashtags', [...hashtags, tag])
      }
      setNewHashtag('')
    }
  }

  const removeHashtag = (tag: string) => {
    setValue('hashtags', hashtags.filter((h: string) => h !== tag))
  }

  const addKeyword = () => {
    if (newKeyword.trim()) {
      const kw = newKeyword.trim()
      if (!keywords.includes(kw)) {
        setValue('keywords', [...keywords, kw])
      }
      setNewKeyword('')
    }
  }

  const removeKeyword = (kw: string) => {
    setValue('keywords', keywords.filter((k: string) => k !== kw))
  }

  const onSubmit = async (data: CampaignForm) => {
    // Verificar limite de campanhas antes de criar
    if (!checkCampaignsLimit()) {
      return // Modal de upgrade já foi exibido
    }
    
    // Verificar se WhatsApp está habilitado quando selecionado
    if (data.channel === 'whatsapp' && !checkWhatsApp()) {
      return // Modal de upgrade já foi exibido
    }
    
    setIsLoading(true)
    try {
      // Preparar dados para envio
      const payload = {
        ...data,
        agent_id: data.agent_id || null,
        search_config: {},
      }

      await api.post('/campaigns', payload)
      toast({
        title: 'Campanha criada!',
        description: 'A campanha foi criada com sucesso.',
      })
      navigate('/campaigns')
    } catch (error: any) {
      // O interceptor já vai tratar erros 403 e mostrar o modal
      toast({
        variant: 'destructive',
        title: 'Erro ao criar campanha',
        description: error.response?.data?.detail || 'Não foi possível criar a campanha.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Verificar se deve mostrar campos específicos
  const showInstagramFields = prospectingSource === 'instagram' || prospectingSource === 'all'
  const showGoogleFields = prospectingSource === 'google' || prospectingSource === 'google_maps' || prospectingSource === 'all'

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/campaigns')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nova Campanha</h1>
          <p className="text-muted-foreground">
            Configure uma nova campanha de prospecção
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6">
          {/* Informações Básicas */}
          <Card>
            <CardHeader>
              <CardTitle>Informações Básicas</CardTitle>
              <CardDescription>
                Dados de identificação da campanha
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Nome da Campanha *</Label>
                  <Input
                    id="name"
                    placeholder="Ex: Prospecção Restaurantes SP"
                    {...register('name')}
                  />
                  {errors.name && (
                    <p className="text-sm text-destructive">{errors.name.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="agent_id">Agente de IA (opcional)</Label>
                  <select
                    id="agent_id"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    {...register('agent_id')}
                  >
                    <option value="">Selecione um agente</option>
                    {agents.map((agent) => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <Textarea
                  id="description"
                  placeholder="Descreva o objetivo desta campanha"
                  {...register('description')}
                />
              </div>
            </CardContent>
          </Card>

          {/* Fonte de Prospecção */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Fonte de Prospecção
              </CardTitle>
              <CardDescription>
                Escolha onde buscar seus Leads
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Controller
                name="prospecting_source"
                control={control}
                render={({ field }) => (
                  <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                    {PROSPECTING_SOURCES.map((source) => {
                      const Icon = source.icon
                      const isSelected = field.value === source.value
                      return (
                        <div
                          key={source.value}
                          onClick={() => field.onChange(source.value)}
                          className={`
                            relative cursor-pointer rounded-lg border-2 p-4 transition-all
                            ${isSelected 
                              ? 'border-primary bg-primary/5' 
                              : 'border-border hover:border-primary/50'
                            }
                          `}
                        >
                          <div className="flex flex-col items-center text-center gap-2">
                            <div className={`p-2 rounded-full ${isSelected ? 'bg-primary/10' : 'bg-muted'}`}>
                              <Icon className={`h-6 w-6 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                            </div>
                            <h4 className="font-medium">{source.label}</h4>
                            <p className="text-xs text-muted-foreground">{source.description}</p>
                          </div>
                          {isSelected && (
                            <div className="absolute top-2 right-2">
                              <div className="h-2 w-2 rounded-full bg-primary" />
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              />
            </CardContent>
          </Card>

          {/* Configurações de Busca */}
          <Card>
            <CardHeader>
              <CardTitle>Configurações de Busca</CardTitle>
              <CardDescription>
                Defina os critérios para encontrar Leads
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Nicho e Localização - sempre visíveis */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="niche">Nicho / Segmento *</Label>
                  <Input
                    id="niche"
                    placeholder="Ex: restaurantes, clínicas odontológicas, academias"
                    {...register('niche')}
                  />
                  {errors.niche && (
                    <p className="text-sm text-destructive">{errors.niche.message}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Tipo de negócio que você deseja prospectar
                  </p>
                </div>
                
                {showGoogleFields && (
                  <div className="space-y-2">
                    <Label htmlFor="location">Localização</Label>
                    <Input
                      id="location"
                      placeholder="Ex: São Paulo, SP"
                      {...register('location')}
                    />
                    <p className="text-xs text-muted-foreground">
                      Região geográfica para a busca
                    </p>
                  </div>
                )}
              </div>

              {/* Palavras-chave - para Google */}
              {showGoogleFields && (
                <div className="space-y-2">
                  <Label>Palavras-chave Adicionais</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Adicionar palavra-chave"
                      value={newKeyword}
                      onChange={(e) => setNewKeyword(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
                    />
                    <Button type="button" variant="outline" onClick={addKeyword}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {keywords.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {keywords.map((kw) => (
                        <Badge key={kw} variant="secondary" className="gap-1">
                          {kw}
                          <X
                            className="h-3 w-3 cursor-pointer hover:text-destructive"
                            onClick={() => removeKeyword(kw)}
                          />
                        </Badge>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Termos adicionais para refinar a busca no Google
                  </p>
                </div>
              )}

              {/* Hashtags - para Instagram */}
              {showInstagramFields && (
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Instagram className="h-4 w-4" />
                    Hashtags para Instagram
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Adicionar hashtag (sem #)"
                      value={newHashtag}
                      onChange={(e) => setNewHashtag(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addHashtag())}
                    />
                    <Button type="button" variant="outline" onClick={addHashtag}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {hashtags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {hashtags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="gap-1">
                          #{tag}
                          <X
                            className="h-3 w-3 cursor-pointer hover:text-destructive"
                            onClick={() => removeHashtag(tag)}
                          />
                        </Badge>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Hashtags usadas por negócios do seu nicho no Instagram
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Canal de Comunicação */}
          <Card>
            <CardHeader>
              <CardTitle>Canal de Comunicação</CardTitle>
              <CardDescription>
                Como você irá contatar os Leads
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="channel">Canal de Envio *</Label>
                  <select
                    id="channel"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    {...register('channel')}
                  >
                    {COMMUNICATION_CHANNELS.map((ch) => (
                      <option key={ch.value} value={ch.value}>
                        {ch.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rate_limit">Limite de Mensagens/Hora</Label>
                  <Input
                    id="rate_limit"
                    type="number"
                    min={1}
                    max={100}
                    {...register('rate_limit', { valueAsNumber: true })}
                  />
                  {errors.rate_limit && (
                    <p className="text-sm text-destructive">{errors.rate_limit.message}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Máximo de mensagens enviadas por hora (recomendado: 20)
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <Button type="button" variant="outline" onClick={() => navigate('/campaigns')}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Criando...' : 'Criar Campanha'}
          </Button>
        </div>
      </form>
    </div>
  )
}
