import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { Campaign, PaginatedResponse } from '@/types';

export function useCampaigns() {
  return useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Campaign>>('/campaigns/campaigns/');
      return data;
    },
  });
}

export function useCampaign(id: string | number) {
  return useQuery({
    queryKey: ['campaigns', id],
    queryFn: async () => {
      const { data } = await api.get<Campaign>(`/campaigns/campaigns/${id}/`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Campaign>) => {
      const { data } = await api.post<Campaign>('/campaigns/campaigns/', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}

export function useUpdateCampaign(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Campaign>) => {
      const { data } = await api.patch<Campaign>(`/campaigns/campaigns/${id}/`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['campaigns', id] });
    },
  });
}
