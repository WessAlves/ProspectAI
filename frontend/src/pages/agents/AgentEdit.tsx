import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'

const agentSchema = z.object({
  name: z.string().min(2, 'Nome deve ter no mínimo 2 caracteres'),
  description: z.string().optional(),
  personality: z.string().min(10, 'Personalidade deve ter no mínimo 10 caracteres'),
  communication_style: z.string().optional(),
  knowledge_base: z.string().optional(),
  is_active: z.boolean().optional(),
})

type AgentForm = z.infer<typeof agentSchema>

export default function AgentEdit() {
  const { id } = useParams<{ id: string }>()
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(true)
  const navigate = useNavigate()
  const { toast } = useToast()

  const { register, handleSubmit, formState: { errors }, reset } = useForm<AgentForm>({
    resolver: zodResolver(agentSchema),
  })

  useEffect(() => {
    const fetchAgent = async () => {
      try {
        const response = await api.get(`/agents/${id}`)
        reset(response.data)
      } catch (error: any) {
        toast({
          variant: 'destructive',
          title: 'Erro ao carregar agente',
          description: 'Não foi possível carregar os dados do agente.',
        })
        navigate('/agents')
      } finally {
        setIsFetching(false)
      }
    }

    if (id) {
      fetchAgent()
    }
  }, [id, reset, navigate, toast])

  const onSubmit = async (data: AgentForm) => {
    setIsLoading(true)
    try {
      await api.put(`/agents/${id}`, data)
      toast({
        title: 'Agente atualizado!',
        description: 'O agente foi atualizado com sucesso.',
      })
      navigate('/agents')
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao atualizar agente',
        description: error.response?.data?.detail || 'Não foi possível atualizar o agente.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (isFetching) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/agents')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Editar Agente</h1>
          <p className="text-muted-foreground">
            Atualize as configurações do agente
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Informações Básicas</CardTitle>
              <CardDescription>
                Dados de identificação do agente
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome do Agente *</Label>
                <Input
                  id="name"
                  placeholder="Ex: Vendedor Virtual"
                  {...register('name')}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <Textarea
                  id="description"
                  placeholder="Descreva o propósito deste agente"
                  {...register('description')}
                />
                {errors.description && (
                  <p className="text-sm text-destructive">{errors.description.message}</p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Personalidade</CardTitle>
              <CardDescription>
                Defina como o agente deve se comportar
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="personality">Personalidade *</Label>
                <Textarea
                  id="personality"
                  placeholder="Descreva a personalidade e tom de voz do agente"
                  rows={4}
                  {...register('personality')}
                />
                {errors.personality && (
                  <p className="text-sm text-destructive">{errors.personality.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Defina o tom de voz, comportamento e abordagem do agente nas conversas
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="communication_style">Estilo de Comunicação</Label>
                <Textarea
                  id="communication_style"
                  placeholder="Ex: Formal, direto ao ponto, usa emojis moderadamente"
                  {...register('communication_style')}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Base de Conhecimento</CardTitle>
              <CardDescription>
                Informações que o agente deve conhecer para responder perguntas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="knowledge_base">Conhecimento</Label>
                <Textarea
                  id="knowledge_base"
                  placeholder="Adicione informações sobre produtos, serviços, preços, diferenciais, respostas para perguntas frequentes, etc."
                  rows={6}
                  {...register('knowledge_base')}
                />
                <p className="text-xs text-muted-foreground">
                  Quanto mais detalhado, melhor o agente poderá responder às perguntas dos Leads
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <Button type="button" variant="outline" onClick={() => navigate('/agents')}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Salvando...' : 'Salvar Alterações'}
          </Button>
        </div>
      </form>
    </div>
  )
}
