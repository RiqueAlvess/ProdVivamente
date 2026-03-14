import { Badge } from '@/components/ui/badge';
import type { TaskStatus } from '@/types';

interface TaskStatusBadgeProps {
  status: TaskStatus;
  progress?: number;
}

const statusConfig: Record<TaskStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  pending: { label: 'Aguardando', variant: 'secondary' },
  running: { label: 'Processando', variant: 'default' },
  completed: { label: 'Concluído', variant: 'outline' },
  failed: { label: 'Erro', variant: 'destructive' },
};

export function TaskStatusBadge({ status, progress }: TaskStatusBadgeProps) {
  const config = statusConfig[status];
  return (
    <Badge variant={config.variant}>
      {config.label}
      {status === 'running' && progress !== undefined && ` (${progress}%)`}
    </Badge>
  );
}
