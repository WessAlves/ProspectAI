import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Lock, Crown, ArrowRight } from 'lucide-react'

interface UpgradePromptProps {
  feature: string
  description: string
  requiredPlan: 'starter' | 'pro' | 'scale'
  currentPlan: string
  onUpgrade?: () => void
}

const PLAN_INFO: Record<string, { name: string; price: string; color: string }> = {
  starter: { name: 'Starter', price: 'R$ 199,90', color: 'bg-blue-500' },
  pro: { name: 'Pro', price: 'R$ 399,90', color: 'bg-purple-500' },
  scale: { name: 'Scale', price: 'R$ 799,90', color: 'bg-gradient-to-r from-amber-400 to-orange-500' },
}

export function UpgradePrompt({ 
  feature, 
  description, 
  requiredPlan, 
  currentPlan,
  onUpgrade 
}: UpgradePromptProps) {
  const planInfo = PLAN_INFO[requiredPlan]
  
  return (
    <Card className="border-dashed border-2 bg-muted/30">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Lock className="h-8 w-8 text-muted-foreground" />
        </div>
        
        <h3 className="text-xl font-semibold mb-2">{feature}</h3>
        <p className="text-muted-foreground mb-6 max-w-md">{description}</p>
        
        <div className="flex items-center gap-2 mb-6">
          <Badge variant="outline" className="text-muted-foreground">
            Seu plano: {currentPlan}
          </Badge>
          <ArrowRight className="h-4 w-4 text-muted-foreground" />
          <Badge className={`${planInfo.color} text-white`}>
            <Crown className="h-3 w-3 mr-1" />
            Requer: {planInfo.name}
          </Badge>
        </div>
        
        <p className="text-sm text-muted-foreground mb-4">
          A partir de <span className="font-semibold">{planInfo.price}/mês</span>
        </p>
        
        <Button onClick={onUpgrade} className="gap-2">
          <Crown className="h-4 w-4" />
          Fazer Upgrade para {planInfo.name}
        </Button>
      </CardContent>
    </Card>
  )
}
