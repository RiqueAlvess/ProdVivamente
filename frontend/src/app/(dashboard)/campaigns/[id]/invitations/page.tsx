'use client';

import { useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Users, Upload, Download, Send, Trash2, RefreshCw,
  FileText, CheckCircle2, Clock, AlertCircle, XCircle, Info,
} from 'lucide-react';
import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import api from '@/lib/api';
import { formatDate } from '@/lib/utils';
import type { InvitationListResponse, InvitationStatus } from '@/types';

// ─── Status config ────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<InvitationStatus, {
  label: string;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
  icon: React.ElementType;
  color: string;
}> = {
  pending:  { label: 'Pendente',   variant: 'secondary',    icon: Clock,        color: 'text-yellow-600' },
  sent:     { label: 'Enviado',    variant: 'default',      icon: Send,         color: 'text-blue-600'   },
  used:     { label: 'Respondido', variant: 'outline',      icon: CheckCircle2, color: 'text-green-600'  },
  expired:  { label: 'Expirado',   variant: 'destructive',  icon: XCircle,      color: 'text-red-500'    },
};

type UploadState = 'idle' | 'uploading' | 'success' | 'error';

export default function InvitationsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [uploadMsg, setUploadMsg] = useState('');
  const [taskId, setTaskId] = useState<number | null>(null);

  // ─── Queries ────────────────────────────────────────────────────────────

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['invitations', id, statusFilter],
    queryFn: async () => {
      const params = statusFilter !== 'all' ? `?status=${statusFilter}` : '';
      const { data } = await api.get<InvitationListResponse>(
        `/campaigns/campaigns/${id}/invitations/${params}`
      );
      return data;
    },
  });

  // Poll import task
  useQuery({
    queryKey: ['import-task', taskId],
    queryFn: async () => {
      const { data } = await api.get(`/core/tasks/${taskId}/`);
      if (data.status === 'completed') {
        setUploadState('success');
        setUploadMsg(data.progress_message || 'Importação concluída com sucesso!');
        setTaskId(null);
        queryClient.invalidateQueries({ queryKey: ['invitations', id] });
      } else if (data.status === 'failed') {
        setUploadState('error');
        setUploadMsg(data.error_message || 'Erro ao processar importação.');
        setTaskId(null);
      }
      return data;
    },
    enabled: !!taskId,
    refetchInterval: 2000,
  });

  // ─── Mutations ───────────────────────────────────────────────────────────

  const sendAllMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/campaigns/campaigns/${id}/invitations/send_all/`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations', id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (invId: number) => {
      await api.delete(`/campaigns/campaigns/${id}/invitations/${invId}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations', id] });
    },
  });

  // ─── CSV upload ───────────────────────────────────────────────────────────

  async function handleFileUpload(file: File) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadState('error');
      setUploadMsg('Por favor, selecione um arquivo .csv');
      return;
    }

    setUploadState('uploading');
    setUploadMsg('Enviando arquivo...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await api.post(
        `/campaigns/campaigns/${id}/invitations/import/`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      setTaskId(data.task_id);
      setUploadMsg(`${data.total_rows} registros encontrados. Processando em segundo plano...`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
        || 'Erro ao enviar arquivo.';
      setUploadState('error');
      setUploadMsg(msg);
    }
  }

  async function downloadTemplate() {
    try {
      const response = await api.get(
        `/campaigns/campaigns/${id}/invitations/template/`,
        { responseType: 'blob' }
      );
      const url = URL.createObjectURL(new Blob([response.data as Blob]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'modelo_funcionarios.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Erro ao baixar modelo.');
    }
  }

  // ─── Values ───────────────────────────────────────────────────────────────

  const stats = data?.stats;
  const invitations = data?.results ?? [];
  const pendingCount = stats?.pending ?? 0;

  return (
    <div>
      <Header title="Gerenciar Convites" />
      <div className="p-6 space-y-6">

        {/* Stats cards */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="Total" value={stats.total} Icon={Users} color="text-slate-600" />
            <StatCard label="Pendentes" value={stats.pending} Icon={Clock} color="text-yellow-600" />
            <StatCard label="Enviados" value={stats.sent} Icon={Send} color="text-blue-600" />
            <StatCard label="Respondidos" value={stats.used} Icon={CheckCircle2} color="text-green-600" />
          </div>
        )}

        <Tabs defaultValue="list">
          <TabsList>
            <TabsTrigger value="list">
              <Users className="h-4 w-4 mr-2" />
              Convites ({data?.count ?? 0})
            </TabsTrigger>
            <TabsTrigger value="import">
              <Upload className="h-4 w-4 mr-2" />
              Importar planilha
            </TabsTrigger>
          </TabsList>

          {/* ── List tab ─────────────────────────────────────────────── */}
          <TabsContent value="list" className="mt-4 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-3">
              {/* Status filter */}
              <div className="flex gap-2 flex-wrap">
                {(['all', 'pending', 'sent', 'used', 'expired'] as const).map((s) => (
                  <Button
                    key={s}
                    size="sm"
                    variant={statusFilter === s ? 'default' : 'outline'}
                    onClick={() => setStatusFilter(s)}
                    className="h-8 text-xs"
                  >
                    {s === 'all' ? 'Todos' : STATUS_CONFIG[s as InvitationStatus]?.label ?? s}
                  </Button>
                ))}
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => refetch()}
                  className="h-8"
                >
                  <RefreshCw className="h-3.5 w-3.5 mr-1" />
                  Atualizar
                </Button>
                {pendingCount > 0 && (
                  <Button
                    size="sm"
                    onClick={() => sendAllMutation.mutate()}
                    disabled={sendAllMutation.isPending}
                  >
                    <Send className="h-3.5 w-3.5 mr-1.5" />
                    {sendAllMutation.isPending
                      ? 'Enviando...'
                      : `Enviar ${pendingCount} pendente${pendingCount > 1 ? 's' : ''}`}
                  </Button>
                )}
              </div>
            </div>

            {/* LGPD notice */}
            <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 border border-blue-200 text-sm text-blue-700">
              <Info className="h-4 w-4 mt-0.5 shrink-0" />
              <span>
                Em conformidade com a LGPD, os e-mails dos participantes são armazenados
                de forma criptografada e exibidos apenas como identificadores anônimos (hash) nesta tela.
              </span>
            </div>

            {isLoading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
              </div>
            ) : invitations.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground">
                <Users className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p className="font-medium">Nenhum convite encontrado.</p>
                <p className="text-sm mt-1">
                  Use a aba &ldquo;Importar planilha&rdquo; para adicionar participantes em massa,
                  ou adicione individualmente pelo formulário acima.
                </p>
              </div>
            ) : (
              <Card>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-muted/40">
                          <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                            Hash (LGPD)
                          </th>
                          <th className="text-left py-3 px-4 font-medium text-muted-foreground">Unidade</th>
                          <th className="text-left py-3 px-4 font-medium text-muted-foreground">Setor</th>
                          <th className="text-left py-3 px-4 font-medium text-muted-foreground">Status</th>
                          <th className="text-left py-3 px-4 font-medium text-muted-foreground">Enviado em</th>
                          <th className="text-left py-3 px-4 font-medium text-muted-foreground">Respondido em</th>
                          <th className="py-3 px-4" />
                        </tr>
                      </thead>
                      <tbody>
                        {invitations.map((inv) => {
                          const cfg = STATUS_CONFIG[inv.status];
                          const StatusIcon = cfg?.icon ?? AlertCircle;
                          return (
                            <tr
                              key={inv.id}
                              className="border-b last:border-0 hover:bg-muted/20 transition-colors"
                            >
                              <td className="py-3 px-4">
                                <code className="font-mono text-xs bg-muted px-2 py-0.5 rounded select-all">
                                  {inv.email_display || inv.email_hash}
                                </code>
                              </td>
                              <td className="py-3 px-4 text-muted-foreground text-xs">
                                {inv.unidade_nome ?? '—'}
                              </td>
                              <td className="py-3 px-4 text-muted-foreground text-xs">
                                {inv.setor_nome ?? '—'}
                              </td>
                              <td className="py-3 px-4">
                                <div className="flex items-center gap-1.5">
                                  <StatusIcon className={`h-3.5 w-3.5 ${cfg?.color ?? ''}`} />
                                  <Badge variant={cfg?.variant ?? 'secondary'} className="text-xs">
                                    {cfg?.label ?? inv.status}
                                  </Badge>
                                </div>
                              </td>
                              <td className="py-3 px-4 text-muted-foreground text-xs">
                                {inv.sent_at ? formatDate(inv.sent_at) : '—'}
                              </td>
                              <td className="py-3 px-4 text-muted-foreground text-xs">
                                {inv.completed_at ? formatDate(inv.completed_at) : '—'}
                              </td>
                              <td className="py-3 px-4">
                                {inv.status !== 'used' && (
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 text-muted-foreground hover:text-destructive"
                                    onClick={() => deleteMutation.mutate(inv.id)}
                                    disabled={deleteMutation.isPending}
                                    title="Remover convite"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </Button>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* ── Import tab ────────────────────────────────────────────── */}
          <TabsContent value="import" className="mt-4 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Importar funcionários via planilha CSV
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Instructions */}
                <div className="rounded-lg border bg-muted/30 p-4 space-y-2 text-sm">
                  <p className="font-medium">Instruções:</p>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    <li>
                      O arquivo deve ser <strong>CSV</strong> com separador{' '}
                      <strong>ponto-e-vírgula (;)</strong> ou vírgula (,).
                    </li>
                    <li>
                      Colunas obrigatórias:{' '}
                      <code className="bg-muted px-1 rounded">nome</code>,{' '}
                      <code className="bg-muted px-1 rounded">email</code>,{' '}
                      <code className="bg-muted px-1 rounded">unidade</code>,{' '}
                      <code className="bg-muted px-1 rounded">setor</code>
                    </li>
                    <li>
                      Coluna opcional: <code className="bg-muted px-1 rounded">cargo</code>
                    </li>
                    <li>
                      Os e-mails serão <strong>criptografados</strong> e exibidos apenas como
                      hashes irreversíveis (conformidade LGPD).
                    </li>
                    <li>
                      Unidades, setores e cargos serão criados automaticamente se não existirem.
                    </li>
                  </ul>
                </div>

                {/* Template download */}
                <div className="flex items-center justify-between p-4 rounded-lg border bg-background">
                  <div>
                    <p className="font-medium text-sm">Baixar modelo de planilha</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Preencha com os dados dos funcionários e importe abaixo.
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={downloadTemplate}>
                    <Download className="h-4 w-4 mr-2" />
                    modelo_funcionarios.csv
                  </Button>
                </div>

                {/* Drop zone */}
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFileUpload(file);
                      e.target.value = '';
                    }}
                  />
                  <div
                    className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer
                      transition-colors hover:border-primary/60 hover:bg-primary/5
                      ${uploadState === 'uploading' ? 'opacity-60 pointer-events-none' : ''}`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      const file = e.dataTransfer.files[0];
                      if (file) handleFileUpload(file);
                    }}
                  >
                    <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
                    <p className="font-medium">Clique para selecionar ou arraste o arquivo</p>
                    <p className="text-sm text-muted-foreground mt-1">Apenas arquivos .csv</p>
                  </div>
                </div>

                {/* Upload feedback */}
                {uploadState !== 'idle' && (
                  <div className={`flex items-start gap-3 p-4 rounded-lg border text-sm ${
                    uploadState === 'success' ? 'bg-green-50 border-green-200 text-green-700' :
                    uploadState === 'error'   ? 'bg-red-50 border-red-200 text-red-700' :
                    'bg-blue-50 border-blue-200 text-blue-700'
                  }`}>
                    {uploadState === 'uploading' && (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 shrink-0 mt-0.5" />
                    )}
                    {uploadState === 'success' && <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />}
                    {uploadState === 'error' && <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />}
                    <div className="flex-1">
                      <p className="font-medium">
                        {uploadState === 'uploading' ? 'Processando importação...' :
                         uploadState === 'success'  ? 'Importação concluída!' :
                         'Erro na importação'}
                      </p>
                      <p className="mt-0.5 whitespace-pre-line">{uploadMsg}</p>
                      <button
                        className="mt-2 underline text-xs"
                        onClick={() => { setUploadState('idle'); setUploadMsg(''); }}
                      >
                        Fechar
                      </button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  Icon,
  color,
}: {
  label: string;
  value: number;
  Icon: React.ElementType;
  color: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-muted flex items-center justify-center">
            <Icon className={`h-5 w-5 ${color}`} />
          </div>
          <div>
            <p className="text-2xl font-bold leading-none">{value}</p>
            <p className="text-xs text-muted-foreground mt-1">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
