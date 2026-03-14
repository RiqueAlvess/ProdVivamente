'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { TaskStatusBadge } from './task-status-badge';
import { useTaskPolling } from '@/hooks/use-task-polling';
import { Download, Loader2 } from 'lucide-react';
import api from '@/lib/api';

interface AsyncExportButtonProps {
  label?: string;
  endpoint: string;
  payload?: Record<string, unknown>;
  filename?: string;
}

export function AsyncExportButton({
  label = 'Exportar',
  endpoint,
  payload = {},
  filename = 'export',
}: AsyncExportButtonProps) {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const task = useTaskPolling(taskId);

  async function startExport() {
    setIsStarting(true);
    try {
      const { data } = await api.post<{ task_id: string }>(endpoint, payload);
      setTaskId(data.task_id);
    } catch {
      alert('Erro ao iniciar exportação. Tente novamente.');
    } finally {
      setIsStarting(false);
    }
  }

  function reset() {
    setTaskId(null);
  }

  if (!taskId) {
    return (
      <Button onClick={startExport} disabled={isStarting} variant="outline">
        {isStarting ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Download className="h-4 w-4 mr-2" />
        )}
        {label}
      </Button>
    );
  }

  if (!task) {
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Iniciando...</span>
      </div>
    );
  }

  if (task.status === 'failed') {
    return (
      <div className="flex items-center gap-2">
        <TaskStatusBadge status="failed" />
        <Button variant="ghost" size="sm" onClick={reset}>Tentar novamente</Button>
      </div>
    );
  }

  if (task.status === 'completed' && task.result_url) {
    return (
      <div className="flex items-center gap-2">
        <TaskStatusBadge status="completed" />
        <Button asChild size="sm">
          <a href={task.result_url} download={filename} target="_blank" rel="noopener noreferrer">
            <Download className="h-4 w-4 mr-2" />
            Baixar arquivo
          </a>
        </Button>
        <Button variant="ghost" size="sm" onClick={reset}>Nova exportação</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 min-w-[200px]">
      <div className="flex items-center gap-2">
        <TaskStatusBadge status={task.status} progress={task.progress} />
      </div>
      <Progress value={task.progress ?? 0} className="h-2" />
      <p className="text-xs text-muted-foreground">Aguarde, processando...</p>
    </div>
  );
}
