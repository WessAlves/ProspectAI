import { useEffect, useState, useRef } from 'react'
import { Plus, Users, Upload, Search, Trash2, Download, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { useConfirmDialog } from '@/components/ui/confirm-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import api from '@/lib/api'

interface Lead {
  id: string
  name: string | null
  username: string
  email: string | null
  phone: string | null
  company: string | null
  position: string | null
  platform: string
  profile_url: string | null
  status: string
  score: number
  campaign_id: string | null
  created_at: string
}

interface Campaign {
  id: string
  name: string
}

const statusConfig: Record<string, { label: string; color: string }> = {
  found: { label: 'Novo', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  contacted: { label: 'Contatado', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
  replied: { label: 'Respondeu', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  converted: { label: 'Convertido', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300' },
  ignored: { label: 'Ignorado', color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' },
}

const platformLabels: Record<string, string> = {
  manual: 'Manual',
  import: 'Importado',
  instagram: 'Instagram',
  google: 'Google',
}

export default function Leads() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedLeads, setSelectedLeads] = useState<string[]>([])
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()
  const { confirm, ConfirmDialog } = useConfirmDialog({
    title: 'Excluir Lead',
    description: 'Tem certeza que deseja excluir este lead? Esta ação não pode ser desfeita.',
    confirmText: 'Excluir',
    cancelText: 'Cancelar',
    variant: 'destructive',
  })

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    position: '',
    campaign_id: '',
  })

  // Import state
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importCampaignId, setImportCampaignId] = useState('')

  const fetchLeads = async () => {
    try {
      const response = await api.get('/prospects', {
        params: { search: searchTerm || undefined },
      })
      setLeads(response.data)
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao carregar leads',
        description: 'Não foi possível carregar a lista de leads.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const fetchCampaigns = async () => {
    try {
      const response = await api.get('/campaigns')
      setCampaigns(response.data)
    } catch (error) {
      console.error('Erro ao carregar campanhas:', error)
    }
  }

  useEffect(() => {
    fetchLeads()
    fetchCampaigns()
  }, [searchTerm])

  const handleCreateLead = async () => {
    if (!formData.name && !formData.email) {
      toast({
        variant: 'destructive',
        title: 'Dados obrigatórios',
        description: 'Informe pelo menos o nome ou email do lead.',
      })
      return
    }

    setIsSubmitting(true)
    try {
      const response = await api.post('/prospects', {
        name: formData.name || null,
        email: formData.email || null,
        phone: formData.phone || null,
        company: formData.company || null,
        position: formData.position || null,
        campaign_id: formData.campaign_id || null,
        platform: 'manual',
      })
      
      setLeads([response.data, ...leads])
      setIsCreateModalOpen(false)
      setFormData({ name: '', email: '', phone: '', company: '', position: '', campaign_id: '' })
      
      toast({
        title: 'Lead criado',
        description: 'O lead foi adicionado com sucesso.',
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao criar lead',
        description: error.response?.data?.detail || 'Não foi possível criar o lead.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleImport = async () => {
    if (!importFile) {
      toast({
        variant: 'destructive',
        title: 'Selecione um arquivo',
        description: 'Por favor, selecione um arquivo CSV ou XLSX para importar.',
      })
      return
    }

    setIsSubmitting(true)
    try {
      // Parse do arquivo
      const text = await importFile.text()
      const lines = text.split('\n').filter(line => line.trim())
      
      if (lines.length < 2) {
        throw new Error('Arquivo vazio ou sem dados')
      }

      // Parse do header
      const headers = lines[0].split(/[,;]/).map(h => h.trim().toLowerCase().replace(/"/g, ''))
      
      // Mapear colunas
      const nameIdx = headers.findIndex(h => ['nome', 'name'].includes(h))
      const emailIdx = headers.findIndex(h => ['email', 'e-mail'].includes(h))
      const phoneIdx = headers.findIndex(h => ['telefone', 'phone', 'celular', 'tel'].includes(h))
      const companyIdx = headers.findIndex(h => ['empresa', 'company'].includes(h))
      const positionIdx = headers.findIndex(h => ['cargo', 'position', 'posição'].includes(h))

      const prospects = []
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(/[,;]/).map(v => v.trim().replace(/"/g, ''))
        
        if (values.length < 1 || !values.some(v => v)) continue
        
        prospects.push({
          name: nameIdx >= 0 ? values[nameIdx] || null : null,
          email: emailIdx >= 0 ? values[emailIdx] || null : null,
          phone: phoneIdx >= 0 ? values[phoneIdx] || null : null,
          company: companyIdx >= 0 ? values[companyIdx] || null : null,
          position: positionIdx >= 0 ? values[positionIdx] || null : null,
          campaign_id: importCampaignId || null,
          platform: 'import',
        })
      }

      if (prospects.length === 0) {
        throw new Error('Nenhum lead válido encontrado no arquivo')
      }

      const response = await api.post('/prospects/bulk', { prospects })
      
      setIsImportModalOpen(false)
      setImportFile(null)
      setImportCampaignId('')
      if (fileInputRef.current) fileInputRef.current.value = ''
      
      fetchLeads()
      
      toast({
        title: 'Importação concluída',
        description: `${response.data.created} leads importados com sucesso.${response.data.errors?.length > 0 ? ` ${response.data.errors.length} erros.` : ''}`,
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro na importação',
        description: error.message || 'Não foi possível importar os leads.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const downloadTemplate = () => {
    const template = 'Nome,Email,Telefone,Empresa,Cargo\nJoão Silva,joao@email.com,(11) 99999-9999,Empresa ABC,Gerente\nMaria Santos,maria@email.com,(21) 88888-8888,Empresa XYZ,Diretora'
    const blob = new Blob([template], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'template_leads.csv'
    link.click()
  }

  const deleteLead = async (leadId: string) => {
    const confirmed = await confirm({
      title: 'Excluir Lead',
      description: 'Tem certeza que deseja excluir este lead? Esta ação não pode ser desfeita.',
    })
    if (!confirmed) return
    
    try {
      await api.delete(`/prospects/${leadId}`)
      setLeads(leads.filter(l => l.id !== leadId))
      toast({
        title: 'Lead excluído',
        description: 'O lead foi excluído com sucesso.',
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao excluir lead',
        description: 'Não foi possível excluir o lead.',
      })
    }
  }

  const toggleSelectLead = (leadId: string) => {
    setSelectedLeads(prev => 
      prev.includes(leadId) 
        ? prev.filter(id => id !== leadId)
        : [...prev, leadId]
    )
  }

  const toggleSelectAll = () => {
    if (selectedLeads.length === leads.length) {
      setSelectedLeads([])
    } else {
      setSelectedLeads(leads.map(l => l.id))
    }
  }

  const deleteSelected = async () => {
    const confirmed = await confirm({
      title: 'Excluir Leads Selecionados',
      description: `Tem certeza que deseja excluir ${selectedLeads.length} leads? Esta ação não pode ser desfeita.`,
    })
    if (!confirmed) return
    
    try {
      await Promise.all(selectedLeads.map(id => api.delete(`/prospects/${id}`)))
      setLeads(leads.filter(l => !selectedLeads.includes(l.id)))
      setSelectedLeads([])
      toast({
        title: 'Leads excluídos',
        description: `${selectedLeads.length} leads foram excluídos.`,
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Erro ao excluir leads',
        description: 'Não foi possível excluir alguns leads.',
      })
    }
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Leads</h1>
          <p className="text-muted-foreground">
            Gerencie sua base de Leads
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsImportModalOpen(true)}>
            <Upload className="mr-2 h-4 w-4" />
            Importar
          </Button>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Novo Lead
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Lista de Leads</CardTitle>
              <CardDescription>
                {leads.length} leads cadastrados
              </CardDescription>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar leads..."
                  className="pl-10 w-64"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              {selectedLeads.length > 0 && (
                <Button variant="destructive" size="sm" onClick={deleteSelected}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Excluir ({selectedLeads.length})
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {leads.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Nenhum lead cadastrado</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Adicione leads manualmente ou importe de um arquivo CSV/XLSX
              </p>
              <div className="flex gap-2 justify-center">
                <Button variant="outline" onClick={() => setIsImportModalOpen(true)}>
                  <Upload className="mr-2 h-4 w-4" />
                  Importar
                </Button>
                <Button onClick={() => setIsCreateModalOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Adicionar Lead
                </Button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">
                      <input
                        type="checkbox"
                        checked={selectedLeads.length === leads.length && leads.length > 0}
                        onChange={toggleSelectAll}
                        className="rounded border-gray-300"
                      />
                    </th>
                    <th className="text-left py-3 px-4 font-medium">Nome</th>
                    <th className="text-left py-3 px-4 font-medium">Contato</th>
                    <th className="text-left py-3 px-4 font-medium">Empresa</th>
                    <th className="text-left py-3 px-4 font-medium">Origem</th>
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                    <th className="text-left py-3 px-4 font-medium">Data</th>
                    <th className="text-left py-3 px-4 font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => (
                    <tr key={lead.id} className="border-b hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <input
                          type="checkbox"
                          checked={selectedLeads.includes(lead.id)}
                          onChange={() => toggleSelectLead(lead.id)}
                          className="rounded border-gray-300"
                        />
                      </td>
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium">{lead.name || lead.username}</p>
                          {lead.position && (
                            <p className="text-sm text-muted-foreground">{lead.position}</p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          {lead.email && <p>{lead.email}</p>}
                          {lead.phone && <p className="text-muted-foreground">{lead.phone}</p>}
                          {!lead.email && !lead.phone && '-'}
                        </div>
                      </td>
                      <td className="py-3 px-4">{lead.company || '-'}</td>
                      <td className="py-3 px-4">
                        <span className="text-sm">
                          {platformLabels[lead.platform] || lead.platform}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig[lead.status]?.color || 'bg-gray-100'}`}>
                          {statusConfig[lead.status]?.label || lead.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {new Date(lead.created_at).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="py-3 px-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteLead(lead.id)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de Criar Lead */}
      <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Novo Lead</DialogTitle>
            <DialogDescription>
              Adicione um novo lead manualmente. Preencha pelo menos o nome ou email.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Nome</Label>
              <Input
                id="name"
                placeholder="Nome completo"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="email@exemplo.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="phone">Telefone</Label>
                <Input
                  id="phone"
                  placeholder="(11) 99999-9999"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="company">Empresa</Label>
                <Input
                  id="company"
                  placeholder="Nome da empresa"
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="position">Cargo</Label>
                <Input
                  id="position"
                  placeholder="Cargo/Função"
                  value={formData.position}
                  onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="campaign">Vincular a Campanha (opcional)</Label>
              <Select
                value={formData.campaign_id || "none"}
                onValueChange={(value) => setFormData({ ...formData, campaign_id: value === "none" ? "" : value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma campanha" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Nenhuma campanha</SelectItem>
                  {campaigns.map((campaign) => (
                    <SelectItem key={campaign.id} value={campaign.id}>
                      {campaign.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleCreateLead} disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Criar Lead
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Importar */}
      <Dialog open={isImportModalOpen} onOpenChange={setIsImportModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Importar Leads</DialogTitle>
            <DialogDescription>
              Importe leads em massa a partir de um arquivo CSV ou XLSX.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={downloadTemplate}>
                <Download className="mr-2 h-4 w-4" />
                Baixar Template
              </Button>
              <span className="text-sm text-muted-foreground">
                Use o template para formatar seus dados
              </span>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="file">Arquivo CSV/XLSX</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="file"
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  ref={fileInputRef}
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="flex-1"
                />
                {importFile && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setImportFile(null)
                      if (fileInputRef.current) fileInputRef.current.value = ''
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              {importFile && (
                <p className="text-sm text-muted-foreground">
                  Arquivo selecionado: {importFile.name}
                </p>
              )}
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="import-campaign">Vincular a Campanha (opcional)</Label>
              <Select
                value={importCampaignId || "none"}
                onValueChange={(value) => setImportCampaignId(value === "none" ? "" : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma campanha" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Nenhuma campanha</SelectItem>
                  {campaigns.map((campaign) => (
                    <SelectItem key={campaign.id} value={campaign.id}>
                      {campaign.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="bg-muted p-3 rounded-lg text-sm">
              <p className="font-medium mb-1">Colunas suportadas:</p>
              <p className="text-muted-foreground">
                Nome, Email, Telefone, Empresa, Cargo
              </p>
              <p className="text-muted-foreground mt-1">
                O arquivo deve conter um cabeçalho na primeira linha.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsImportModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleImport} disabled={isSubmitting || !importFile}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Importar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog de Confirmação */}
      <ConfirmDialog />
    </div>
  )
}
