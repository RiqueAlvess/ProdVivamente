// ─── Autenticação ────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_active: boolean;
  role?: 'rh' | 'lideranca';
  empresa_id?: number;
  empresa_nome?: string;
  profile?: UserProfile;
}

export interface UserProfile {
  id: number;
  role: 'rh' | 'lideranca';
  empresa?: number;
  empresa_nome?: string;
  telefone?: string;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

// ─── Empresa ─────────────────────────────────────────────────────────────────

export interface Empresa {
  id: number;
  nome: string;
  cnpj: string;
  slug: string;
  total_funcionarios: number;
  cnae: string;
  cnae_descricao: string;
  admin_email: string;
  ativo: boolean;
  created_at: string;
  updated_at: string;
}

// ─── Campanha ─────────────────────────────────────────────────────────────────

export type StatusCampanha = 'draft' | 'active' | 'closed' | 'archived';

export interface Campaign {
  id: number;
  name: string;
  company: number;
  status: StatusCampanha;
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
  response_count?: number;
  invitation_count?: number;
  response_rate?: number;
}

// Aliases em inglês mantidos para compatibilidade com componentes existentes
export type CampaignStatus = StatusCampanha;

// ─── Convite ─────────────────────────────────────────────────────────────────

export type StatusConvite = 'pending' | 'sent' | 'used' | 'expired';
export type InvitationStatus = StatusConvite;

export interface Invitation {
  id: number;
  campaign: number;
  /** LGPD: primeiros 16 chars do hash HMAC-SHA256 — nunca o e-mail real */
  email_hash: string;
  email_display: string;
  unidade?: number;
  unidade_nome?: string;
  setor?: number;
  setor_nome?: string;
  cargo?: number;
  cargo_nome?: string;
  status: StatusConvite;
  sent_at?: string;
  completed_at?: string;
  expires_at?: string;
  created_at: string;
}

export interface EstatisticasConvite {
  total: number;
  pending: number;
  sent: number;
  used: number;
  expired: number;
}

export interface InvitationStats extends EstatisticasConvite {}

export interface InvitationListResponse {
  count: number;
  results: Invitation[];
  stats: EstatisticasConvite;
}

// ─── Pesquisa ─────────────────────────────────────────────────────────────────

export interface SurveyQuestion {
  id: number;
  order: number;
  text: string;
  dimension: string;
}

export interface SurveyResponse {
  token: string;
  lgpd_consent: boolean;
  demographics?: Demographics;
  answers: Answer[];
  feedback?: string;
}

export interface Demographics {
  gender?: 'M' | 'F' | 'NB' | 'NO_ANSWER';
  age_range?: '18-24' | '25-34' | '35-44' | '45-54' | '55+' | 'NO_ANSWER';
  time_at_company?: '<1' | '1-3' | '3-5' | '5-10' | '10+' | 'NO_ANSWER';
}

export interface Answer {
  question_id: number;
  value: 0 | 1 | 2 | 3 | 4;
}

export interface SurveyData {
  campaign_name: string;
  company_name: string;
  questions: SurveyQuestion[];
  already_completed: boolean;
}

// ─── Analytics / Dashboard ───────────────────────────────────────────────────

export type NivelRisco = 'critical' | 'high' | 'medium' | 'low';
export type RiskLevel = NivelRisco;

export interface DashboardMetrics {
  total_invited: number;
  total_responded: number;
  response_rate: number;
  igrp_score: number;
  igrp_level: NivelRisco;
  dimension_scores: DimensionScore[];
  risk_distribution: RiskDistribution;
  top_critical_sectors: SectorRisk[];
  heatmap: HeatmapCell[];
  demographic_scores?: DemographicScores;
}

export interface DimensionScore {
  dimension: string;
  score: number;
  label: string;
}

export interface RiskDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface SectorRisk {
  sector_id: number;
  sector_name: string;
  igrp_score: number;
  risk_level: NivelRisco;
  response_count: number;
}

export interface HeatmapCell {
  sector_id: number;
  sector_name: string;
  dimension: string;
  score: number;
  risk_level: NivelRisco;
}

export interface DemographicScores {
  by_gender: Record<string, number>;
  by_age_range: Record<string, number>;
  by_time_at_company: Record<string, number>;
}

// ─── Checklist ───────────────────────────────────────────────────────────────

export interface ChecklistStage {
  id: number;
  campaign: number;
  stage_number: number;
  stage_name: string;
  items: ChecklistItem[];
  progress: number;
}

export interface ChecklistItem {
  id: number;
  stage: number;
  order: number;
  description: string;
  is_completed: boolean;
  responsible?: string;
  deadline?: string;
  notes?: string;
  evidence_url?: string;
  evidence_filename?: string;
}

export interface ChecklistProgress {
  campaign_id: number;
  overall_progress: number;
  stages: { stage_number: number; stage_name: string; progress: number }[];
}

// ─── Planos de Ação ───────────────────────────────────────────────────────────

export type StatusAcao = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type ActionStatus = StatusAcao;

export interface ActionPlan {
  id: number;
  campaign: number;
  title: string;
  description: string;
  status: StatusAcao;
  responsible?: string;
  due_date?: string;
  sector?: number;
  sector_name?: string;
  dimension?: string;
  risk_level?: NivelRisco;
  created_at: string;
  updated_at: string;
}

// ─── Matriz de Risco ──────────────────────────────────────────────────────────

export interface RiskMatrix {
  id: number;
  campaign: number;
  generated_at: string;
  risks: RiskItem[];
}

export interface RiskItem {
  id: number;
  dimension: string;
  sector_id: number;
  sector_name: string;
  probability: 1 | 2 | 3 | 4 | 5;
  severity: 1 | 2 | 3 | 4 | 5;
  risk_score: number;
  risk_level: NivelRisco;
  description?: string;
}

// ─── Tarefas assíncronas ──────────────────────────────────────────────────────

export type StatusTarefa = 'pending' | 'running' | 'completed' | 'failed';
export type TaskStatus = StatusTarefa;

export interface AsyncTask {
  id: string;
  status: StatusTarefa;
  progress: number;
  result_url?: string;
  error?: string;
  created_at: string;
  updated_at: string;
}

// ─── Notificações ─────────────────────────────────────────────────────────────

export interface Notification {
  id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  link?: string;
  type: 'info' | 'warning' | 'success' | 'error';
}

// ─── Paginação ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
