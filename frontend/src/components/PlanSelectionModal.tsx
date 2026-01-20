import { useState } from 'react'
import { Check, X, Sparkles, Zap, Rocket, Building2, Crown } from 'lucide-react'
import {
  Dialog,
  DialogContent,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export interface Plan {
  id: string
  name: string
  price: number
  priceLabel: string
  description: string
  icon: React.ReactNode
  popular?: boolean
  features: {
    name: string
    included: boolean
  }[]
  limits: {
    prospects: string
    agents: string
    campaigns: string
  }
}

const plans: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    priceLabel: 'Grátis',
    description: 'Teste a qualidade da prospecção e da IA',
    icon: <Sparkles className="h-5 w-5" />,
    features: [
      { name: 'Busca Google (Localização/Nicho)', included: true },
      { name: 'Busca Instagram (Seguidores/Atividade)', included: true },
      { name: 'Filtros Avançados de Qualificação', included: false },
      { name: 'Instagram Direct', included: true },
      { name: 'WhatsApp (Simulação)', included: false },
      { name: 'WhatsApp Business API Oficial', included: false },
      { name: 'Dashboard Básico', included: true },
      { name: 'Histórico de Interações', included: true },
      { name: 'Relatórios de Funil', included: false },
      { name: 'Comparativo de Campanhas', included: false },
      { name: 'Integração com CRM', included: false },
      { name: 'Suporte por Email', included: false },
      { name: 'Suporte Prioritário', included: false },
      { name: 'SSO (Single Sign-On)', included: false },
    ],
    limits: {
      prospects: '50/mês',
      agents: '1 Agente',
      campaigns: '1 Campanha',
    },
  },
  {
    id: 'starter',
    name: 'Starter',
    price: 199.90,
    priceLabel: 'R$ 199,90',
    description: 'Ideal para empreendedores iniciando',
    icon: <Zap className="h-5 w-5" />,
    features: [
      { name: 'Busca Google (Localização/Nicho)', included: true },
      { name: 'Busca Instagram (Seguidores/Atividade)', included: true },
      { name: 'Filtros Avançados de Qualificação', included: true },
      { name: 'Instagram Direct', included: true },
      { name: 'WhatsApp (Simulação)', included: true },
      { name: 'WhatsApp Business API Oficial', included: false },
      { name: 'Dashboard Básico', included: true },
      { name: 'Histórico de Interações', included: true },
      { name: 'Relatórios de Funil', included: true },
      { name: 'Comparativo de Campanhas', included: false },
      { name: 'Integração com CRM', included: false },
      { name: 'Suporte por Email', included: true },
      { name: 'Suporte Prioritário', included: false },
      { name: 'SSO (Single Sign-On)', included: false },
    ],
    limits: {
      prospects: '500/mês',
      agents: '1 Agente',
      campaigns: '3 Campanhas',
    },
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 399.90,
    priceLabel: 'R$ 399,90',
    description: 'Para agências que buscam escala',
    icon: <Rocket className="h-5 w-5" />,
    popular: true,
    features: [
      { name: 'Busca Google (Localização/Nicho)', included: true },
      { name: 'Busca Instagram (Seguidores/Atividade)', included: true },
      { name: 'Filtros Avançados de Qualificação', included: true },
      { name: 'Instagram Direct', included: true },
      { name: 'WhatsApp (Simulação)', included: true },
      { name: 'WhatsApp Business API Oficial', included: true },
      { name: 'Dashboard Básico', included: true },
      { name: 'Histórico de Interações', included: true },
      { name: 'Relatórios de Funil', included: true },
      { name: 'Comparativo de Campanhas', included: true },
      { name: 'Integração com CRM', included: true },
      { name: 'Suporte por Email', included: true },
      { name: 'Suporte Prioritário', included: false },
      { name: 'SSO (Single Sign-On)', included: false },
    ],
    limits: {
      prospects: '2.000/mês',
      agents: '5 Agentes',
      campaigns: '10 Campanhas',
    },
  },
  {
    id: 'scale',
    name: 'Scale',
    price: 799.90,
    priceLabel: 'R$ 799,90',
    description: 'Para grandes agências',
    icon: <Building2 className="h-5 w-5" />,
    features: [
      { name: 'Busca Google (Localização/Nicho)', included: true },
      { name: 'Busca Instagram (Seguidores/Atividade)', included: true },
      { name: 'Filtros Avançados de Qualificação', included: true },
      { name: 'Instagram Direct', included: true },
      { name: 'WhatsApp (Simulação)', included: true },
      { name: 'WhatsApp Business API Oficial', included: true },
      { name: 'Dashboard Básico', included: true },
      { name: 'Histórico de Interações', included: true },
      { name: 'Relatórios de Funil', included: true },
      { name: 'Comparativo de Campanhas', included: true },
      { name: 'Integração com CRM', included: true },
      { name: 'Suporte por Email', included: true },
      { name: 'Suporte Prioritário', included: true },
      { name: 'SSO (Single Sign-On)', included: true },
    ],
    limits: {
      prospects: 'Ilimitado',
      agents: 'Ilimitado',
      campaigns: 'Ilimitado',
    },
  },
]

// Lista única de todas as features para a tabela comparativa
const allFeatures = [
  'Busca Google (Localização/Nicho)',
  'Busca Instagram (Seguidores/Atividade)',
  'Filtros Avançados de Qualificação',
  'Instagram Direct',
  'WhatsApp (Simulação)',
  'WhatsApp Business API Oficial',
  'Dashboard Básico',
  'Histórico de Interações',
  'Relatórios de Funil',
  'Comparativo de Campanhas',
  'Integração com CRM',
  'Suporte por Email',
  'Suporte Prioritário',
  'SSO (Single Sign-On)',
]

interface PlanSelectionModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelectPlan: (planId: string) => void
  selectedPlan?: string
  isLoading?: boolean
}

export function PlanSelectionModal({
  open,
  onOpenChange,
  onSelectPlan,
  selectedPlan,
  isLoading = false,
}: PlanSelectionModalProps) {
  const [localSelectedPlan, setLocalSelectedPlan] = useState<string>(selectedPlan || 'free')

  const handleSelectPlan = (planId: string) => {
    setLocalSelectedPlan(planId)
  }

  const handleConfirm = () => {
    onSelectPlan(localSelectedPlan)
  }

  const getPlanFeatureStatus = (planId: string, featureName: string): boolean => {
    const plan = plans.find(p => p.id === planId)
    const feature = plan?.features.find(f => f.name === featureName)
    return feature?.included || false
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] w-full h-[95vh] max-h-[95vh] p-0 overflow-hidden flex flex-col">
        {/* Header fixo */}
        <div className="flex-shrink-0 p-6 pb-4 border-b bg-background">
          <div className="text-center">
            <h2 className="text-2xl font-bold flex items-center justify-center gap-2">
              <Crown className="h-6 w-6 text-primary" />
              Escolha seu plano
            </h2>
            <p className="text-muted-foreground mt-1">
              Comece gratuitamente ou escolha o plano ideal para suas necessidades
            </p>
          </div>
        </div>

        {/* Conteúdo com scroll */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Cards dos planos no topo */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {plans.map((plan) => (
              <div
                key={plan.id}
                onClick={() => handleSelectPlan(plan.id)}
                className={cn(
                  'relative rounded-xl border-2 p-4 cursor-pointer transition-all',
                  localSelectedPlan === plan.id
                    ? 'border-primary bg-primary/5 shadow-lg scale-[1.02]'
                    : 'border-border hover:border-primary/50 hover:shadow-md',
                  plan.popular && 'ring-2 ring-primary ring-offset-2'
                )}
              >
                {plan.popular && (
                  <Badge className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs">
                    Mais Popular
                  </Badge>
                )}

                <div className="flex items-center gap-3 mb-3">
                  <div className={cn(
                    'p-2 rounded-lg',
                    localSelectedPlan === plan.id
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  )}>
                    {plan.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold">{plan.name}</h3>
                    <p className="text-xs text-muted-foreground">{plan.description}</p>
                  </div>
                </div>

                <div className="mb-3">
                  <span className="text-2xl font-bold text-primary">{plan.priceLabel}</span>
                  {plan.price > 0 && <span className="text-sm text-muted-foreground">/mês</span>}
                </div>

                {/* Limites */}
                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Prospects:</span>
                    <span className="font-medium">{plan.limits.prospects}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Agentes IA:</span>
                    <span className="font-medium">{plan.limits.agents}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Campanhas:</span>
                    <span className="font-medium">{plan.limits.campaigns}</span>
                  </div>
                </div>

                <Button
                  variant={localSelectedPlan === plan.id ? 'default' : 'outline'}
                  className="w-full mt-4"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleSelectPlan(plan.id)
                  }}
                >
                  {localSelectedPlan === plan.id ? '✓ Selecionado' : 'Selecionar'}
                </Button>
              </div>
            ))}
          </div>

          {/* Tabela comparativa de funcionalidades */}
          <div className="rounded-xl border overflow-hidden">
            <div className="bg-muted/50 px-4 py-3 border-b">
              <h3 className="font-semibold text-lg">Comparativo de Funcionalidades</h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/30">
                    <th className="text-left p-3 font-medium min-w-[250px]">Funcionalidade</th>
                    {plans.map((plan) => (
                      <th
                        key={plan.id}
                        className={cn(
                          'text-center p-3 font-medium min-w-[120px]',
                          localSelectedPlan === plan.id && 'bg-primary/10'
                        )}
                      >
                        <div className="flex items-center justify-center gap-1.5">
                          {plan.icon}
                          <span>{plan.name}</span>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {/* Limites */}
                  <tr className="border-b bg-muted/20">
                    <td className="p-3 font-medium text-sm" colSpan={5}>
                      📊 Limites de Uso
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-3 text-sm">Prospects por mês</td>
                    {plans.map((plan) => (
                      <td
                        key={plan.id}
                        className={cn(
                          'text-center p-3 text-sm font-medium',
                          localSelectedPlan === plan.id && 'bg-primary/10'
                        )}
                      >
                        {plan.limits.prospects}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-3 text-sm">Agentes de IA</td>
                    {plans.map((plan) => (
                      <td
                        key={plan.id}
                        className={cn(
                          'text-center p-3 text-sm font-medium',
                          localSelectedPlan === plan.id && 'bg-primary/10'
                        )}
                      >
                        {plan.limits.agents}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-3 text-sm">Campanhas simultâneas</td>
                    {plans.map((plan) => (
                      <td
                        key={plan.id}
                        className={cn(
                          'text-center p-3 text-sm font-medium',
                          localSelectedPlan === plan.id && 'bg-primary/10'
                        )}
                      >
                        {plan.limits.campaigns}
                      </td>
                    ))}
                  </tr>

                  {/* Funcionalidades */}
                  <tr className="border-b bg-muted/20">
                    <td className="p-3 font-medium text-sm" colSpan={5}>
                      ⚡ Funcionalidades
                    </td>
                  </tr>
                  {allFeatures.map((featureName, index) => (
                    <tr key={index} className="border-b hover:bg-muted/30 transition-colors">
                      <td className="p-3 text-sm">{featureName}</td>
                      {plans.map((plan) => (
                        <td
                          key={plan.id}
                          className={cn(
                            'text-center p-3',
                            localSelectedPlan === plan.id && 'bg-primary/10'
                          )}
                        >
                          {getPlanFeatureStatus(plan.id, featureName) ? (
                            <Check className="h-5 w-5 text-green-500 mx-auto" />
                          ) : (
                            <X className="h-5 w-5 text-muted-foreground/30 mx-auto" />
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer fixo */}
        <div className="flex-shrink-0 border-t bg-background p-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 max-w-4xl mx-auto">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>💡</span>
              <span>Você pode alterar seu plano a qualquer momento</span>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isLoading}
              >
                Cancelar
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={isLoading}
                className="min-w-[150px]"
              >
                {isLoading ? (
                  'Processando...'
                ) : (
                  <>
                    Continuar com{' '}
                    <span className="font-bold ml-1">
                      {plans.find(p => p.id === localSelectedPlan)?.name}
                    </span>
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export { plans }
export type { PlanSelectionModalProps }
