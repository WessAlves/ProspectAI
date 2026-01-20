import { useNavigate } from 'react-router-dom'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { 
  ArrowRight, 
  Crown, 
  Sparkles, 
  Check,
  Zap
} from 'lucide-react'
import { useUpgradeStore, UPGRADE_MESSAGES, getSuggestedPlan } from '@/stores/upgradeStore'
import { useAuthStore } from '@/stores/authStore'

// Detalhes dos planos para exibição
const PLAN_DETAILS = {
  starter: {
    name: 'Starter',
    price: 'R$ 97',
    period: '/mês',
    color: 'bg-blue-500',
    popular: false,
    features: [
      '500 leads/mês',
      '1 agente de IA',
      '3 campanhas',
      'WhatsApp',
      'Filtros avançados',
      'Relatórios de funil',
    ],
  },
  pro: {
    name: 'Pro',
    price: 'R$ 297',
    period: '/mês',
    color: 'bg-purple-500',
    popular: true,
    features: [
      '2.000 leads/mês',
      '5 agentes de IA',
      '10 campanhas',
      'API Oficial WhatsApp',
      'Comparativo de campanhas',
      'Integração CRM',
    ],
  },
  scale: {
    name: 'Scale',
    price: 'R$ 697',
    period: '/mês',
    color: 'bg-gradient-to-r from-amber-400 to-orange-500',
    popular: false,
    features: [
      'Leads ilimitados',
      'Agentes ilimitados',
      'Campanhas ilimitadas',
      'Suporte prioritário',
      'SSO / Login corporativo',
      'Gerente de conta dedicado',
    ],
  },
}

export function UpgradeModal() {
  const navigate = useNavigate()
  const { isOpen, context, closeUpgradeModal } = useUpgradeStore()
  const { getPlanTier, getPlanName } = useAuthStore()
  
  const currentPlan = getPlanTier()
  const currentPlanName = getPlanName()
  
  if (!context) return null
  
  const messageInfo = UPGRADE_MESSAGES[context.reason]
  
  // Determina o próximo plano baseado no plano atual do usuário
  const suggestedPlan = getSuggestedPlan(currentPlan, context.reason)
  const planDetails = PLAN_DETAILS[suggestedPlan]
  
  // Determinar quais planos mostrar (apenas superiores ao atual)
  const planOrder = ['free', 'starter', 'pro', 'scale']
  const currentIndex = planOrder.indexOf(currentPlan)
  const availablePlans = (['starter', 'pro', 'scale'] as const).filter(
    (plan) => planOrder.indexOf(plan) > currentIndex
  )
  
  const handleSelectPlan = (plan: string) => {
    closeUpgradeModal()
    navigate(`/upgrade?selected=${plan}`)
  }
  
  const handleViewAllPlans = () => {
    closeUpgradeModal()
    navigate('/upgrade')
  }

  return (
    <Dialog open={isOpen} onOpenChange={closeUpgradeModal}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="text-4xl">{messageInfo.icon}</div>
            <div>
              <DialogTitle className="text-xl">{messageInfo.title}</DialogTitle>
              <DialogDescription className="mt-1">
                {context.customMessage || messageInfo.description}
              </DialogDescription>
            </div>
          </div>
          
          {/* Mostrar uso atual se disponível */}
          {context.currentValue !== undefined && context.limitValue !== undefined && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center justify-between text-sm">
                <span className="text-red-700">Uso atual:</span>
                <span className="font-bold text-red-700">
                  {context.currentValue} / {context.limitValue}
                </span>
              </div>
              <div className="mt-2 h-2 bg-red-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-red-500 rounded-full"
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          )}
        </DialogHeader>
        
        {/* Plano Sugerido */}
        <div className="mt-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-5 w-5 text-amber-500" />
            <span className="font-medium">Plano recomendado para você:</span>
          </div>
          
          <Card className={`border-2 ${suggestedPlan === 'pro' ? 'border-purple-500' : suggestedPlan === 'scale' ? 'border-amber-500' : 'border-blue-500'}`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {suggestedPlan === 'scale' && <Crown className="h-5 w-5 text-amber-500" />}
                  <span className="font-bold text-lg">{planDetails.name}</span>
                  {planDetails.popular && (
                    <Badge className="bg-purple-100 text-purple-700 text-xs">
                      Mais popular
                    </Badge>
                  )}
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold">{planDetails.price}</span>
                  <span className="text-muted-foreground text-sm">{planDetails.period}</span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-2 mb-4">
                {planDetails.features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
              
              <Button 
                className={`w-full ${suggestedPlan === 'scale' ? 'bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600' : suggestedPlan === 'pro' ? 'bg-purple-600 hover:bg-purple-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                onClick={() => handleSelectPlan(suggestedPlan)}
              >
                <Zap className="mr-2 h-4 w-4" />
                Fazer Upgrade para {planDetails.name}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        </div>
        
        {/* Outros planos disponíveis */}
        {availablePlans.length > 1 && (
          <div className="mt-4">
            <p className="text-sm text-muted-foreground mb-2">Outros planos disponíveis:</p>
            <div className="flex gap-2">
              {availablePlans
                .filter((plan) => plan !== suggestedPlan)
                .map((plan) => (
                  <Button
                    key={plan}
                    variant="outline"
                    size="sm"
                    onClick={() => handleSelectPlan(plan)}
                    className="flex-1"
                  >
                    {PLAN_DETAILS[plan].name} - {PLAN_DETAILS[plan].price}
                  </Button>
                ))}
            </div>
          </div>
        )}
        
        <DialogFooter className="mt-4 flex-col sm:flex-row gap-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Plano atual:</span>
            <Badge variant="outline">{currentPlanName}</Badge>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={closeUpgradeModal}>
              Agora não
            </Button>
            <Button variant="link" onClick={handleViewAllPlans}>
              Ver todos os planos
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
