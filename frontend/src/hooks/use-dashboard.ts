import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type { DashboardMetrics } from '@/types';

export function useDashboard(campaignId: string | number | null, sectorId?: string | number | null) {
  return useQuery({
    queryKey: ['dashboard', campaignId, sectorId],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (campaignId) params.campaign_id = String(campaignId);
      if (sectorId) params.sector_id = String(sectorId);
      const { data } = await api.get<DashboardMetrics>('/analytics/dashboard/', { params });
      return data;
    },
    enabled: !!campaignId,
  });
}
