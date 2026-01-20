import { useEffect, useState } from 'react';
import { useCampaignScraping } from '../../hooks/useScrapingWebSocket';
import { Loader2, CheckCircle, XCircle, AlertTriangle, Wifi, WifiOff } from 'lucide-react';

interface ScrapingProgressProps {
  campaignId: string;
  onComplete?: (totalSaved: number) => void;
}

export function ScrapingProgress({ campaignId, onComplete }: ScrapingProgressProps) {
  const {
    isConnected,
    progress,
    leads,
    completed,
    error,
  } = useCampaignScraping(campaignId);

  const [showLeads, setShowLeads] = useState(false);

  useEffect(() => {
    if (completed && onComplete) {
      onComplete(completed.total_saved);
    }
  }, [completed, onComplete]);

  // Se não há progresso e não está conectado, não mostrar nada
  if (!progress && !completed && !error && !isConnected) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-4">
      {/* Header com status de conexão */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-800">Progresso do Scraping</h3>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <span className="flex items-center gap-1 text-green-600 text-sm">
              <Wifi className="w-4 h-4" />
              Conectado
            </span>
          ) : (
            <span className="flex items-center gap-1 text-gray-400 text-sm">
              <WifiOff className="w-4 h-4" />
              Desconectado
            </span>
          )}
        </div>
      </div>

      {/* Status de erro */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg mb-3">
          <XCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Progresso atual */}
      {progress && !completed && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">
                  Encontrados: <strong>{progress.found}</strong>
                </span>
                <span className="text-gray-600">
                  Salvos: <strong>{progress.saved}</strong>
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min((progress.saved / Math.max(progress.found, 1)) * 100, 100)}%` }}
                />
              </div>
            </div>
          </div>
          
          {progress.current && (
            <p className="text-sm text-gray-500 truncate">
              Atual: <span className="font-medium">{progress.current}</span>
            </p>
          )}
        </div>
      )}

      {/* Conclusão */}
      {completed && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 p-3 bg-green-50 text-green-700 rounded-lg">
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
            <div>
              <p className="font-medium">Scraping concluído!</p>
              <p className="text-sm">
                {completed.total_saved} leads salvos de {completed.total_found} encontrados
                {' '}em {Math.round(completed.duration_seconds)}s
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Lista de leads encontrados */}
      {leads.length > 0 && (
        <div className="mt-4">
          <button 
            onClick={() => setShowLeads(!showLeads)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {showLeads ? 'Ocultar' : 'Mostrar'} leads encontrados ({leads.length})
          </button>
          
          {showLeads && (
            <div className="mt-2 max-h-60 overflow-y-auto border rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="text-left p-2 font-medium text-gray-600">Nome</th>
                    <th className="text-left p-2 font-medium text-gray-600">Telefone</th>
                    <th className="text-left p-2 font-medium text-gray-600">Website</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead, index) => (
                    <tr key={index} className="border-t hover:bg-gray-50">
                      <td className="p-2 font-medium">{lead.name}</td>
                      <td className="p-2 text-gray-600">{lead.phone || '-'}</td>
                      <td className="p-2">
                        {lead.website ? (
                          <a 
                            href={lead.website} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline truncate block max-w-[150px]"
                          >
                            {new URL(lead.website).hostname}
                          </a>
                        ) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Versão compacta para usar em cards de campanha
export function ScrapingProgressCompact({ campaignId }: { campaignId: string }) {
  const { progress, completed, error } = useCampaignScraping(campaignId);

  if (!progress && !completed && !error) {
    return null;
  }

  if (error) {
    return (
      <div className="flex items-center gap-1 text-red-500 text-xs">
        <AlertTriangle className="w-3 h-3" />
        <span>Erro no scraping</span>
      </div>
    );
  }

  if (completed) {
    return (
      <div className="flex items-center gap-1 text-green-600 text-xs">
        <CheckCircle className="w-3 h-3" />
        <span>{completed.total_saved} leads salvos</span>
      </div>
    );
  }

  if (progress) {
    return (
      <div className="flex items-center gap-1 text-blue-500 text-xs">
        <Loader2 className="w-3 h-3 animate-spin" />
        <span>Buscando... {progress.saved}/{progress.found}</span>
      </div>
    );
  }

  return null;
}
