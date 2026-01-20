import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { useUpgradeStore, MINIMUM_PLAN_FOR_FEATURE, UpgradeReason } from '@/stores/upgradeStore'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Mapear mensagens de erro do backend para razões de upgrade
const ERROR_TO_UPGRADE_REASON: Record<string, UpgradeReason> = {
  'limite de leads': 'leads_limit',
  'limite de prospects': 'leads_limit',
  'limite de agentes': 'agents_limit',
  'limite de campanhas': 'campaigns_limit',
  'whatsapp': 'whatsapp',
  'api oficial': 'whatsapp_official',
  'filtros avançados': 'advanced_filters',
  'relatórios de funil': 'funnel_reports',
  'funil': 'funnel_reports',
  'comparação de campanhas': 'campaign_comparison',
  'comparativo': 'campaign_comparison',
  'integração crm': 'crm_integration',
  'crm': 'crm_integration',
  'suporte prioritário': 'priority_support',
  'sso': 'sso',
}

// Detectar razão de upgrade a partir da mensagem de erro
function detectUpgradeReason(errorMessage: string): UpgradeReason {
  const lowerMessage = errorMessage.toLowerCase()
  
  for (const [keyword, reason] of Object.entries(ERROR_TO_UPGRADE_REASON)) {
    if (lowerMessage.includes(keyword)) {
      return reason
    }
  }
  
  return 'general'
}

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail?: string }>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    
    // Se não há config (erro de rede), rejeitar
    if (!originalRequest) {
      return Promise.reject(error)
    }
    
    // If 403 (Forbidden) - usually means plan limit or feature restriction
    if (error.response?.status === 403) {
      const detail = error.response.data?.detail || ''
      const reason = detectUpgradeReason(detail)
      
      // Abrir modal de upgrade com contexto
      useUpgradeStore.getState().openUpgradeModal({
        reason,
        customMessage: detail,
        suggestedPlan: MINIMUM_PLAN_FOR_FEATURE[reason],
      })
      
      return Promise.reject(error)
    }
    
    // If 401 (Unauthorized) - token inválido ou expirado
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const refreshToken = useAuthStore.getState().refreshToken
      
      if (refreshToken) {
        try {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })
          
          const { access_token, refresh_token } = response.data
          useAuthStore.getState().setTokens(access_token, refresh_token)
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh falhou - fazer logout e redirecionar
          console.warn('Sessão expirada. Redirecionando para login...')
          useAuthStore.getState().logout()
          window.location.href = '/login?expired=true'
          return Promise.reject(refreshError)
        }
      } else {
        // Sem refresh token - fazer logout e redirecionar
        console.warn('Token inválido. Redirecionando para login...')
        useAuthStore.getState().logout()
        window.location.href = '/login?expired=true'
      }
    }
    
    // Se já tentou retry e ainda deu 401, fazer logout
    if (error.response?.status === 401 && originalRequest._retry) {
      console.warn('Falha na autenticação após retry. Redirecionando para login...')
      useAuthStore.getState().logout()
      window.location.href = '/login?expired=true'
    }
    
    return Promise.reject(error)
  }
)

export default api

// API Types
export interface ApiError {
  detail: string
  error_code?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
