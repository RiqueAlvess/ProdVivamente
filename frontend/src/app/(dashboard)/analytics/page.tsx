'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MetricCard } from '@/components/dashboard/metric-card';
import { DimensionScores } from '@/components/dashboard/dimension-scores';
import { RiskDistributionChart } from '@/components/dashboard/risk-distribution';
import { Heatmap } from '@/components/dashboard/heatmap';
import { IGRPGauge } from '@/components/dashboard/igrp-gauge';
import { useCampaigns } from '@/hooks/use-campaigns';
import { useDashboard } from '@/hooks/use-dashboard';
import { formatPercent } from '@/lib/utils';
import { Users, CheckSquare, TrendingUp } from 'lucide-react';

export default function AnalyticsPage() {
  const searchParams = useSearchParams();
  const defaultCampaign = searchParams.get('campaign');
  const [selectedCampaign, setSelectedCampaign] = useState<string | null>(defaultCampaign);

  const { data: campaignsData } = useCampaigns();
  const { data: metrics, isLoading } = useDashboard(selectedCampaign);

  return (
    <div>
      <Header title="Analytics" />
      <div className="p-6 space-y-6">
        <div className="min-w-[200px] max-w-xs">
          <Select defaultValue={defaultCampaign ?? undefined} onValueChange={setSelectedCampaign}>
            <SelectTrigger>
              <SelectValue placeholder="Selecionar campanha" />
            </SelectTrigger>
            <SelectContent>
              {campaignsData?.results?.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {!selectedCampaign ? (
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            <p>Selecione uma campanha para visualizar os analytics</p>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : !metrics ? (
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            <p>Dados não disponíveis.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <MetricCard title="Total Convidados" value={metrics.total_invited} icon={Users} />
              <MetricCard title="Respondidos" value={metrics.total_responded} icon={CheckSquare} />
              <MetricCard title="Taxa de Adesão" value={formatPercent(metrics.response_rate)} icon={TrendingUp} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <IGRPGauge score={metrics.igrp_score} level={metrics.igrp_level} />
              {metrics.dimension_scores?.length > 0 && <DimensionScores scores={metrics.dimension_scores} />}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskDistributionChart distribution={metrics.risk_distribution} />
            </div>
            {metrics.heatmap?.length > 0 && <Heatmap cells={metrics.heatmap} />}
          </>
        )}
      </div>
    </div>
  );
}
