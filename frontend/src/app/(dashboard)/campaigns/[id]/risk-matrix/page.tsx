'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/header';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import api from '@/lib/api';
import type { RiskMatrix, RiskItem } from '@/types';
import { getRiskLevelLabel, getRiskColor } from '@/lib/utils';

const probabilityLabels: Record<number, string> = {
  1: 'Muito baixa',
  2: 'Baixa',
  3: 'Média',
  4: 'Alta',
  5: 'Muito alta',
};

const severityLabels: Record<number, string> = {
  1: 'Insignificante',
  2: 'Menor',
  3: 'Moderado',
  4: 'Grave',
  5: 'Catastrófico',
};

export default function RiskMatrixPage() {
  const { id } = useParams<{ id: string }>();

  const { data: matrix, isLoading, error } = useQuery({
    queryKey: ['risk-matrix', id],
    queryFn: async () => {
      const { data } = await api.get<RiskMatrix>(`/campaigns/campaigns/${id}/risk-matrix/`);
      return data;
    },
  });

  const getCellColor = (score: number) => {
    if (score >= 20) return 'bg-red-500 text-white';
    if (score >= 12) return 'bg-orange-400 text-white';
    if (score >= 6) return 'bg-yellow-400 text-gray-900';
    return 'bg-green-400 text-gray-900';
  };

  return (
    <div>
      <Header title="Matriz de Risco" />
      <div className="p-6 space-y-6">
        {/* Matrix visualization */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Matriz Probabilidade × Severidade</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="text-xs border-collapse w-full max-w-lg">
              <thead>
                <tr>
                  <th className="p-2 text-left text-muted-foreground">Prob \ Sev</th>
                  {[1, 2, 3, 4, 5].map((s) => (
                    <th key={s} className="p-2 text-center text-muted-foreground">{severityLabels[s]}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[5, 4, 3, 2, 1].map((prob) => (
                  <tr key={prob}>
                    <td className="p-2 font-medium text-muted-foreground">{probabilityLabels[prob]}</td>
                    {[1, 2, 3, 4, 5].map((sev) => {
                      const score = prob * sev;
                      return (
                        <td key={sev} className="p-1">
                          <div className={`h-10 w-full rounded flex items-center justify-center font-bold ${getCellColor(score)}`}>
                            {score}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-red-500 inline-block" /> Crítico (≥20)</span>
              <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-orange-400 inline-block" /> Alto (12-19)</span>
              <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-yellow-400 inline-block" /> Médio (6-11)</span>
              <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-green-400 inline-block" /> Baixo (&lt;6)</span>
            </div>
          </CardContent>
        </Card>

        {/* Risk Items */}
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : error ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Matriz de risco ainda não gerada para esta campanha.
            </CardContent>
          </Card>
        ) : !matrix?.risks?.length ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Nenhum risco identificado na matriz.
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Riscos Identificados ({matrix.risks.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-muted-foreground">
                      <th className="text-left py-2 pr-3">Dimensão</th>
                      <th className="text-left py-2 pr-3">Setor</th>
                      <th className="text-center py-2 pr-3">Prob.</th>
                      <th className="text-center py-2 pr-3">Sev.</th>
                      <th className="text-center py-2 pr-3">Score</th>
                      <th className="text-left py-2">Nível</th>
                    </tr>
                  </thead>
                  <tbody>
                    {matrix.risks
                      .sort((a: RiskItem, b: RiskItem) => b.risk_score - a.risk_score)
                      .map((risk: RiskItem) => (
                        <tr key={risk.id} className="border-b last:border-0 hover:bg-muted/30">
                          <td className="py-2 pr-3 font-medium">{risk.dimension}</td>
                          <td className="py-2 pr-3 text-muted-foreground">{risk.sector_name}</td>
                          <td className="py-2 pr-3 text-center">{probabilityLabels[risk.probability]}</td>
                          <td className="py-2 pr-3 text-center">{severityLabels[risk.severity]}</td>
                          <td className="py-2 pr-3 text-center font-bold">{risk.risk_score}</td>
                          <td className="py-2">
                            <Badge className={getRiskColor(risk.risk_level)} variant="outline">
                              {getRiskLevelLabel(risk.risk_level)}
                            </Badge>
                          </td>
                        </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
