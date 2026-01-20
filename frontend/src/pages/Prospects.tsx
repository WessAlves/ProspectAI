import { useEffect, useState } from 'react'
import { Plus, Users, Upload, Search, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'

interface Prospect {
  id: string
  name: string
  email: string | null
  phone: string | null
  company: string | null
  position: string | null
  linkedin_url: string | null
  status: 'new' | 'contacted' | 'responded' | 'qualified' | 'converted' | 'lost'
  source: string | null
  created_at: string
}

const statusConfig = {
  new: { label: 'Novo', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  contacted: { label: 'Contatado', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
  responded: { label: 'Respondeu', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  qualified: { label: 'Qualificado', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' },
  converted: { label: 'Convertido', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300' },
  lost: { label: 'Perdido', color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' },
}

export default function Prospects() {
  const [prospects, setProspects] = useState<Prospect[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProspects, setSelectedProspects] = useState<string[]>([])
  const { toast } = useToast()

  const fetchProspects = async () => {
    try {
      const response = await api.get('/prospects', {
        params: { search: searchTerm || undefined },
      })
      setProspects(response.data)
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

  useEffect(() => {
    fetchProspects()
  }, [searchTerm])

  const deleteProspect = async (prospectId: string) => {
    if (!confirm('Tem certeza que deseja excluir este lead?')) return
    
    try {
      await api.delete(`/prospects/${prospectId}`)
      setProspects(prospects.filter(p => p.id !== prospectId))
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

  const toggleSelectProspect = (prospectId: string) => {
    setSelectedProspects(prev => 
      prev.includes(prospectId) 
        ? prev.filter(id => id !== prospectId)
        : [...prev, prospectId]
    )
  }

  const toggleSelectAll = () => {
    if (selectedProspects.length === prospects.length) {
      setSelectedProspects([])
    } else {
      setSelectedProspects(prospects.map(p => p.id))
    }
  }

  const deleteSelected = async () => {
    if (!confirm(`Tem certeza que deseja excluir ${selectedProspects.length} leads?`)) return
    
    try {
      await Promise.all(selectedProspects.map(id => api.delete(`/prospects/${id}`)))
      setProspects(prospects.filter(p => !selectedProspects.includes(p.id)))
      setSelectedProspects([])
      toast({
        title: 'Leads excluídos',
        description: `${selectedProspects.length} leads foram excluídos.`,
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
          <Button variant="outline">
            <Upload className="mr-2 h-4 w-4" />
            Importar CSV
          </Button>
          <Button>
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
                {prospects.length} leads cadastrados
              </CardDescription>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar Leads..."
                  className="pl-10 w-64"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              {selectedProspects.length > 0 && (
                <Button variant="destructive" size="sm" onClick={deleteSelected}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Excluir ({selectedProspects.length})
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {prospects.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Nenhum lead cadastrado</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Adicione leads manualmente ou importe de um arquivo CSV
              </p>
              <div className="flex gap-2 justify-center">
                <Button variant="outline">
                  <Upload className="mr-2 h-4 w-4" />
                  Importar CSV
                </Button>
                <Button>
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
                        checked={selectedProspects.length === prospects.length}
                        onChange={toggleSelectAll}
                        className="rounded border-gray-300"
                      />
                    </th>
                    <th className="text-left py-3 px-4 font-medium">Nome</th>
                    <th className="text-left py-3 px-4 font-medium">Empresa</th>
                    <th className="text-left py-3 px-4 font-medium">Cargo</th>
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                    <th className="text-left py-3 px-4 font-medium">Fonte</th>
                    <th className="text-left py-3 px-4 font-medium">Data</th>
                    <th className="text-left py-3 px-4 font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {prospects.map((prospect) => (
                    <tr key={prospect.id} className="border-b hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <input
                          type="checkbox"
                          checked={selectedProspects.includes(prospect.id)}
                          onChange={() => toggleSelectProspect(prospect.id)}
                          className="rounded border-gray-300"
                        />
                      </td>
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium">{prospect.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {prospect.email || prospect.phone || '-'}
                          </p>
                        </div>
                      </td>
                      <td className="py-3 px-4">{prospect.company || '-'}</td>
                      <td className="py-3 px-4">{prospect.position || '-'}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig[prospect.status].color}`}>
                          {statusConfig[prospect.status].label}
                        </span>
                      </td>
                      <td className="py-3 px-4">{prospect.source || '-'}</td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {new Date(prospect.created_at).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="py-3 px-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteProspect(prospect.id)}
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
    </div>
  )
}
