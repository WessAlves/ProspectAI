import { useCallback, useEffect, useState } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { useUpgradeStore } from '@/stores/upgradeStore'
import api from '@/lib/api'

interface UsageLimits {
  plan_tier: string
  leads_limit: number
  leads_used: number
  leads_remaining: number
  agents_limit: number
  agents_used: number
  agents_remaining: number
  campaigns_limit: number
  campaigns_used: number
  campaigns_remaining: number
  whatsapp_enabled: boolean
  whatsapp_official_api: boolean
  advanced_filters: boolean
  funnel_reports: boolean
  campaign_comparison: boolean
  crm_integration: boolean
  priority_support: boolean
  sso: boolean
}

export function usePlanLimits() {
  const [usageLimits, setUsageLimits] = useState<UsageLimits | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { getPlanFeatures, getPlanTier } = useAuthStore()
  const { 
    showLeadsLimitReached, 
    showAgentsLimitReached, 
    showCampaignsLimitReached,
    openUpgradeModal 
  } = useUpgradeStore()
  
  // Buscar limites de uso do backend
  const fetchUsageLimits = useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await api.get('/dashboard/usage-limits')
      setUsageLimits(response.data)
    } catch (error) {
      console.error('Erro ao carregar limites de uso:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])
  
  useEffect(() => {
    fetchUsageLimits()
  }, [fetchUsageLimits])
  
  // Verificar se pode criar mais leads
  const canCreateLead = useCallback(() => {
    if (!usageLimits) return true // Permitir se ainda não carregou
    if (usageLimits.leads_limit === -1) return true // Ilimitado
    return usageLimits.leads_used < usageLimits.leads_limit
  }, [usageLimits])
  
  // Verificar se pode criar mais agentes
  const canCreateAgent = useCallback(() => {
    if (!usageLimits) return true
    if (usageLimits.agents_limit === -1) return true
    return usageLimits.agents_used < usageLimits.agents_limit
  }, [usageLimits])
  
  // Verificar se pode criar mais campanhas
  const canCreateCampaign = useCallback(() => {
    if (!usageLimits) return true
    if (usageLimits.campaigns_limit === -1) return true
    return usageLimits.campaigns_used < usageLimits.campaigns_limit
  }, [usageLimits])
  
  // Verificar e mostrar modal se limite atingido
  const checkLeadsLimit = useCallback(() => {
    if (!usageLimits) return true
    if (usageLimits.leads_limit === -1) return true
    
    if (usageLimits.leads_used >= usageLimits.leads_limit) {
      showLeadsLimitReached(usageLimits.leads_used, usageLimits.leads_limit)
      return false
    }
    return true
  }, [usageLimits, showLeadsLimitReached])
  
  const checkAgentsLimit = useCallback(() => {
    if (!usageLimits) return true
    if (usageLimits.agents_limit === -1) return true
    
    if (usageLimits.agents_used >= usageLimits.agents_limit) {
      showAgentsLimitReached(usageLimits.agents_used, usageLimits.agents_limit)
      return false
    }
    return true
  }, [usageLimits, showAgentsLimitReached])
  
  const checkCampaignsLimit = useCallback(() => {
    if (!usageLimits) return true
    if (usageLimits.campaigns_limit === -1) return true
    
    if (usageLimits.campaigns_used >= usageLimits.campaigns_limit) {
      showCampaignsLimitReached(usageLimits.campaigns_used, usageLimits.campaigns_limit)
      return false
    }
    return true
  }, [usageLimits, showCampaignsLimitReached])
  
  // Verificar feature específica
  const checkFeature = useCallback((feature: keyof UsageLimits, featureName: string, suggestedPlan: 'starter' | 'pro' | 'scale') => {
    if (!usageLimits) return true
    
    const hasFeature = usageLimits[feature]
    if (!hasFeature) {
      openUpgradeModal({
        reason: 'general',
        featureName,
        suggestedPlan,
        customMessage: `${featureName} não está disponível no seu plano atual. Faça upgrade para ${suggestedPlan.charAt(0).toUpperCase() + suggestedPlan.slice(1)} ou superior.`,
      })
      return false
    }
    return true
  }, [usageLimits, openUpgradeModal])
  
  // Verificar WhatsApp
  const checkWhatsApp = useCallback(() => {
    return checkFeature('whatsapp_enabled', 'WhatsApp', 'starter')
  }, [checkFeature])
  
  // Verificar API Oficial WhatsApp
  const checkWhatsAppOfficial = useCallback(() => {
    return checkFeature('whatsapp_official_api', 'API Oficial do WhatsApp', 'pro')
  }, [checkFeature])
  
  // Verificar Filtros Avançados
  const checkAdvancedFilters = useCallback(() => {
    return checkFeature('advanced_filters', 'Filtros Avançados', 'starter')
  }, [checkFeature])
  
  return {
    usageLimits,
    isLoading,
    refetch: fetchUsageLimits,
    
    // Checagens simples (retornam boolean)
    canCreateLead,
    canCreateAgent,
    canCreateCampaign,
    
    // Checagens com modal (retornam boolean e mostram modal se necessário)
    checkLeadsLimit,
    checkAgentsLimit,
    checkCampaignsLimit,
    checkFeature,
    checkWhatsApp,
    checkWhatsAppOfficial,
    checkAdvancedFilters,
    
    // Dados do plano
    planFeatures: getPlanFeatures(),
    planTier: getPlanTier(),
  }
}
