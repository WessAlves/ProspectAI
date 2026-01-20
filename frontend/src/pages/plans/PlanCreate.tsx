import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowLeft, Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'

const planSchema = z.object({
  name: z.string().min(2, 'Nome deve ter no mínimo 2 caracteres'),
  description: z.string().optional(),
  price: z.number().min(0, 'Preço deve ser positivo'),
  billing_cycle: z.enum(['monthly', 'yearly']),
  max_agents: z.number().min(1, 'Mínimo de 1 agente'),
  max_campaigns: z.number().min(1, 'Mínimo de 1 campanha'),
  max_prospects: z.number().min(1, 'Mínimo de 1 prospect'),
  max_messages_per_day: z.number().min(1, 'Mínimo de 1 mensagem'),
})

type PlanForm = z.infer<typeof planSchema>

export default function PlanCreate() {
  const [isLoading, setIsLoading] = useState(false)
  const [features, setFeatures] = useState<string[]>([])
  const [newFeature, setNewFeature] = useState('')
  const navigate = useNavigate()
  const { toast } = useToast()

  const { register, handleSubmit, formState: { errors } } = useForm<PlanForm>({
    resolver: zodResolver(planSchema),
    defaultValues: {
      billing_cycle: 'monthly',
      max_agents: 3,
      max_campaigns: 5,
      max_prospects: 1000,
      max_messages_per_day: 100,
    },
  })

  const addFeature = () => {
    if (newFeature.trim() && !features.includes(newFeature.trim())) {
      setFeatures([...features, newFeature.trim()])
      setNewFeature('')
    }
  }

  const removeFeature = (index: number) => {
    setFeatures(features.filter((_, i) => i !== index))
  }

  const onSubmit = async (data: PlanForm) => {
    setIsLoading(true)
    try {
      await api.post('/plans', { ...data, features })
      toast({
        title: 'Plano criado!',
        description: 'O plano foi criado com sucesso.',
      })
      navigate('/plans')
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao criar plano',
        description: error.response?.data?.detail || 'Não foi possível criar o plano.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/plans')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Novo Plano</h1>
          <p className="text-muted-foreground">
            Configure um novo plano de assinatura
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Informações Básicas</CardTitle>
              <CardDescription>
                Dados de identificação do plano
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome do Plano *</Label>
                <Input
                  id="name"
                  placeholder="Ex: Plano Profissional"
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
                  placeholder="Descreva os benefícios deste plano"
                  {...register('description')}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="price">Preço *</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="99.90"
                    {...register('price', { valueAsNumber: true })}
                  />
                  {errors.price && (
                    <p className="text-sm text-destructive">{errors.price.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="billing_cycle">Ciclo de Cobrança *</Label>
                  <select
                    id="billing_cycle"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    {...register('billing_cycle')}
                  >
                    <option value="monthly">Mensal</option>
                    <option value="yearly">Anual</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Limites</CardTitle>
              <CardDescription>
                Defina os limites de uso do plano
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max_agents">Máx. Agentes</Label>
                  <Input
                    id="max_agents"
                    type="number"
                    min="1"
                    {...register('max_agents', { valueAsNumber: true })}
                  />
                  {errors.max_agents && (
                    <p className="text-sm text-destructive">{errors.max_agents.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_campaigns">Máx. Campanhas</Label>
                  <Input
                    id="max_campaigns"
                    type="number"
                    min="1"
                    {...register('max_campaigns', { valueAsNumber: true })}
                  />
                  {errors.max_campaigns && (
                    <p className="text-sm text-destructive">{errors.max_campaigns.message}</p>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max_prospects">Máx. Leads</Label>
                  <Input
                    id="max_prospects"
                    type="number"
                    min="1"
                    {...register('max_prospects', { valueAsNumber: true })}
                  />
                  {errors.max_prospects && (
                    <p className="text-sm text-destructive">{errors.max_prospects.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_messages_per_day">Máx. Mensagens/Dia</Label>
                  <Input
                    id="max_messages_per_day"
                    type="number"
                    min="1"
                    {...register('max_messages_per_day', { valueAsNumber: true })}
                  />
                  {errors.max_messages_per_day && (
                    <p className="text-sm text-destructive">{errors.max_messages_per_day.message}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recursos do Plano</CardTitle>
              <CardDescription>
                Liste os recursos incluídos neste plano
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Ex: Suporte prioritário"
                    value={newFeature}
                    onChange={(e) => setNewFeature(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addFeature())}
                  />
                  <Button type="button" onClick={addFeature}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                {features.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {features.map((feature, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-1 px-3 py-1 bg-primary/10 rounded-full text-sm"
                      >
                        {feature}
                        <button
                          type="button"
                          onClick={() => removeFeature(index)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <Button type="button" variant="outline" onClick={() => navigate('/plans')}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Criando...' : 'Criar Plano'}
          </Button>
        </div>
      </form>
    </div>
  )
}
