import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  TrendingUp, 
  TrendingDown,
  Trophy,
  AlertTriangle,
  BarChart3
} from 'lucide-react'

interface CampaignComparisonItem {
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
}

interface CampaignComparisonData {
  campaigns: CampaignComparisonItem[]
  best_performer_id?: string
  worst_performer_id?: string
  avg_reply_rate: number
  avg_conversion_rate: number
}

interface CampaignComparisonProps {
  data: CampaignComparisonData
  isLoading?: boolean
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  paused: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-blue-100 text-blue-800',
  draft: 'bg-gray-100 text-gray-800',
}

function MetricBar({ value, maxValue, color }: { value: number; maxValue: number; color: string }) {
  const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0
  return (
    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
      <div 
        className={`h-full rounded-full ${color}`}
        style={{ width: `${Math.min(percentage, 100)}%` }}
      />
    </div>
  )
}

export function CampaignComparison({ data, isLoading }: CampaignComparisonProps) {
  if (isLoading) {
    return (
      <Card className="col-span-full">
        <CardHeader>
          <CardTitle>Comparativo de Campanhas</CardTitle>
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

  if (data.campaigns.length === 0) {
    return (
      <Card className="col-span-full">
        <CardHeader>
          <CardTitle>Comparativo de Campanhas</CardTitle>
          <CardDescription>Performance comparada entre campanhas</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
            <BarChart3 className="h-8 w-8 mb-2" />
            <p>Nenhuma campanha para comparar</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Encontrar valores máximos para as barras
  const maxLeads = Math.max(...data.campaigns.map(c => c.total_leads), 1)
  const maxMessages = Math.max(...data.campaigns.map(c => c.messages_sent), 1)
  const maxConversions = Math.max(...data.campaigns.map(c => c.conversions), 1)

  return (
    <Card className="col-span-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Comparativo de Campanhas</CardTitle>
            <CardDescription>Performance comparada entre campanhas</CardDescription>
          </div>
          <div className="flex gap-4 text-sm">
            <div className="text-center">
              <p className="font-semibold text-lg">{data.avg_reply_rate.toFixed(1)}%</p>
              <p className="text-muted-foreground text-xs">Média resposta</p>
            </div>
            <div className="text-center">
              <p className="font-semibold text-lg text-green-600">{data.avg_conversion_rate.toFixed(1)}%</p>
              <p className="text-muted-foreground text-xs">Média conversão</p>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-muted-foreground border-b">
                <th className="pb-3 font-medium">Campanha</th>
                <th className="pb-3 font-medium text-center">Leads</th>
                <th className="pb-3 font-medium text-center">Mensagens</th>
                <th className="pb-3 font-medium text-center">Taxa Resposta</th>
                <th className="pb-3 font-medium text-center">Conversões</th>
                <th className="pb-3 font-medium text-center">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.campaigns.map((campaign) => {
                const isBest = campaign.campaign_id === data.best_performer_id
                const isWorst = campaign.campaign_id === data.worst_performer_id && data.campaigns.length > 1
                
                return (
                  <tr key={campaign.campaign_id} className={`${isBest ? 'bg-green-50' : isWorst ? 'bg-red-50' : ''}`}>
                    <td className="py-4">
                      <div className="flex items-center gap-2">
                        {isBest && <Trophy className="h-4 w-4 text-amber-500" />}
                        {isWorst && <AlertTriangle className="h-4 w-4 text-red-500" />}
                        <div>
                          <p className="font-medium">{campaign.campaign_name}</p>
                          <Badge className={`text-xs mt-1 ${STATUS_COLORS[campaign.status] || STATUS_COLORS.draft}`}>
                            {campaign.status}
                          </Badge>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-2">
                      <div className="space-y-1">
                        <p className="text-center font-mono">{campaign.total_leads.toLocaleString()}</p>
                        <MetricBar value={campaign.total_leads} maxValue={maxLeads} color="bg-blue-500" />
                      </div>
                    </td>
                    <td className="py-4 px-2">
                      <div className="space-y-1">
                        <p className="text-center font-mono">{campaign.messages_sent.toLocaleString()}</p>
                        <MetricBar value={campaign.messages_sent} maxValue={maxMessages} color="bg-purple-500" />
                      </div>
                    </td>
                    <td className="py-4 px-2">
                      <div className="flex items-center justify-center gap-1">
                        <span className={`font-mono ${campaign.reply_rate > data.avg_reply_rate ? 'text-green-600' : 'text-red-600'}`}>
                          {campaign.reply_rate.toFixed(1)}%
                        </span>
                        {campaign.reply_rate > data.avg_reply_rate ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-600" />
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-2">
                      <div className="space-y-1">
                        <p className="text-center font-mono text-green-600">{campaign.conversions}</p>
                        <MetricBar value={campaign.conversions} maxValue={maxConversions} color="bg-green-500" />
                        <p className="text-center text-xs text-muted-foreground">{campaign.conversion_rate.toFixed(1)}%</p>
                      </div>
                    </td>
                    <td className="py-4 text-center">
                      <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full font-bold ${
                        campaign.performance_score >= 70 ? 'bg-green-100 text-green-700' :
                        campaign.performance_score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {campaign.performance_score.toFixed(0)}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
