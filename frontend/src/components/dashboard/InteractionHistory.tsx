import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  MessageSquare, 
  User, 
  Calendar,
  Search,
  ChevronLeft,
  ChevronRight,
  ExternalLink
} from 'lucide-react'

interface InteractionItem {
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
}

interface InteractionHistoryData {
  items: InteractionItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

interface InteractionHistoryProps {
  data: InteractionHistoryData
  isLoading?: boolean
  onPageChange?: (page: number) => void
  onSearch?: (query: string) => void
  onViewLead?: (leadId: string) => void
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending: { label: 'Pendente', color: 'bg-gray-100 text-gray-800' },
  contacted: { label: 'Contatado', color: 'bg-blue-100 text-blue-800' },
  replied: { label: 'Respondeu', color: 'bg-purple-100 text-purple-800' },
  converted: { label: 'Convertido', color: 'bg-green-100 text-green-800' },
  rejected: { label: 'Rejeitado', color: 'bg-red-100 text-red-800' },
}

const SOURCE_ICONS: Record<string, string> = {
  instagram: '📸',
  google_maps: '📍',
  google: '🔍',
  whatsapp: '💬',
  unknown: '❓',
}

export function InteractionHistory({ 
  data, 
  isLoading, 
  onPageChange, 
  onSearch,
  onViewLead 
}: InteractionHistoryProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = () => {
    onSearch?.(searchQuery)
  }

  if (isLoading) {
    return (
      <Card className="col-span-full">
        <CardHeader>
          <CardTitle>Histórico de Interações</CardTitle>
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

  return (
    <Card className="col-span-full">
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <CardTitle>Histórico de Interações</CardTitle>
            <CardDescription>CRM básico - {data.total} interações registradas</CardDescription>
          </div>
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar prospect..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-9 w-64"
              />
            </div>
            <Button variant="outline" size="icon" onClick={handleSearch}>
              <Search className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {data.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
            <MessageSquare className="h-8 w-8 mb-2" />
            <p>Nenhuma interação encontrada</p>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {data.items.map((item) => {
                const statusConfig = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending
                const sourceIcon = SOURCE_ICONS[item.lead_source] || SOURCE_ICONS.unknown
                
                return (
                  <div 
                    key={item.id} 
                    className="flex items-start gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    {/* Avatar / Source */}
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-lg">
                      {sourceIcon}
                    </div>
                    
                    {/* Main content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium truncate">{item.lead_name}</span>
                        <Badge className={`text-xs ${statusConfig.color}`}>
                          {statusConfig.label}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {item.campaign_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          {item.total_messages} msgs • {item.reply_count} respostas
                        </span>
                      </div>
                      
                      {item.last_message && (
                        <p className="mt-2 text-sm text-muted-foreground line-clamp-2 italic">
                          "{item.last_message}"
                        </p>
                      )}
                      
                      {item.last_message_at && (
                        <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(item.last_message_at).toLocaleString('pt-BR')}
                        </p>
                      )}
                    </div>
                    
                    {/* Actions */}
                    <div className="flex-shrink-0">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => onViewLead?.(item.lead_id)}
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
            
            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  Página {data.page} de {data.total_pages}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={data.page <= 1}
                    onClick={() => onPageChange?.(data.page - 1)}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={data.page >= data.total_pages}
                    onClick={() => onPageChange?.(data.page + 1)}
                  >
                    Próxima
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
