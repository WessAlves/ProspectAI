import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type UserRole = 'admin' | 'common'
type PlanTier = 'free' | 'starter' | 'pro' | 'scale'

// Limites e features por plano
const PLAN_FEATURES: Record<PlanTier, {
  prospects_per_month: number
  agents: number
  campaigns: number
  whatsapp_enabled: boolean
  whatsapp_official_api: boolean
  advanced_filters: boolean
  funnel_reports: boolean
  campaign_comparison: boolean
  crm_integration: boolean
  priority_support: boolean
  sso: boolean
}> = {
  free: {
    prospects_per_month: 50,
    agents: 1,
    campaigns: 1,
    whatsapp_enabled: false,
    whatsapp_official_api: false,
    advanced_filters: false,
    funnel_reports: false,
    campaign_comparison: false,
    crm_integration: false,
    priority_support: false,
    sso: false,
  },
  starter: {
    prospects_per_month: 500,
    agents: 1,
    campaigns: 3,
    whatsapp_enabled: true,
    whatsapp_official_api: false,
    advanced_filters: true,
    funnel_reports: true,
    campaign_comparison: false,
    crm_integration: false,
    priority_support: false,
    sso: false,
  },
  pro: {
    prospects_per_month: 2000,
    agents: 5,
    campaigns: 10,
    whatsapp_enabled: true,
    whatsapp_official_api: true,
    advanced_filters: true,
    funnel_reports: true,
    campaign_comparison: true,
    crm_integration: true,
    priority_support: false,
    sso: false,
  },
  scale: {
    prospects_per_month: -1, // ilimitado
    agents: -1,
    campaigns: -1,
    whatsapp_enabled: true,
    whatsapp_official_api: true,
    advanced_filters: true,
    funnel_reports: true,
    campaign_comparison: true,
    crm_integration: true,
    priority_support: true,
    sso: true,
  },
}

interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  plan_tier: PlanTier
  is_active: boolean
  is_admin: boolean
  profile_completed: boolean
  person_type?: 'individual' | 'company' | null
  created_at: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  
  // Actions
  setUser: (user: User) => void
  setTokens: (accessToken: string, refreshToken: string) => void
  login: (user: User, accessToken: string, refreshToken: string) => void
  logout: () => void
  refreshUser: () => Promise<void>
  
  // Computed
  isAdmin: () => boolean
  hasFeature: (feature: keyof typeof PLAN_FEATURES.free) => boolean
  getPlanFeatures: () => typeof PLAN_FEATURES.free
  getPlanTier: () => PlanTier
  getPlanName: () => string
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      
      setUser: (user) => set({ user }),
      
      setTokens: (accessToken, refreshToken) => set({
        accessToken,
        refreshToken,
        isAuthenticated: true,
      }),
      
      login: (user, accessToken, refreshToken) => set({
        user,
        accessToken,
        refreshToken,
        isAuthenticated: true,
      }),
      
      logout: () => set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
      }),
      
      refreshUser: async () => {
        const { accessToken } = get()
        if (!accessToken) return
        
        try {
          const response = await fetch('/api/v1/auth/me', {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
            },
          })
          
          if (response.ok) {
            const user = await response.json()
            set({ user })
          }
        } catch (error) {
          console.error('Error refreshing user:', error)
        }
      },
      
      isAdmin: () => {
        const user = get().user
        return user?.is_admin || user?.role === 'admin' || false
      },
      
      hasFeature: (feature: keyof typeof PLAN_FEATURES.free) => {
        const user = get().user
        if (!user) return false
        const tier = user.plan_tier as PlanTier
        const value = PLAN_FEATURES[tier]?.[feature]
        // Features booleanas retornam true/false, limites numéricos retornam true se > 0 ou == -1 (ilimitado)
        if (typeof value === 'boolean') return value
        if (typeof value === 'number') return value === -1 || value > 0
        return false
      },
      
      getPlanFeatures: () => {
        const user = get().user
        const tier = (user?.plan_tier || 'free') as PlanTier
        return PLAN_FEATURES[tier]
      },
      
      getPlanTier: () => {
        const user = get().user
        return (user?.plan_tier || 'free') as PlanTier
      },
      
      getPlanName: () => {
        const user = get().user
        const tier = (user?.plan_tier || 'free') as PlanTier
        const names: Record<PlanTier, string> = {
          free: 'Free',
          starter: 'Starter',
          pro: 'Pro',
          scale: 'Scale',
        }
        return names[tier]
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state: AuthState) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export { PLAN_FEATURES }
export type { PlanTier, User }
