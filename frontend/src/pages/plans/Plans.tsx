import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, CreditCard, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'

interface Plan {
  id: string
  name: string
  description: string | null
  price: number
  billing_cycle: 'monthly' | 'yearly'
  max_agents: number
  max_campaigns: number
  max_prospects: number
  max_messages_per_day: number
  features: string[]
  is_active: boolean
}

export default function Plans() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  const fetchPlans = async () => {
    try {
      const response = await api.get('/plans')
      setPlans(response.data)
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao carregar planos',
        description: 'Não foi possível carregar a lista de planos.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchPlans()
  }, [])

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(price)
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
          <h1 className="text-3xl font-bold tracking-tight">Planos</h1>
          <p className="text-muted-foreground">
            Gerencie os planos disponíveis para seus clientes
          </p>
        </div>
        <Link to="/plans/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Novo Plano
          </Button>
        </Link>
      </div>

      {plans.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <CreditCard className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Nenhum plano cadastrado</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Crie seu primeiro plano para começar
            </p>
            <Link to="/plans/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Criar primeiro plano
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {plans.map((plan) => (
            <Card key={plan.id} className={`relative ${!plan.is_active ? 'opacity-60' : ''}`}>
              {!plan.is_active && (
                <div className="absolute top-2 right-2 px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded text-xs">
                  Inativo
                </div>
              )}
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  {plan.name}
                </CardTitle>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <span className="text-3xl font-bold">{formatPrice(plan.price)}</span>
                  <span className="text-muted-foreground">
                    /{plan.billing_cycle === 'monthly' ? 'mês' : 'ano'}
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Agentes</span>
                    <span className="font-medium">{plan.max_agents}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Campanhas</span>
                    <span className="font-medium">{plan.max_campaigns}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Leads</span>
                    <span className="font-medium">{plan.max_prospects.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Mensagens/dia</span>
                    <span className="font-medium">{plan.max_messages_per_day}</span>
                  </div>
                </div>

                {plan.features && plan.features.length > 0 && (
                  <div className="border-t pt-4">
                    <p className="text-sm font-medium mb-2">Recursos:</p>
                    <ul className="space-y-1">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-center gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-500" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <Link to={`/plans/${plan.id}/edit`} className="w-full">
                  <Button variant="outline" className="w-full">
                    Editar Plano
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
