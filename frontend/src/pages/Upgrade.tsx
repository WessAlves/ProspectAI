import { useSearchParams } from 'react-router-dom'
import { Check, Crown, Sparkles, Zap, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/components/ui/use-toast'

// Detalhes completos dos planos
const PLANS = [
  {
    id: 'free',
    name: 'Gratuito',
    description: 'Para conhecer a plataforma',
    price: 0,
    priceLabel: 'R$ 0',
    period: '/mês',
    color: 'border-gray-300',
    buttonColor: 'bg-gray-500 hover:bg-gray-600',
    features: [
      { text: '50 leads/mês', included: true },
      { text: '1 agente de IA', included: true },
      { text: '1 campanha', included: true },
      { text: 'WhatsApp', included: false },
      { text: 'Filtros avançados', included: false },
      { text: 'Relatórios de funil', included: false },
    ],
  },
  {
    id: 'starter',
    name: 'Starter',
    description: 'Para começar a prospectar',
    price: 97,
    priceLabel: 'R$ 97',
    period: '/mês',
    color: 'border-blue-500',
    buttonColor: 'bg-blue-600 hover:bg-blue-700',
    features: [
      { text: '500 leads/mês', included: true },
      { text: '1 agente de IA', included: true },
      { text: '3 campanhas', included: true },
      { text: 'WhatsApp', included: true },
      { text: 'Filtros avançados', included: true },
      { text: 'Relatórios de funil', included: true },
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    description: 'Para escalar sua prospecção',
    price: 297,
    priceLabel: 'R$ 297',
    period: '/mês',
    color: 'border-purple-500',
    buttonColor: 'bg-purple-600 hover:bg-purple-700',
    popular: true,
    features: [
      { text: '2.000 leads/mês', included: true },
      { text: '5 agentes de IA', included: true },
      { text: '10 campanhas', included: true },
      { text: 'API Oficial WhatsApp', included: true },
      { text: 'Comparativo de campanhas', included: true },
      { text: 'Integração CRM', included: true },
    ],
  },
  {
    id: 'scale',
    name: 'Scale',
    description: 'Para operações enterprise',
    price: 697,
    priceLabel: 'R$ 697',
    period: '/mês',
    color: 'border-amber-500',
    buttonColor: 'bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600',
    features: [
      { text: 'Leads ilimitados', included: true },
      { text: 'Agentes ilimitados', included: true },
      { text: 'Campanhas ilimitadas', included: true },
      { text: 'Suporte prioritário', included: true },
      { text: 'SSO / Login corporativo', included: true },
      { text: 'Gerente de conta dedicado', included: true },
    ],
  },
]

export default function Upgrade() {
  const [searchParams] = useSearchParams()
  const { getPlanTier, getPlanName } = useAuthStore()
  const { toast } = useToast()
  
  const currentPlanTier = getPlanTier()
  const currentPlanName = getPlanName()
  const selectedPlan = searchParams.get('selected')
  
  // Ordem dos planos para comparação
  const planOrder = ['free', 'starter', 'pro', 'scale']
  const currentIndex = planOrder.indexOf(currentPlanTier)
  
  // Próximo plano recomendado
  const nextPlanIndex = currentIndex + 1
  const recommendedPlan = nextPlanIndex < planOrder.length ? planOrder[nextPlanIndex] : null
  
  const handleSelectPlan = (planId: string) => {
    const planIndex = planOrder.indexOf(planId)
    
    if (planIndex <= currentIndex) {
      toast({
        variant: 'destructive',
        title: 'Plano não disponível',
        description: 'Você já possui este plano ou um superior.',
      })
      return
    }
    
    // TODO: Integrar com gateway de pagamento
    toast({
      title: 'Redirecionando...',
      description: `Iniciando processo de upgrade para o plano ${PLANS.find(p => p.id === planId)?.name}.`,
    })
    
    // Simular redirecionamento para checkout
    // navigate(`/checkout?plan=${planId}`)
  }
  
  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Faça Upgrade do seu Plano
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Escolha o plano ideal para escalar sua prospecção. 
          Todos os planos incluem atualizações gratuitas e acesso a novas funcionalidades.
        </p>
        
        {/* Plano atual */}
        <div className="mt-4 inline-flex items-center gap-2 bg-muted px-4 py-2 rounded-full">
          <span className="text-sm text-muted-foreground">Seu plano atual:</span>
          <Badge variant="outline" className="font-semibold">
            {currentPlanName}
          </Badge>
        </div>
      </div>
      
      {/* Plano Recomendado Destacado */}
      {recommendedPlan && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20 border border-purple-200 dark:border-purple-800 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <span className="font-semibold text-purple-900 dark:text-purple-100">
              Recomendado para você
            </span>
          </div>
          <p className="text-sm text-purple-700 dark:text-purple-300">
            Baseado no seu uso atual, recomendamos o plano{' '}
            <strong>{PLANS.find(p => p.id === recommendedPlan)?.name}</strong> para 
            desbloquear mais recursos e aumentar seus limites.
          </p>
        </div>
      )}
      
      {/* Cards dos Planos */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {PLANS.map((plan) => {
          const planIndex = planOrder.indexOf(plan.id)
          const isCurrentPlan = plan.id === currentPlanTier
          const isPastPlan = planIndex < currentIndex
          const isRecommended = plan.id === recommendedPlan
          const isSelected = plan.id === selectedPlan
          const isDisabled = planIndex <= currentIndex
          
          return (
            <Card 
              key={plan.id} 
              className={`relative flex flex-col ${plan.color} border-2 
                ${isRecommended ? 'ring-2 ring-purple-500 ring-offset-2' : ''}
                ${isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
                ${isDisabled ? 'opacity-60' : ''}`}
            >
              {/* Badges */}
              {plan.popular && !isDisabled && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-purple-600 text-white">
                    Mais Popular
                  </Badge>
                </div>
              )}
              {isRecommended && (
                <div className="absolute -top-3 right-4">
                  <Badge className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
                    <Sparkles className="h-3 w-3 mr-1" />
                    Recomendado
                  </Badge>
                </div>
              )}
              {isCurrentPlan && (
                <div className="absolute -top-3 left-4">
                  <Badge variant="secondary">
                    Plano Atual
                  </Badge>
                </div>
              )}
              
              <CardHeader className="text-center pb-2">
                {plan.id === 'scale' && (
                  <Crown className="h-8 w-8 text-amber-500 mx-auto mb-2" />
                )}
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>
              
              <CardContent className="flex-1 space-y-4">
                {/* Preço */}
                <div className="text-center">
                  <span className="text-4xl font-bold">{plan.priceLabel}</span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </div>
                
                {/* Features */}
                <ul className="space-y-2">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-sm">
                      <Check 
                        className={`h-4 w-4 flex-shrink-0 ${
                          feature.included ? 'text-green-500' : 'text-gray-300'
                        }`} 
                      />
                      <span className={feature.included ? '' : 'text-muted-foreground line-through'}>
                        {feature.text}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              
              <CardFooter>
                {isCurrentPlan ? (
                  <Button disabled className="w-full" variant="outline">
                    Plano Atual
                  </Button>
                ) : isPastPlan ? (
                  <Button disabled className="w-full" variant="outline">
                    Já incluído
                  </Button>
                ) : (
                  <Button 
                    className={`w-full ${plan.buttonColor} text-white`}
                    onClick={() => handleSelectPlan(plan.id)}
                  >
                    {isRecommended && <Zap className="mr-2 h-4 w-4" />}
                    Selecionar {plan.name}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                )}
              </CardFooter>
            </Card>
          )
        })}
      </div>
      
      {/* FAQ / Informações adicionais */}
      <div className="text-center text-sm text-muted-foreground">
        <p>
          Todos os planos são cobrados mensalmente. Cancele a qualquer momento.
        </p>
        <p className="mt-1">
          Precisa de um plano customizado?{' '}
          <a href="mailto:contato@prospectai.com.br" className="text-primary hover:underline">
            Entre em contato
          </a>
        </p>
      </div>
    </div>
  )
}
