'use client';

import { useState, useRef } from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Paperclip, Upload, Loader2 } from 'lucide-react';
import api from '@/lib/api';
import type { ChecklistItem as ChecklistItemType } from '@/types';

interface ChecklistItemProps {
  item: ChecklistItemType;
  campaignId: string | number;
  onUpdate: (updatedItem: ChecklistItemType) => void;
}

export function ChecklistItem({ item, campaignId, onUpdate }: ChecklistItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [localItem, setLocalItem] = useState(item);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function saveField(field: Partial<ChecklistItemType>) {
    setIsSaving(true);
    try {
      const updated = { ...localItem, ...field };
      setLocalItem(updated);
      await api.patch(`/campaigns/campaigns/${campaignId}/checklist/items/${item.id}/`, field);
      onUpdate(updated);
    } catch {
      // revert on error
      setLocalItem(item);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleFileUpload(file: File) {
    if (file.size > 10 * 1024 * 1024) {
      alert('Arquivo muito grande. Máximo permitido: 10MB.');
      return;
    }
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('evidence', file);
      const { data } = await api.patch(
        `/campaigns/campaigns/${campaignId}/checklist/items/${item.id}/upload_evidence/`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      const updated = { ...localItem, evidence_url: data.evidence_url, evidence_filename: data.evidence_filename };
      setLocalItem(updated);
      onUpdate(updated);
    } catch {
      alert('Erro ao fazer upload do arquivo.');
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className={`border rounded-lg p-4 transition-all ${localItem.is_completed ? 'bg-green-50 border-green-200' : 'bg-white'}`}>
      <div className="flex items-start gap-3">
        <Checkbox
          checked={localItem.is_completed}
          onCheckedChange={(checked) => saveField({ is_completed: !!checked })}
          className="mt-0.5"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2">
            <p className={`text-sm flex-1 ${localItem.is_completed ? 'line-through text-muted-foreground' : ''}`}>
              {localItem.description}
            </p>
            <div className="flex items-center gap-2 shrink-0">
              {isSaving && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
              {localItem.evidence_url && (
                <Badge variant="secondary" className="text-xs">
                  <Paperclip className="h-3 w-3 mr-1" />
                  Evidência
                </Badge>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? 'Fechar' : 'Detalhes'}
              </Button>
            </div>
          </div>

          {isExpanded && (
            <div className="mt-4 space-y-3 border-t pt-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">Responsável</Label>
                  <Input
                    value={localItem.responsible ?? ''}
                    onChange={(e) => setLocalItem({ ...localItem, responsible: e.target.value })}
                    onBlur={(e) => saveField({ responsible: e.target.value })}
                    placeholder="Nome do responsável"
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Prazo</Label>
                  <Input
                    type="date"
                    value={localItem.deadline ?? ''}
                    onChange={(e) => setLocalItem({ ...localItem, deadline: e.target.value })}
                    onBlur={(e) => saveField({ deadline: e.target.value })}
                    className="h-8 text-sm"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Observações</Label>
                <Textarea
                  value={localItem.notes ?? ''}
                  onChange={(e) => setLocalItem({ ...localItem, notes: e.target.value })}
                  onBlur={(e) => saveField({ notes: e.target.value })}
                  placeholder="Adicione observações..."
                  rows={2}
                  className="text-sm"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Evidência (máx. 10MB)</Label>
                <div className="flex items-center gap-2">
                  {localItem.evidence_url ? (
                    <a
                      href={localItem.evidence_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline truncate max-w-xs"
                    >
                      {localItem.evidence_filename ?? 'Ver evidência'}
                    </a>
                  ) : (
                    <span className="text-sm text-muted-foreground">Nenhuma evidência</span>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isUploading}
                  >
                    {isUploading ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                    ) : (
                      <Upload className="h-3 w-3 mr-1" />
                    )}
                    {localItem.evidence_url ? 'Substituir' : 'Upload'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
