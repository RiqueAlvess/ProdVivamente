'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/header';
import { DimensionScores } from '@/components/dashboard/dimension-scores';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import api from '@/lib/api';
import type { DashboardMetrics } from '@/types';

export default function SectorAnalyticsPage() {
  const { id } = useParams<{ id: string }>();

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['sector-analytics', id],
    queryFn: async () => {
      const { data } = await api.get<DashboardMetrics>('/analytics/dashboard/', {
        params: { sector_id: id },
      });
      return data;
    },
    enabled: !!id,
  });

  return (
    <div>
      <Header title="Analytics do Setor" />
      <div className="p-6 space-y-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : !metrics ? (
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            <p>Dados não disponíveis para este setor.</p>
          </div>
        ) : (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Resumo do Setor</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold">{metrics.total_invited}</p>
                    <p className="text-sm text-muted-foreground">Convidados</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{metrics.total_responded}</p>
                    <p className="text-sm text-muted-foreground">Respondidos</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{metrics.igrp_score.toFixed(2)}</p>
                    <p className="text-sm text-muted-foreground">IGRP</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            {metrics.dimension_scores?.length > 0 && (
              <DimensionScores scores={metrics.dimension_scores} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
