'use client';

import { useState } from 'react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { ChecklistItem } from './checklist-item';
import type { ChecklistStage as ChecklistStageType, ChecklistItem as ChecklistItemType } from '@/types';

interface ChecklistStageProps {
  stage: ChecklistStageType;
  campaignId: string | number;
  onItemUpdate: (stageId: number, updatedItem: ChecklistItemType) => void;
}

export function ChecklistStage({ stage, campaignId, onItemUpdate }: ChecklistStageProps) {
  const [isOpen, setIsOpen] = useState(stage.stage_number === 1);

  const completedCount = stage.items.filter((i) => i.is_completed).length;

  function getProgressColor(progress: number) {
    if (progress === 100) return 'bg-green-500';
    if (progress >= 50) return 'bg-yellow-500';
    return 'bg-blue-500';
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center gap-4 p-4 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? (
          <ChevronDown className="h-5 w-5 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm">
              Etapa {stage.stage_number}: {stage.stage_name}
            </span>
            <Badge variant={stage.progress === 100 ? 'default' : 'secondary'} className="text-xs">
              {completedCount}/{stage.items.length}
            </Badge>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-1.5">
              <div
                className={`h-1.5 rounded-full transition-all ${getProgressColor(stage.progress)}`}
                style={{ width: `${stage.progress}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground shrink-0">{Math.round(stage.progress)}%</span>
          </div>
        </div>
      </button>

      {isOpen && (
        <div className="p-4 space-y-3">
          {stage.items.map((item) => (
            <ChecklistItem
              key={item.id}
              item={item}
              campaignId={campaignId}
              onUpdate={(updatedItem) => onItemUpdate(stage.id, updatedItem)}
            />
          ))}
          {stage.items.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">Nenhum item nesta etapa.</p>
          )}
        </div>
      )}
    </div>
  );
}
