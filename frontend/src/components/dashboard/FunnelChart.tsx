import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Users, 
  Send, 
  CheckCheck, 
  Eye, 
  MessageSquare, 
  Target,
  ArrowDown
} from 'lucide-react'

interface FunnelStage {
  name: string
  count: number
  percentage: number
  color: string
}

interface FunnelData {
  campaign_id?: string
  campaign_name?: string
  stages: FunnelStage[]
  total_leads: number
  total_conversions: number
  overall_conversion_rate: number
  avg_time_to_reply?: number
  avg_messages_until_conversion?: number
  best_performing_day?: string
  best_performing_hour?: number
}

interface FunnelChartProps {
  data: FunnelData
  isLoading?: boolean
}

const STAGE_ICONS: Record<string, React.ElementType> = {
  'Encontrados': Users,
  'Contatados': Send,
  'Entregues': CheckCheck,
  'Lidas': Eye,
  'Responderam': MessageSquare,
  'Convertidos': Target,
}

export function FunnelChart({ data, isLoading }: FunnelChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Funil de Conversão</CardTitle>
          <CardDescription>Carregando...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const maxCount = Math.max(...data.stages.map(s => s.count), 1)

  return (
    <Card className="col-span-full lg:col-span-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Funil de Conversão</CardTitle>
            <CardDescription>
              {data.campaign_name ? `Campanha: ${data.campaign_name}` : 'Todas as campanhas'}
            </CardDescription>
          </div>
          <Badge variant={data.overall_conversion_rate >= 5 ? 'success' : 'secondary'}>
            {data.overall_conversion_rate.toFixed(1)}% conversão
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.stages.map((stage, index) => {
            const Icon = STAGE_ICONS[stage.name] || Users
            const widthPercent = Math.max((stage.count / maxCount) * 100, 10)
            const isLast = index === data.stages.length - 1
            
            return (
              <div key={stage.name} className="relative">
                <div className="flex items-center gap-4">
                  <div 
                    className="flex items-center gap-3 px-4 py-3 rounded-lg transition-all"
                    style={{ 
                      width: `${widthPercent}%`,
                      backgroundColor: stage.color,
                      minWidth: '200px'
                    }}
                  >
                    <Icon className="h-5 w-5 text-white" />
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-medium truncate">{stage.name}</p>
                      <p className="text-white/80 text-sm">
                        {stage.count.toLocaleString()} ({stage.percentage.toFixed(1)}%)
                      </p>
                    </div>
                  </div>
                </div>
                {!isLast && (
                  <div className="flex justify-center my-1">
                    <ArrowDown className="h-4 w-4 text-muted-foreground" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
        
        {/* Métricas adicionais */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t">
          <div className="text-center">
            <p className="text-2xl font-bold text-primary">{data.total_leads.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">Total Leads</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{data.total_conversions.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">Conversões</p>
          </div>
          {data.avg_time_to_reply && (
            <div className="text-center">
              <p className="text-2xl font-bold">{data.avg_time_to_reply.toFixed(1)}h</p>
              <p className="text-xs text-muted-foreground">Tempo médio resposta</p>
            </div>
          )}
          {data.best_performing_day && (
            <div className="text-center">
              <p className="text-2xl font-bold">{data.best_performing_day}</p>
              <p className="text-xs text-muted-foreground">Melhor dia</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
