'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AsyncExportButton } from '@/components/shared/async-export-button';
import api from '@/lib/api';
import type { ActionPlan, PaginatedResponse, ActionStatus } from '@/types';
import { formatDate, getActionStatusLabel } from '@/lib/utils';

const statusVariants: Record<ActionStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'secondary',
  in_progress: 'default',
  completed: 'outline',
  cancelled: 'destructive',
};

const statusColors: Record<ActionStatus, string> = {
  pending: 'text-yellow-600',
  in_progress: 'text-blue-600',
  completed: 'text-green-600',
  cancelled: 'text-red-600',
};

export default function ActionsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [form, setForm] = useState({
    title: '',
    description: '',
    responsible: '',
    due_date: '',
    dimension: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['actions', id],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<ActionPlan>>(
        `/campaigns/campaigns/${id}/actions/`
      );
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/campaigns/campaigns/${id}/actions/`, {
        ...form,
        campaign: Number(id),
        status: 'pending',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions', id] });
      setForm({ title: '', description: '', responsible: '', due_date: '', dimension: '' });
      setIsOpen(false);
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: async ({ actionId, status }: { actionId: number; status: ActionStatus }) => {
      await api.patch(`/campaigns/campaigns/${id}/actions/${actionId}/`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions', id] });
    },
  });

  return (
    <div>
      <Header title="Planos de Ação" />
      <div className="p-6 space-y-4">
        <div className="flex justify-between items-center flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <p className="text-muted-foreground text-sm">
              {data?.count ?? 0} planos de ação
            </p>
            <AsyncExportButton
              label="Exportar Word"
              endpoint={`/campaigns/campaigns/${id}/actions/export_word/`}
              payload={{ campaign_id: Number(id) }}
              filename={`planos-acao-campanha-${id}.docx`}
            />
          </div>
          <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Novo plano
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Criar Plano de Ação</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-2">
                <div className="space-y-2">
                  <Label>Título *</Label>
                  <Input
                    value={form.title}
                    onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
                    placeholder="Título do plano de ação"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Descrição *</Label>
                  <Textarea
                    value={form.description}
                    onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                    placeholder="Descreva as ações a serem tomadas..."
                    rows={4}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label>Responsável</Label>
                    <Input
                      value={form.responsible}
                      onChange={(e) => setForm((p) => ({ ...p, responsible: e.target.value }))}
                      placeholder="Nome do responsável"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Prazo</Label>
                    <Input
                      type="date"
                      value={form.due_date}
                      onChange={(e) => setForm((p) => ({ ...p, due_date: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Dimensão</Label>
                  <Input
                    value={form.dimension}
                    onChange={(e) => setForm((p) => ({ ...p, dimension: e.target.value }))}
                    placeholder="Ex: Demandas de trabalho"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  onClick={() => createMutation.mutate()}
                  disabled={!form.title || !form.description || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Criando...' : 'Criar plano'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : !data?.results?.length ? (
          <div className="text-center py-16 text-muted-foreground">
            <p className="mb-2">Nenhum plano de ação criado.</p>
            <p className="text-sm">Crie planos de ação para endereçar os riscos identificados.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {data.results.map((action) => (
              <Card key={action.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <CardTitle className="text-base">{action.title}</CardTitle>
                        <Badge variant={statusVariants[action.status]}>
                          {getActionStatusLabel(action.status)}
                        </Badge>
                        {action.dimension && (
                          <Badge variant="outline" className="text-xs">{action.dimension}</Badge>
                        )}
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground flex gap-3 flex-wrap">
                        {action.responsible && <span>Resp: {action.responsible}</span>}
                        {action.due_date && <span>Prazo: {formatDate(action.due_date)}</span>}
                        {action.sector_name && <span>Setor: {action.sector_name}</span>}
                      </div>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {action.status === 'pending' && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-blue-600 border-blue-200 hover:bg-blue-50"
                          onClick={() =>
                            updateStatusMutation.mutate({ actionId: action.id, status: 'in_progress' })
                          }
                          disabled={updateStatusMutation.isPending}
                        >
                          Iniciar
                        </Button>
                      )}
                      {action.status === 'in_progress' && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-green-600 border-green-200 hover:bg-green-50"
                          onClick={() =>
                            updateStatusMutation.mutate({ actionId: action.id, status: 'completed' })
                          }
                          disabled={updateStatusMutation.isPending}
                        >
                          Concluir
                        </Button>
                      )}
                      {action.status !== 'cancelled' && action.status !== 'completed' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-500 hover:text-red-700"
                          onClick={() =>
                            updateStatusMutation.mutate({ actionId: action.id, status: 'cancelled' })
                          }
                          disabled={updateStatusMutation.isPending}
                        >
                          Cancelar
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">{action.description}</p>
                  <p className="text-xs text-muted-foreground mt-3">
                    Criado em {formatDate(action.created_at)} · Atualizado em {formatDate(action.updated_at)}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
