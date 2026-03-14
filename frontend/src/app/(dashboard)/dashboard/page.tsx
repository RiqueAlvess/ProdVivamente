'use client';

import { useState } from 'react';
import { Users, CheckSquare, TrendingUp, AlertTriangle } from 'lucide-react';
import { Header } from '@/components/layout/header';
import { MetricCard } from '@/components/dashboard/metric-card';
import { DimensionScores } from '@/components/dashboard/dimension-scores';
import { RiskDistributionChart } from '@/components/dashboard/risk-distribution';
import { Heatmap } from '@/components/dashboard/heatmap';
import { IGRPGauge } from '@/components/dashboard/igrp-gauge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCampaigns } from '@/hooks/use-campaigns';
import { useDashboard } from '@/hooks/use-dashboard';
import { useAuthStore } from '@/store/auth-store';
import { formatPercent, getRiskLevelLabel, getRiskColor } from '@/lib/utils';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [selectedCampaign, setSelectedCampaign] = useState<string | null>(null);
  const [selectedSector, setSelectedSector] = useState<string | null>(null);

  const { data: campaignsData, isLoading: loadingCampaigns } = useCampaigns();
  const { data: metrics, isLoading: loadingMetrics } = useDashboard(selectedCampaign, selectedSector);

  const isLeadership = user?.role === 'leadership';

  return (
    <div>
      <Header title="Dashboard" />
      <div className="p-6 space-y-6">
        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          <div className="min-w-[200px]">
            <Select onValueChange={setSelectedCampaign}>
              <SelectTrigger>
                <SelectValue placeholder={loadingCampaigns ? 'Carregando...' : 'Selecionar campanha'} />
              </SelectTrigger>
              <SelectContent>
                {campaignsData?.results?.map((campaign) => (
                  <SelectItem key={campaign.id} value={String(campaign.id)}>
                    {campaign.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {isLeadership && user?.sector && (
            <div className="min-w-[200px]">
              <Select onValueChange={setSelectedSector}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecionar setor" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={String(user.sector)}>Meu setor</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {!selectedCampaign ? (
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            <div className="text-center">
              <TrendingUp className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>Selecione uma campanha para visualizar os dados</p>
            </div>
          </div>
        ) : loadingMetrics ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : !metrics ? (
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            <p>Sem dados disponíveis para esta campanha.</p>
          </div>
        ) : (
          <>
            {/* Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <MetricCard
                title="Total Convidados"
                value={metrics.total_invited}
                icon={Users}
              />
              <MetricCard
                title="Respondidos"
                value={metrics.total_responded}
                icon={CheckSquare}
              />
              <MetricCard
                title="Taxa de Adesão"
                value={formatPercent(metrics.response_rate)}
                icon={TrendingUp}
                subtitle={`${metrics.total_responded} de ${metrics.total_invited}`}
              />
            </div>

            {/* IGRP + Dimensions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <IGRPGauge score={metrics.igrp_score} level={metrics.igrp_level} />
              {metrics.dimension_scores?.length > 0 && (
                <DimensionScores scores={metrics.dimension_scores} />
              )}
            </div>

            {/* Risk Distribution + Top Sectors */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskDistributionChart distribution={metrics.risk_distribution} />

              {/* Top Critical Sectors */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                    Top 5 Setores Críticos
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {metrics.top_critical_sectors?.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Nenhum setor em situação crítica.</p>
                  ) : (
                    <div className="space-y-3">
                      {metrics.top_critical_sectors?.slice(0, 5).map((sector) => (
                        <div key={sector.sector_id} className="flex items-center justify-between gap-2">
                          <span className="text-sm font-medium truncate">{sector.sector_name}</span>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-sm text-muted-foreground">
                              {sector.igrp_score.toFixed(2)}
                            </span>
                            <Badge
                              className={`text-xs ${getRiskColor(sector.risk_level)}`}
                              variant="outline"
                            >
                              {getRiskLevelLabel(sector.risk_level)}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Heatmap */}
            {metrics.heatmap?.length > 0 && (
              <Heatmap cells={metrics.heatmap} />
            )}

            {/* Demographic Scores */}
            {metrics.demographic_scores && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Pontuações Demográficas</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                    <div>
                      <h4 className="font-medium mb-2">Por Gênero</h4>
                      {Object.entries(metrics.demographic_scores.by_gender).map(([k, v]) => (
                        <div key={k} className="flex justify-between py-1 border-b last:border-0">
                          <span className="text-muted-foreground">{k}</span>
                          <span className="font-medium">{(v as number).toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Por Faixa Etária</h4>
                      {Object.entries(metrics.demographic_scores.by_age_range).map(([k, v]) => (
                        <div key={k} className="flex justify-between py-1 border-b last:border-0">
                          <span className="text-muted-foreground">{k}</span>
                          <span className="font-medium">{(v as number).toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Por Tempo na Empresa</h4>
                      {Object.entries(metrics.demographic_scores.by_time_at_company).map(([k, v]) => (
                        <div key={k} className="flex justify-between py-1 border-b last:border-0">
                          <span className="text-muted-foreground">{k}</span>
                          <span className="font-medium">{(v as number).toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}
