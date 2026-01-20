import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '../stores/authStore';

interface ScrapingProgress {
  type: 'scraping_progress';
  campaign_id: string;
  found: number;
  saved: number;
  current?: string;
}

interface LeadFound {
  type: 'lead_found';
  campaign_id: string;
  lead: {
    name: string;
    phone?: string;
    website?: string;
    email?: string;
    category?: string;
    rating?: number;
  };
}

interface ScrapingCompleted {
  type: 'scraping_completed';
  campaign_id: string;
  total_found: number;
  total_saved: number;
  duration_seconds: number;
}

interface ScrapingError {
  type: 'scraping_error';
  campaign_id: string;
  error: string;
}

interface LimitReached {
  type: 'limit_reached';
  campaign_id?: string;
  message: string;
}

interface Connected {
  type: 'connected';
  campaign_id?: string;
  message: string;
}

type WebSocketMessage = 
  | ScrapingProgress 
  | LeadFound 
  | ScrapingCompleted 
  | ScrapingError 
  | LimitReached 
  | Connected
  | { type: 'ping' }
  | { type: 'pong' };

interface UseScrapingWebSocketOptions {
  campaignId?: string;
  onProgress?: (data: ScrapingProgress) => void;
  onLeadFound?: (data: LeadFound) => void;
  onCompleted?: (data: ScrapingCompleted) => void;
  onError?: (data: ScrapingError) => void;
  onLimitReached?: (data: LimitReached) => void;
  enabled?: boolean;
}

interface UseScrapingWebSocketReturn {
  isConnected: boolean;
  progress: ScrapingProgress | null;
  leads: LeadFound['lead'][];
  completed: ScrapingCompleted | null;
  error: string | null;
  reconnect: () => void;
}

export function useScrapingWebSocket(options: UseScrapingWebSocketOptions): UseScrapingWebSocketReturn {
  const {
    campaignId,
    onProgress,
    onLeadFound,
    onCompleted,
    onError,
    onLimitReached,
    enabled = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [isConnected, setIsConnected] = useState(false);
  const [progress, setProgress] = useState<ScrapingProgress | null>(null);
  const [leads, setLeads] = useState<LeadFound['lead'][]>([]);
  const [completed, setCompleted] = useState<ScrapingCompleted | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { accessToken } = useAuthStore();

  const connect = useCallback(() => {
    if (!enabled || !accessToken) {
      return;
    }

    // Fechar conexão existente
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Construir URL do WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const path = campaignId 
      ? `/api/v1/ws/scraping/${campaignId}`
      : '/api/v1/ws/user';
    const url = `${protocol}//${host}${path}?token=${accessToken}`;

    console.log('[WebSocket] Conectando:', path);

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WebSocket] Conectado');
      setIsConnected(true);
      setError(null);

      // Iniciar ping interval para manter conexão viva
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 25000);
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        
        // Ignorar ping/pong
        if (data.type === 'ping' || data.type === 'pong') {
          if (data.type === 'ping' && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'pong' }));
          }
          return;
        }

        console.log('[WebSocket] Mensagem:', data.type, data);

        switch (data.type) {
          case 'connected':
            console.log('[WebSocket] Confirmação de conexão:', data.message);
            break;

          case 'scraping_progress':
            setProgress(data);
            onProgress?.(data);
            break;

          case 'lead_found':
            setLeads(prev => [...prev, data.lead]);
            onLeadFound?.(data);
            break;

          case 'scraping_completed':
            setCompleted(data);
            onCompleted?.(data);
            break;

          case 'scraping_error':
            setError(data.error);
            onError?.(data);
            break;

          case 'limit_reached':
            setError(data.message);
            onLimitReached?.(data);
            break;
        }
      } catch (e) {
        console.error('[WebSocket] Erro ao processar mensagem:', e);
      }
    };

    ws.onerror = (event) => {
      console.error('[WebSocket] Erro:', event);
      setError('Erro de conexão WebSocket');
    };

    ws.onclose = (event) => {
      console.log('[WebSocket] Desconectado:', event.code, event.reason);
      setIsConnected(false);

      // Limpar ping interval
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      // Tentar reconectar após 3 segundos (exceto se foi fechamento intencional)
      if (event.code !== 1000 && enabled) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('[WebSocket] Tentando reconectar...');
          connect();
        }, 3000);
      }
    };
  }, [enabled, accessToken, campaignId, onProgress, onLeadFound, onCompleted, onError, onLimitReached]);

  const reconnect = useCallback(() => {
    // Limpar leads e progresso ao reconectar
    setLeads([]);
    setProgress(null);
    setCompleted(null);
    setError(null);
    connect();
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      // Cleanup ao desmontar
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
      }
    };
  }, [connect]);

  // Resetar estado quando campaign muda
  useEffect(() => {
    setLeads([]);
    setProgress(null);
    setCompleted(null);
    setError(null);
  }, [campaignId]);

  return {
    isConnected,
    progress,
    leads,
    completed,
    error,
    reconnect,
  };
}

// Hook simplificado para monitorar uma campanha específica
export function useCampaignScraping(campaignId: string | undefined) {
  return useScrapingWebSocket({
    campaignId,
    enabled: !!campaignId,
  });
}

// Hook para monitorar todas as atividades do usuário
export function useUserNotifications() {
  return useScrapingWebSocket({
    enabled: true,
  });
}
