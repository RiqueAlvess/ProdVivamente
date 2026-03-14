import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { RiskLevel } from '@/types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'critical':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'high':
      return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'medium':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'low':
      return 'text-green-600 bg-green-50 border-green-200';
  }
}

export function getRiskBadgeVariant(level: RiskLevel): 'destructive' | 'default' | 'secondary' | 'outline' {
  switch (level) {
    case 'critical':
      return 'destructive';
    case 'high':
      return 'default';
    case 'medium':
      return 'secondary';
    case 'low':
      return 'outline';
  }
}

export function getDimensionScoreColor(score: number): string {
  if (score < 2) return 'text-red-600';
  if (score < 3) return 'text-yellow-600';
  return 'text-green-600';
}

export function getDimensionScoreBg(score: number): string {
  if (score < 2) return 'bg-red-500';
  if (score < 3) return 'bg-yellow-500';
  return 'bg-green-500';
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}

export function getRiskLevelLabel(level: RiskLevel): string {
  switch (level) {
    case 'critical':
      return 'Crítico';
    case 'high':
      return 'Alto';
    case 'medium':
      return 'Médio';
    case 'low':
      return 'Baixo';
  }
}

export function getCampaignStatusLabel(status: string): string {
  switch (status) {
    case 'draft':
      return 'Rascunho';
    case 'active':
      return 'Ativa';
    case 'closed':
      return 'Encerrada';
    case 'archived':
      return 'Arquivada';
    default:
      return status;
  }
}

export function getActionStatusLabel(status: string): string {
  switch (status) {
    case 'pending':
      return 'Pendente';
    case 'in_progress':
      return 'Em andamento';
    case 'completed':
      return 'Concluído';
    case 'cancelled':
      return 'Cancelado';
    default:
      return status;
  }
}
