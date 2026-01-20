import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Users, Bot, Target, MessageSquare, TrendingUp, TrendingDown } from 'lucide-react'
import api from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore } from '@/stores/authStore'
import { 
  UsageLimitsCard, 
  FunnelChart, 
  CampaignComparison, 
  InteractionHistory,
  UpgradePrompt 
} from '@/components/dashboard'

// Types
interface DashboardMetrics {
  total_leads: number
  active_agents: number
  active_campaigns: number
  messages_sent_today: number
  response_rate: number
  conversion_rate: number
}

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

interface FunnelData {
  campaign_id?: string
  campaign_name?: string
  stages: Array<{
    name: string
    count: number
    percentage: number
    color: string
  }>
  total_leads: number
  total_conversions: number
  overall_conversion_rate: number
}

interface CampaignComparisonData {
  campaigns: Array<{
    campaign_id: string
    campaign_name: string
    status: string
    created_at: string
    total_leads: number
    messages_sent: number
    messages_delivered: number
    messages_read: number
    replies_received: number
    conversions: number
    delivery_rate: number
    read_rate: number
    reply_rate: number
    conversion_rate: number
    performance_score: number
  }>
  best_performer_id?: string
  worst_performer_id?: string
  avg_reply_rate: number
  avg_conversion_rate: number
}

interface InteractionHistoryData {
  items: Array<{
    id: string
    lead_id: string
    lead_name: string
    lead_source: string
    campaign_id: string
    campaign_name: string
    last_message?: string
    last_message_at?: string
    status: string
    total_messages: number
    reply_count: number
  }>
  total: number
  page: number
  page_size: number
  total_pages: number
}

interface RecentActivity {
  id: string
  type: 'message' | 'lead' | 'campaign'
  description: string
  timestamp: string
}

interface TopAgent {
  id: string
  name: string
  messages_sent: number
  response_rate: number
}

// Components
interface StatCardProps {
  title: string
  value: string | number
  description?: string
  icon: React.ReactNode
  trend?: {
    value: number
    isPositive: boolean
  }
}

function StatCard({ title, value, description, icon, trend }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
        {trend && (
          <div className={`flex items-center text-xs ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {trend.isPositive ? <TrendingUp className="mr-1 h-3 w-3" /> : <TrendingDown className="mr-1 h-3 w-3" />}
            {trend.value}% em relação à semana anterior
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function RecentActivities({ activities }: { activities: RecentActivity[] }) {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'message':
        return <MessageSquare className="h-4 w-4 text-blue-500" />
      case 'lead':
        return <Users className="h-4 w-4 text-green-500" />
      case 'campaign':
        return <Target className="h-4 w-4 text-purple-500" />
      default:
        return null
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Atividades Recentes</CardTitle>
        <CardDescription>Últimas atividades na plataforma</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              Nenhuma atividade recente
            </p>
          ) : (
            activities.map((activity) => (
              <div key={activity.id} className="flex items-center gap-4">
                {getActivityIcon(activity.type)}
                <div className="flex-1 space-y-1">
                  <p className="text-sm">{activity.description}</p>
                  <p className="text-xs text-muted-foreground">{activity.timestamp}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function TopAgents({ agents }: { agents: TopAgent[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Agentes</CardTitle>
        <CardDescription>Agentes com melhor desempenho</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {agents.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              Nenhum agente cadastrado
            </p>
          ) : (
            agents.map((agent, index) => (
              <div key={agent.id} className="flex items-center gap-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{agent.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {agent.messages_sent} mensagens • {agent.response_rate}% resposta
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Main Dashboard Component
export default function Dashboard() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { hasFeature, getPlanName } = useAuthStore()
  
  // State
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [usageLimits, setUsageLimits] = useState<UsageLimits | null>(null)
  const [activities, setActivities] = useState<RecentActivity[]>([])
  const [topAgents, setTopAgents] = useState<TopAgent[]>([])
  const [funnelData, setFunnelData] = useState<FunnelData | null>(null)
  const [comparisonData, setComparisonData] = useState<CampaignComparisonData | null>(null)
  const [historyData, setHistoryData] = useState<InteractionHistoryData | null>(null)
  const [historyPage, setHistoryPage] = useState(1)
  
  const [isLoading, setIsLoading] = useState(true)
  const [isFunnelLoading, setIsFunnelLoading] = useState(false)
  const [isComparisonLoading, setIsComparisonLoading] = useState(false)
  const [isHistoryLoading, setIsHistoryLoading] = useState(false)

  // Check features
  const canViewFunnel = hasFeature('funnel_reports')
  const canViewComparison = hasFeature('campaign_comparison')
  const planName = getPlanName()

  // Fetch basic dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [metricsRes, activitiesRes, usageRes] = await Promise.all([
          api.get('/dashboard/metrics'),
          api.get('/dashboard/recent-activities'),
          api.get('/dashboard/usage-limits'),
        ])
        
        setMetrics(metricsRes.data)
        setActivities(activitiesRes.data.activities || [])
        setTopAgents(activitiesRes.data.top_agents || [])
        setUsageLimits(usageRes.data)
      } catch (error: any) {
        toast({
          variant: 'destructive',
          title: 'Erro ao carregar dashboard',
          description: 'Não foi possível carregar os dados do dashboard.',
        })
        setMetrics({
          total_leads: 0,
          active_agents: 0,
          active_campaigns: 0,
          messages_sent_today: 0,
          response_rate: 0,
          conversion_rate: 0,
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
  }, [toast])

  // Fetch funnel data (if allowed)
  useEffect(() => {
    if (!canViewFunnel) return
    
    const fetchFunnelData = async () => {
      setIsFunnelLoading(true)
      try {
        const response = await api.get('/dashboard/funnel-report')
        setFunnelData(response.data)
      } catch (error) {
        console.error('Failed to load funnel data:', error)
      } finally {
        setIsFunnelLoading(false)
      }
    }
    
    fetchFunnelData()
  }, [canViewFunnel])

  // Fetch campaign comparison data (if allowed)
  useEffect(() => {
    if (!canViewComparison) return
    
    const fetchComparisonData = async () => {
      setIsComparisonLoading(true)
      try {
        const response = await api.get('/dashboard/campaign-comparison')
        setComparisonData(response.data)
      } catch (error) {
        console.error('Failed to load comparison data:', error)
      } finally {
        setIsComparisonLoading(false)
      }
    }
    
    fetchComparisonData()
  }, [canViewComparison])

  // Fetch interaction history
  const fetchHistoryData = useCallback(async (page: number) => {
    setIsHistoryLoading(true)
    try {
      const response = await api.get('/dashboard/interaction-history', {
        params: { page, page_size: 10 }
      })
      setHistoryData(response.data)
    } catch (error) {
      console.error('Failed to load history data:', error)
    } finally {
      setIsHistoryLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistoryData(historyPage)
  }, [historyPage, fetchHistoryData])

  // Handlers
  const handleUpgrade = () => {
    navigate('/plans')
  }

  const handleHistoryPageChange = (page: number) => {
    setHistoryPage(page)
  }

  const handleViewLead = (leadId: string) => {
    navigate(`/prospects/${leadId}`)
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
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Visão geral das suas métricas e atividades
        </p>
      </div>

      {/* Main KPIs - Available for all plans */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total de Leads"
          value={metrics?.total_leads || 0}
          description="Leads cadastrados"
          icon={<Users className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          title="Agentes Ativos"
          value={metrics?.active_agents || 0}
          description="Agentes em operação"
          icon={<Bot className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          title="Campanhas Ativas"
          value={metrics?.active_campaigns || 0}
          description="Campanhas em andamento"
          icon={<Target className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          title="Mensagens Hoje"
          value={metrics?.messages_sent_today || 0}
          description="Mensagens enviadas"
          icon={<MessageSquare className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* Rates Cards & Usage Limits */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Taxa de Resposta</CardTitle>
            <CardDescription>Percentual de respostas recebidas</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-primary">
              {metrics?.response_rate || 0}%
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Média de respostas das últimas campanhas
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Taxa de Conversão</CardTitle>
            <CardDescription>Percentual de conversões</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-green-600">
              {metrics?.conversion_rate || 0}%
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Leads convertidos em clientes
            </p>
          </CardContent>
        </Card>
        
        {/* Usage Limits Card */}
        {usageLimits && (
          <UsageLimitsCard 
            usage={usageLimits} 
            onUpgrade={handleUpgrade}
          />
        )}
      </div>

      {/* Funnel Reports - Starter+ only */}
      <div className="grid gap-4 lg:grid-cols-3">
        {canViewFunnel ? (
          funnelData && (
            <FunnelChart 
              data={funnelData} 
              isLoading={isFunnelLoading}
            />
          )
        ) : (
          <div className="lg:col-span-2">
            <UpgradePrompt
              feature="Relatórios de Funil de Conversão"
              description="Visualize todo o funil de vendas, desde a descoberta até a conversão. Identifique gargalos e otimize suas campanhas."
              requiredPlan="starter"
              currentPlan={planName}
              onUpgrade={handleUpgrade}
            />
          </div>
        )}
        
        {/* Recent Activities & Top Agents */}
        <div className="space-y-4">
          <RecentActivities activities={activities} />
          <TopAgents agents={topAgents} />
        </div>
      </div>

      {/* Campaign Comparison - Pro+ only */}
      {canViewComparison ? (
        comparisonData && (
          <CampaignComparison 
            data={comparisonData}
            isLoading={isComparisonLoading}
          />
        )
      ) : (
        <UpgradePrompt
          feature="Comparativo de Performance entre Campanhas"
          description="Compare o desempenho de todas as suas campanhas lado a lado. Descubra quais estratégias geram mais conversões."
          requiredPlan="pro"
          currentPlan={planName}
          onUpgrade={handleUpgrade}
        />
      )}

      {/* Interaction History (CRM Basic) - All plans */}
      {historyData && (
        <InteractionHistory
          data={historyData}
          isLoading={isHistoryLoading}
          onPageChange={handleHistoryPageChange}
          onViewLead={handleViewLead}
        />
      )}
    </div>
  )
}
