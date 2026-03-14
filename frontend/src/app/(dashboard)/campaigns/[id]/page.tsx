'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  Users,
  ClipboardList,
  CheckSquare,
  Target,
  BarChart3,
  Calendar,
  ArrowRight,
} from 'lucide-react';
import { Header } from '@/components/layout/header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCampaign } from '@/hooks/use-campaigns';
import { formatDate, formatPercent, getCampaignStatusLabel } from '@/lib/utils';
import type { CampaignStatus } from '@/types';

const statusVariants: Record<CampaignStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'secondary',
  active: 'default',
  closed: 'outline',
  archived: 'outline',
};

const sections = [
  { title: 'Convites', description: 'Gerenciar participantes e enviar convites', icon: Users, href: 'invitations' },
  { title: 'Checklist NR-1', description: 'Acompanhar as 6 etapas de conformidade', icon: CheckSquare, href: 'checklist' },
  { title: 'Planos de Ação', description: 'Criar e monitorar ações corretivas', icon: Target, href: 'actions' },
  { title: 'Matriz de Risco', description: 'Visualizar e analisar riscos identificados', icon: BarChart3, href: 'risk-matrix' },
];

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: campaign, isLoading, error } = useCampaign(id);

  if (isLoading) {
    return (
      <div>
        <Header title="Campanha" />
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div>
        <Header title="Campanha" />
        <div className="p-6 text-destructive">Erro ao carregar campanha.</div>
      </div>
    );
  }

  return (
    <div>
      <Header title={campaign.name} />
      <div className="p-6 space-y-6">
        {/* Campaign Info */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-xl font-bold">{campaign.name}</h2>
                  <Badge variant={statusVariants[campaign.status]}>
                    {getCampaignStatusLabel(campaign.status)}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(campaign.start_date)} → {formatDate(campaign.end_date)}
                  </span>
                  {campaign.invitation_count !== undefined && (
                    <span>{campaign.invitation_count} convidados</span>
                  )}
                  {campaign.response_rate !== undefined && (
                    <span>{formatPercent(campaign.response_rate)} adesão</span>
                  )}
                </div>
              </div>
              {campaign.status === 'active' && (
                <Button asChild variant="outline">
                  <Link href={`/campaigns/${id}/invitations`}>
                    <Users className="h-4 w-4 mr-2" />
                    Gerenciar convites
                  </Link>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {sections.map((section) => (
            <Card
              key={section.href}
              className="hover:shadow-md transition-shadow cursor-pointer group"
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                      <section.icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{section.title}</CardTitle>
                      <p className="text-sm text-muted-foreground">{section.description}</p>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <Button asChild variant="outline" size="sm" className="w-full">
                  <Link href={`/campaigns/${id}/${section.href}`}>
                    Acessar {section.title}
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Analytics Link */}
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <BarChart3 className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="font-medium">Análise Completa</p>
                  <p className="text-sm text-muted-foreground">Ver dashboard de analytics desta campanha</p>
                </div>
              </div>
              <Button variant="outline" asChild>
                <Link href={`/analytics?campaign=${id}`}>
                  Ver analytics
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Checklist shortcut */}
        <div className="flex items-center gap-2">
          <ClipboardList className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            Criado em {formatDate(campaign.created_at)} · Atualizado em {formatDate(campaign.updated_at)}
          </span>
        </div>
      </div>
    </div>
  );
}
