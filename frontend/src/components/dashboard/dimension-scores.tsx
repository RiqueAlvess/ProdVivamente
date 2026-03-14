'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getDimensionScoreBg, getDimensionScoreColor } from '@/lib/utils';
import type { DimensionScore } from '@/types';

interface DimensionScoresProps {
  scores: DimensionScore[];
}

export function DimensionScores({ scores }: DimensionScoresProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Pontuação por Dimensão</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {scores.map((item) => (
            <div key={item.dimension}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium">{item.label}</span>
                <span className={`text-sm font-bold ${getDimensionScoreColor(item.score)}`}>
                  {item.score.toFixed(1)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${getDimensionScoreBg(item.score)}`}
                  style={{ width: `${(item.score / 4) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500 inline-block" /> Crítico (&lt;2)</span>
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-yellow-500 inline-block" /> Médio (&lt;3)</span>
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-green-500 inline-block" /> Bom (&ge;3)</span>
        </div>
      </CardContent>
    </Card>
  );
}
