import { useState, useEffect } from 'react';
import api from '@/lib/api';
import type { AsyncTask } from '@/types';

export function useTaskPolling(taskId: string | null) {
  const [task, setTask] = useState<AsyncTask | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const { data } = await api.get<AsyncTask>(`/core/tasks/${taskId}/`);
        setTask(data);
        if (['completed', 'failed'].includes(data.status)) {
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId]);

  return task;
}
