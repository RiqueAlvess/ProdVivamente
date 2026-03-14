'use client';

import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { RiskDistribution } from '@/types';

interface RiskDistributionChartProps {
  distribution: RiskDistribution;
}

const COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

const LABELS = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
};

export function RiskDistributionChart({ distribution }: RiskDistributionChartProps) {
  const data = Object.entries(distribution)
    .filter(([, value]) => value > 0)
    .map(([key, value]) => ({
      name: LABELS[key as keyof typeof LABELS],
      value,
      color: COLORS[key as keyof typeof COLORS],
    }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Distribuição de Risco</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => [`${value} setores`, '']} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
