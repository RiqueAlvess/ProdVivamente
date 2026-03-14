'use client';

import Link from 'next/link';
import { Plus, ChevronRight } from 'lucide-react';
import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useCampaigns } from '@/hooks/use-campaigns';
import { formatDate, formatPercent, getCampaignStatusLabel } from '@/lib/utils';
import type { CampaignStatus } from '@/types';

const statusVariants: Record<CampaignStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'secondary',
  active: 'default',
  closed: 'outline',
  archived: 'outline',
};

export default function CampaignsPage() {
  const { data, isLoading, error } = useCampaigns();

  return (
    <div>
      <Header title="Campanhas" />
      <div className="p-6 space-y-4">
        <div className="flex justify-end">
          <Button asChild>
            <Link href="/campaigns/new">
              <Plus className="h-4 w-4 mr-2" />
              Nova Campanha
            </Link>
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : error ? (
          <div className="text-center text-destructive py-10">Erro ao carregar campanhas.</div>
        ) : !data?.results?.length ? (
          <div className="text-center text-muted-foreground py-16">
            <p className="text-lg mb-2">Nenhuma campanha encontrada.</p>
            <p className="text-sm">Crie sua primeira campanha de avaliação de clima organizacional.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {data.results.map((campaign) => (
              <Card key={campaign.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-base">{campaign.name}</h3>
                        <Badge variant={statusVariants[campaign.status]}>
                          {getCampaignStatusLabel(campaign.status)}
                        </Badge>
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground flex flex-wrap gap-3">
                        <span>{formatDate(campaign.start_date)} → {formatDate(campaign.end_date)}</span>
                        {campaign.invitation_count !== undefined && (
                          <span>{campaign.invitation_count} convidados</span>
                        )}
                        {campaign.response_rate !== undefined && (
                          <span>{formatPercent(campaign.response_rate)} adesão</span>
                        )}
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/campaigns/${campaign.id}`}>
                        Ver detalhes
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
