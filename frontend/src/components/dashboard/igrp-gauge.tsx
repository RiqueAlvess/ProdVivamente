'use client';

import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { RiskLevel } from '@/types';
import { getRiskLevelLabel } from '@/lib/utils';

interface IGRPGaugeProps {
  score: number;
  level: RiskLevel;
}

const levelColors: Record<RiskLevel, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

export function IGRPGauge({ score, level }: IGRPGaugeProps) {
  const percentage = (score / 4) * 100;
  const color = levelColors[level];

  const data = [{ value: percentage, fill: color }];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Índice Geral de Risco Psicossocial (IGRP)</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <div className="relative h-48 w-48">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="70%"
              outerRadius="100%"
              startAngle={90}
              endAngle={-270}
              data={data}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
              <RadialBar
                dataKey="value"
                cornerRadius={10}
                background={{ fill: '#e2e8f0' }}
                angleAxisId={0}
              />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold" style={{ color }}>
              {score.toFixed(2)}
            </span>
            <span className="text-xs text-muted-foreground">de 4.00</span>
          </div>
        </div>
        <div
          className="mt-2 px-4 py-1 rounded-full text-sm font-semibold"
          style={{ backgroundColor: `${color}20`, color }}
        >
          Risco {getRiskLevelLabel(level)}
        </div>
        <div className="mt-3 text-xs text-muted-foreground text-center">
          Escala: 0 (mínimo) → 4 (máximo risco)
        </div>
      </CardContent>
    </Card>
  );
}
