import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowLeft, Bot, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'
import { usePlanLimits } from '@/hooks/usePlanLimits'

const agentSchema = z.object({
  name: z.string().min(2, 'Nome deve ter no mínimo 2 caracteres'),
  description: z.string().optional(),
  personality: z.string().min(10, 'Personalidade deve ter no mínimo 10 caracteres'),
  communication_style: z.string().optional(),
  knowledge_base: z.string().optional(),
  model_name: z.string().default('gpt-4o-mini'),
  temperature: z.number().min(0).max(2).default(0.7),
  max_tokens: z.number().min(50).max(4000).default(500),
})

type AgentForm = z.infer<typeof agentSchema>

const MODELS = [
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Recomendado)' },
  { value: 'gpt-4o', label: 'GPT-4o (Mais capaz)' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (Econômico)' },
]

export default function AgentCreate() {
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const { toast } = useToast()
  const { checkAgentsLimit } = usePlanLimits()

  const { register, handleSubmit, watch, formState: { errors } } = useForm<AgentForm>({
    resolver: zodResolver(agentSchema),
    defaultValues: {
      name: '',
      description: '',
      personality: 'Profissional, cordial e objetivo. Focado em apresentar soluções para os problemas do cliente de forma consultiva.',
      communication_style: '',
      knowledge_base: '',
      model_name: 'gpt-4o-mini',
      temperature: 0.7,
      max_tokens: 500,
    },
  })

  const temperature = watch('temperature')

  const onSubmit = async (data: AgentForm) => {
    // Verificar limite de agentes antes de criar
    if (!checkAgentsLimit()) {
      return // Modal de upgrade já foi exibido
    }
    
    setIsLoading(true)
    try {
      await api.post('/agents', data)
      toast({
        title: 'Agente criado!',
        description: 'Seu representante virtual foi criado com sucesso.',
      })
      navigate('/agents')
    } catch (error: any) {
      // O interceptor já vai tratar erros 403 e mostrar o modal
      toast({
        variant: 'destructive',
        title: 'Erro ao criar agente',
        description: error.response?.data?.detail || 'Não foi possível criar o agente.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/agents')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Novo Agente</h1>
          <p className="text-muted-foreground">
            Configure um representante virtual para sua empresa
          </p>
        </div>
      </div>

      {/* Dica informativa */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardContent className="flex items-start gap-3 pt-4">
          <Bot className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-blue-900 dark:text-blue-100">
              O que é um Agente?
            </p>
            <p className="text-blue-700 dark:text-blue-300 mt-1">
              O agente é seu representante virtual que irá se comunicar com os leads durante a prospecção. 
              Configure sua personalidade, estilo de comunicação e conhecimento sobre seus produtos/serviços 
              para que ele possa criar mensagens personalizadas e humanizadas.
            </p>
          </div>
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Informações Básicas */}
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
                  placeholder="Ex: João - Consultor de Vendas"
                  {...register('name')}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Use um nome humanizado para tornar as interações mais naturais
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Descrição do Agente</Label>
                <Textarea
                  id="description"
                  placeholder="Ex: Especialista em vendas consultivas para pequenas empresas do setor de alimentação"
                  rows={3}
                  {...register('description')}
                />
                <p className="text-xs text-muted-foreground">
                  Descreva o propósito e especialização deste agente
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Personalidade */}
          <Card>
            <CardHeader>
              <CardTitle>Personalidade do Agente *</CardTitle>
              <CardDescription>
                Como o agente deve se comportar nas conversas
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Textarea
                  id="personality"
                  placeholder="Ex: Profissional mas descontraído. Sempre busca entender as dores do cliente antes de apresentar soluções. Usa linguagem acessível e evita jargões técnicos."
                  rows={5}
                  {...register('personality')}
                />
                {errors.personality && (
                  <p className="text-sm text-destructive">{errors.personality.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Defina o tom de voz, comportamento e abordagem do agente
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Estilo de Comunicação */}
          <Card>
            <CardHeader>
              <CardTitle>Estilo de Comunicação</CardTitle>
              <CardDescription>
                Detalhes sobre como o agente deve se comunicar
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Textarea
                  id="communication_style"
                  placeholder="Ex: Mensagens curtas e diretas. Usa emojis com moderação. Faz perguntas para engajar o prospect. Sempre termina com uma chamada para ação."
                  rows={4}
                  {...register('communication_style')}
                />
                <p className="text-xs text-muted-foreground">
                  Especifique preferências de formatação, uso de emojis, tamanho das mensagens, etc.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Configurações do Modelo */}
          <Card>
            <CardHeader>
              <CardTitle>Configurações de IA</CardTitle>
              <CardDescription>
                Ajustes técnicos do modelo de linguagem
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="model_name">Modelo de IA</Label>
                <select
                  id="model_name"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  {...register('model_name')}
                >
                  {MODELS.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="temperature">
                  Criatividade: {temperature}
                </Label>
                <input
                  type="range"
                  id="temperature"
                  min="0"
                  max="2"
                  step="0.1"
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer"
                  {...register('temperature', { valueAsNumber: true })}
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Mais focado</span>
                  <span>Mais criativo</span>
                </div>
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <Info className="h-3 w-3" />
                  Valores entre 0.5 e 0.9 são ideais para prospecção
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Base de Conhecimento */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Base de Conhecimento</CardTitle>
              <CardDescription>
                Informações que o agente deve conhecer sobre sua empresa, produtos e serviços
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Textarea
                  id="knowledge_base"
                  placeholder={`Ex:
**Sobre a Empresa:**
Somos uma agência de marketing digital especializada em pequenos negócios.

**Serviços:**
- Gestão de redes sociais (a partir de R$ 997/mês)
- Criação de sites (a partir de R$ 2.500)
- Google Ads e Facebook Ads

**Diferenciais:**
- Atendimento personalizado
- Relatórios semanais
- Garantia de 30 dias

**FAQ:**
- Prazo de entrega: 7 a 15 dias úteis
- Formas de pagamento: PIX, boleto ou cartão`}
                  rows={12}
                  {...register('knowledge_base')}
                />
                <p className="text-xs text-muted-foreground">
                  Quanto mais detalhado, melhor o agente poderá responder perguntas e criar mensagens relevantes.
                  Inclua: produtos/serviços, preços, diferenciais, FAQ, objeções comuns e suas respostas.
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
            {isLoading ? 'Criando...' : 'Criar Agente'}
          </Button>
        </div>
      </form>
    </div>
  )
}
