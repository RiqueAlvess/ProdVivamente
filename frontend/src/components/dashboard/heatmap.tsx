'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { HeatmapCell } from '@/types';

interface HeatmapProps {
  cells: HeatmapCell[];
}

const riskColors: Record<string, string> = {
  critical: 'bg-red-500 text-white',
  high: 'bg-orange-400 text-white',
  medium: 'bg-yellow-400 text-gray-900',
  low: 'bg-green-400 text-gray-900',
};

export function Heatmap({ cells }: HeatmapProps) {
  if (!cells || cells.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-base">Mapa de Calor: Setor × Dimensão</CardTitle></CardHeader>
        <CardContent><p className="text-muted-foreground text-sm">Dados insuficientes</p></CardContent>
      </Card>
    );
  }

  const sectors = Array.from(new Set(cells.map((c) => c.sector_name)));
  const dimensions = Array.from(new Set(cells.map((c) => c.dimension)));

  const cellMap = new Map(cells.map((c) => [`${c.sector_name}__${c.dimension}`, c]));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Mapa de Calor: Setor × Dimensão</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="text-xs w-full">
            <thead>
              <tr>
                <th className="text-left py-1 pr-2 font-medium text-muted-foreground min-w-[120px]">Setor</th>
                {dimensions.map((dim) => (
                  <th key={dim} className="text-center py-1 px-1 font-medium text-muted-foreground min-w-[70px]">
                    {dim}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sectors.map((sector) => (
                <tr key={sector}>
                  <td className="py-1 pr-2 font-medium truncate max-w-[120px]">{sector}</td>
                  {dimensions.map((dim) => {
                    const cell = cellMap.get(`${sector}__${dim}`);
                    return (
                      <td key={dim} className="py-1 px-1 text-center">
                        {cell ? (
                          <span
                            className={`inline-block rounded px-2 py-0.5 font-semibold ${riskColors[cell.risk_level]}`}
                            title={`${cell.score.toFixed(2)}`}
                          >
                            {cell.score.toFixed(1)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-red-500 inline-block" /> Crítico</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-orange-400 inline-block" /> Alto</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-yellow-400 inline-block" /> Médio</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-green-400 inline-block" /> Baixo</span>
        </div>
      </CardContent>
    </Card>
  );
}
