'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChecklistStage } from '@/components/checklist/checklist-stage';
import api from '@/lib/api';
import type { ChecklistStage as ChecklistStageType, ChecklistItem, ChecklistProgress } from '@/types';

interface ChecklistData {
  stages: ChecklistStageType[];
  progress: ChecklistProgress;
}

export default function ChecklistPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['checklist', id],
    queryFn: async () => {
      const { data } = await api.get<ChecklistData>(`/campaigns/campaigns/${id}/checklist/`);
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      setIsCreating(true);
      await api.post(`/campaigns/campaigns/${id}/checklist/create/`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['checklist', id] });
      setIsCreating(false);
    },
    onError: () => setIsCreating(false),
  });

  function handleItemUpdate(stageId: number, updatedItem: ChecklistItem) {
    queryClient.setQueryData<ChecklistData>(['checklist', id], (old) => {
      if (!old) return old;
      return {
        ...old,
        stages: old.stages.map((stage) => {
          if (stage.id !== stageId) return stage;
          const updatedItems = stage.items.map((item) =>
            item.id === updatedItem.id ? updatedItem : item
          );
          const completed = updatedItems.filter((i) => i.is_completed).length;
          return {
            ...stage,
            items: updatedItems,
            progress: updatedItems.length ? (completed / updatedItems.length) * 100 : 0,
          };
        }),
      };
    });
    // Refresh overall progress
    queryClient.invalidateQueries({ queryKey: ['checklist', id] });
  }

  const overallProgress = data?.progress?.overall_progress ?? 0;

  return (
    <div>
      <Header title="Checklist NR-1" />
      <div className="p-6 space-y-6">
        {/* Overall Progress */}
        {data && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Progresso Geral da Campanha</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Progress value={overallProgress} className="h-3" />
                </div>
                <span className="text-lg font-bold shrink-0">{Math.round(overallProgress)}%</span>
              </div>
              {data.progress?.stages && (
                <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-2">
                  {data.progress.stages.map((s) => (
                    <div key={s.stage_number} className="text-xs">
                      <div className="flex justify-between mb-1">
                        <span className="text-muted-foreground truncate">Etapa {s.stage_number}</span>
                        <span className="font-medium">{Math.round(s.progress)}%</span>
                      </div>
                      <Progress value={s.progress} className="h-1" />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">Checklist não encontrado para esta campanha.</p>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={isCreating}
            >
              {isCreating ? 'Criando...' : 'Criar checklist NR-1'}
            </Button>
          </div>
        ) : !data?.stages?.length ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">Nenhuma etapa encontrada.</p>
            <Button onClick={() => createMutation.mutate()} disabled={isCreating}>
              {isCreating ? 'Criando...' : 'Inicializar checklist'}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {data.stages.map((stage) => (
              <ChecklistStage
                key={stage.id}
                stage={stage}
                campaignId={id}
                onItemUpdate={handleItemUpdate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
