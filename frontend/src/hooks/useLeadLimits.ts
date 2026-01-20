import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';

interface LeadUsageSummary {
  plan_name: string;
  plan_monthly_limit: number;
  leads_used_this_month: number;
  leads_from_plan: number;
  leads_from_packages: number;
  total_available: number;
  total_remaining: number;
  usage_percentage: number;
  is_limit_reached: boolean;
  campaigns_paused: boolean;
  active_packages: any[];
}

interface UseLeadLimitsReturn {
  usage: LeadUsageSummary | null;
  loading: boolean;
  error: string | null;
  isLimitReached: boolean;
  remainingLeads: number;
  usagePercentage: number;
  refresh: () => Promise<void>;
}

export function useLeadLimits(): UseLeadLimitsReturn {
  const [usage, setUsage] = useState<LeadUsageSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsage = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/lead-packages/usage');
      setUsage(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar uso de leads');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsage();
  }, [fetchUsage]);

  return {
    usage,
    loading,
    error,
    isLimitReached: usage?.is_limit_reached ?? false,
    remainingLeads: usage?.total_remaining ?? 0,
    usagePercentage: usage?.usage_percentage ?? 0,
    refresh: fetchUsage,
  };
}

// Hook para verificação rápida de limite
export function useCanAddLeads() {
  const [canAdd, setCanAdd] = useState<boolean>(true);
  const [remaining, setRemaining] = useState<number>(-1);
  const [loading, setLoading] = useState(true);

  const check = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/lead-packages/check-limit');
      setCanAdd(response.data.can_add_leads);
      setRemaining(response.data.remaining);
    } catch {
      // Em caso de erro, assume que pode adicionar
      setCanAdd(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    check();
  }, [check]);

  return { canAdd, remaining, loading, refresh: check };
}
