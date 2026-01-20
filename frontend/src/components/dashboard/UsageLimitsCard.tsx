import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Users, 
  Bot, 
  Target, 
  Zap, 
  Crown,
  ArrowUpRight
} from 'lucide-react'

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

interface UsageLimitsCardProps {
  usage: UsageLimits
  onUpgrade?: () => void
}

const PLAN_COLORS: Record<string, string> = {
  free: 'bg-gray-100 text-gray-800',
  starter: 'bg-blue-100 text-blue-800',
  pro: 'bg-purple-100 text-purple-800',
  scale: 'bg-gradient-to-r from-amber-400 to-orange-500 text-white',
}

const PLAN_NAMES: Record<string, string> = {
  free: 'Free',
  starter: 'Starter',
  pro: 'Pro',
  scale: 'Scale',
}

function UsageBar({ 
  label, 
  used, 
  limit, 
  icon: Icon 
}: { 
  label: string
  used: number
  limit: number
  icon: React.ElementType
}) {
  const isUnlimited = limit === -1
  const percentage = isUnlimited ? 0 : Math.min((used / limit) * 100, 100)
  const isNearLimit = percentage >= 80
  const isAtLimit = percentage >= 100
  
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{label}</span>
        </div>
        <span className={`font-mono ${isAtLimit ? 'text-red-600' : isNearLimit ? 'text-amber-600' : 'text-muted-foreground'}`}>
          {used} / {isUnlimited ? '∞' : limit}
        </span>
      </div>
      {!isUnlimited && (
        <Progress 
          value={percentage} 
          className={`h-2 ${isAtLimit ? '[&>div]:bg-red-500' : isNearLimit ? '[&>div]:bg-amber-500' : ''}`}
        />
      )}
      {isUnlimited && (
        <div className="h-2 bg-gradient-to-r from-green-200 to-green-400 rounded-full" />
      )}
    </div>
  )
}

export function UsageLimitsCard({ usage, onUpgrade }: UsageLimitsCardProps) {
  const planColor = PLAN_COLORS[usage.plan_tier] || PLAN_COLORS.free
  const planName = PLAN_NAMES[usage.plan_tier] || 'Free'
  const isScale = usage.plan_tier === 'scale'
  
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Uso do Plano</CardTitle>
            <CardDescription>Limites e consumo atual</CardDescription>
          </div>
          <Badge className={`${planColor} px-3 py-1 text-sm font-semibold`}>
            {isScale && <Crown className="h-3 w-3 mr-1" />}
            {planName}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <UsageBar
          label="Leads / mês"
          used={usage.leads_used}
          limit={usage.leads_limit}
          icon={Users}
        />
        <UsageBar
          label="Agentes de IA"
          used={usage.agents_used}
          limit={usage.agents_limit}
          icon={Bot}
        />
        <UsageBar
          label="Campanhas"
          used={usage.campaigns_used}
          limit={usage.campaigns_limit}
          icon={Target}
        />
        
        {/* Features do plano */}
        <div className="pt-4 border-t">
          <p className="text-sm font-medium mb-3">Features Disponíveis</p>
          <div className="flex flex-wrap gap-2">
            {usage.whatsapp_enabled && (
              <Badge variant="outline" className="text-xs">
                <Zap className="h-3 w-3 mr-1" /> WhatsApp
              </Badge>
            )}
            {usage.whatsapp_official_api && (
              <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                API Oficial
              </Badge>
            )}
            {usage.advanced_filters && (
              <Badge variant="outline" className="text-xs">Filtros Avançados</Badge>
            )}
            {usage.funnel_reports && (
              <Badge variant="outline" className="text-xs">Funil</Badge>
            )}
            {usage.campaign_comparison && (
              <Badge variant="outline" className="text-xs">Comparativo</Badge>
            )}
            {usage.crm_integration && (
              <Badge variant="outline" className="text-xs">CRM</Badge>
            )}
            {usage.priority_support && (
              <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                Suporte Prioritário
              </Badge>
            )}
            {usage.sso && (
              <Badge variant="outline" className="text-xs">SSO</Badge>
            )}
          </div>
        </div>
        
        {/* Botão de upgrade */}
        {usage.plan_tier !== 'scale' && onUpgrade && (
          <Button 
            variant="outline" 
            className="w-full mt-4 group"
            onClick={onUpgrade}
          >
            Fazer Upgrade
            <ArrowUpRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
