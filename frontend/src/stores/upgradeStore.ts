import { create } from 'zustand'

export type UpgradeReason = 
  | 'leads_limit'
  | 'agents_limit'
  | 'campaigns_limit'
  | 'whatsapp'
  | 'whatsapp_official'
  | 'advanced_filters'
  | 'funnel_reports'
  | 'campaign_comparison'
  | 'crm_integration'
  | 'priority_support'
  | 'sso'
  | 'general'

interface UpgradeContext {
  reason: UpgradeReason
  currentValue?: number
  limitValue?: number
  featureName?: string
  suggestedPlan?: 'starter' | 'pro' | 'scale'
  customMessage?: string
}

interface UpgradeState {
  isOpen: boolean
  context: UpgradeContext | null
  
  // Actions
  openUpgradeModal: (context: UpgradeContext) => void
  closeUpgradeModal: () => void
  
  // Helpers para abrir com contextos específicos
  showLeadsLimitReached: (used: number, limit: number) => void
  showAgentsLimitReached: (used: number, limit: number) => void
  showCampaignsLimitReached: (used: number, limit: number) => void
  showFeatureRequired: (featureName: string, suggestedPlan: 'starter' | 'pro' | 'scale') => void
}

// Mensagens e títulos por tipo de razão
export const UPGRADE_MESSAGES: Record<UpgradeReason, {
  title: string
  description: string
  icon: string
}> = {
  leads_limit: {
    title: 'Limite de Leads Atingido',
    description: 'Você atingiu o limite de leads do seu plano atual. Faça upgrade para continuar prospectando novos leads.',
    icon: '👥',
  },
  agents_limit: {
    title: 'Limite de Agentes Atingido',
    description: 'Você atingiu o limite de agentes de IA do seu plano. Faça upgrade para criar mais agentes.',
    icon: '🤖',
  },
  campaigns_limit: {
    title: 'Limite de Campanhas Atingido',
    description: 'Você atingiu o limite de campanhas do seu plano. Faça upgrade para criar mais campanhas.',
    icon: '📊',
  },
  whatsapp: {
    title: 'WhatsApp não Disponível',
    description: 'O envio de mensagens via WhatsApp não está disponível no seu plano atual.',
    icon: '💬',
  },
  whatsapp_official: {
    title: 'API Oficial do WhatsApp',
    description: 'A API oficial do WhatsApp Business não está disponível no seu plano atual.',
    icon: '✅',
  },
  advanced_filters: {
    title: 'Filtros Avançados',
    description: 'Os filtros avançados de prospecção não estão disponíveis no seu plano atual.',
    icon: '🔍',
  },
  funnel_reports: {
    title: 'Relatórios de Funil',
    description: 'Os relatórios de funil de conversão não estão disponíveis no seu plano atual.',
    icon: '📈',
  },
  campaign_comparison: {
    title: 'Comparativo de Campanhas',
    description: 'O comparativo de performance entre campanhas não está disponível no seu plano atual.',
    icon: '📊',
  },
  crm_integration: {
    title: 'Integração CRM',
    description: 'A integração com CRMs externos não está disponível no seu plano atual.',
    icon: '🔗',
  },
  priority_support: {
    title: 'Suporte Prioritário',
    description: 'O suporte prioritário não está disponível no seu plano atual.',
    icon: '⭐',
  },
  sso: {
    title: 'Single Sign-On (SSO)',
    description: 'O login único corporativo não está disponível no seu plano atual.',
    icon: '🔐',
  },
  general: {
    title: 'Faça Upgrade do seu Plano',
    description: 'Esta funcionalidade não está disponível no seu plano atual.',
    icon: '🚀',
  },
}

// Plano sugerido por feature (mínimo necessário para a feature)
export const MINIMUM_PLAN_FOR_FEATURE: Record<UpgradeReason, 'starter' | 'pro' | 'scale'> = {
  leads_limit: 'starter',
  agents_limit: 'starter',
  campaigns_limit: 'starter',
  whatsapp: 'starter',
  whatsapp_official: 'pro',
  advanced_filters: 'starter',
  funnel_reports: 'starter',
  campaign_comparison: 'pro',
  crm_integration: 'pro',
  priority_support: 'scale',
  sso: 'scale',
  general: 'starter',
}

// Função para obter o próximo plano baseado no atual
export function getNextPlan(currentPlan: string): 'starter' | 'pro' | 'scale' | null {
  const planOrder = ['free', 'starter', 'pro', 'scale']
  const currentIndex = planOrder.indexOf(currentPlan)
  
  if (currentIndex === -1 || currentIndex >= planOrder.length - 1) {
    return null // Já está no plano máximo ou plano inválido
  }
  
  return planOrder[currentIndex + 1] as 'starter' | 'pro' | 'scale'
}

// Função para determinar o plano sugerido baseado no plano atual e feature
export function getSuggestedPlan(
  currentPlan: string, 
  reason: UpgradeReason
): 'starter' | 'pro' | 'scale' {
  const nextPlan = getNextPlan(currentPlan)
  const minimumPlan = MINIMUM_PLAN_FOR_FEATURE[reason]
  
  // Se não há próximo plano (já está no scale), retorna scale
  if (!nextPlan) return 'scale'
  
  // Ordem dos planos para comparação
  const planOrder = ['free', 'starter', 'pro', 'scale']
  const nextPlanIndex = planOrder.indexOf(nextPlan)
  const minimumPlanIndex = planOrder.indexOf(minimumPlan)
  
  // Retorna o maior entre o próximo plano e o mínimo necessário para a feature
  return nextPlanIndex >= minimumPlanIndex ? nextPlan : minimumPlan
}

export const useUpgradeStore = create<UpgradeState>()((set) => ({
  isOpen: false,
  context: null,
  
  openUpgradeModal: (context) => set({
    isOpen: true,
    context: {
      ...context,
      suggestedPlan: context.suggestedPlan || MINIMUM_PLAN_FOR_FEATURE[context.reason],
    },
  }),
  
  closeUpgradeModal: () => set({
    isOpen: false,
    context: null,
  }),
  
  showLeadsLimitReached: (used, limit) => set({
    isOpen: true,
    context: {
      reason: 'leads_limit',
      currentValue: used,
      limitValue: limit,
      suggestedPlan: 'starter',
    },
  }),
  
  showAgentsLimitReached: (used, limit) => set({
    isOpen: true,
    context: {
      reason: 'agents_limit',
      currentValue: used,
      limitValue: limit,
      suggestedPlan: 'pro',
    },
  }),
  
  showCampaignsLimitReached: (used, limit) => set({
    isOpen: true,
    context: {
      reason: 'campaigns_limit',
      currentValue: used,
      limitValue: limit,
      suggestedPlan: 'starter',
    },
  }),
  
  showFeatureRequired: (featureName, suggestedPlan) => set({
    isOpen: true,
    context: {
      reason: 'general',
      featureName,
      suggestedPlan,
    },
  }),
}))
