'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Send, Trash2 } from 'lucide-react';
import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import api from '@/lib/api';
import type { Invitation, PaginatedResponse, Sector } from '@/types';
import { formatDate } from '@/lib/utils';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const statusColors: Record<string, string> = {
  pending: 'secondary',
  sent: 'default',
  opened: 'outline',
  completed: 'outline',
  bounced: 'destructive',
};

const statusLabels: Record<string, string> = {
  pending: 'Pendente',
  sent: 'Enviado',
  opened: 'Aberto',
  completed: 'Respondido',
  bounced: 'Inválido',
};

export default function InvitationsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newSector, setNewSector] = useState('');

  const { data: invitations, isLoading } = useQuery({
    queryKey: ['invitations', id],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Invitation>>(`/campaigns/campaigns/${id}/invitations/`);
      return data;
    },
  });

  const { data: sectors } = useQuery({
    queryKey: ['sectors'],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Sector>>('/companies/sectors/');
      return data.results;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/campaigns/campaigns/${id}/invitations/`, {
        email: newEmail,
        sector: Number(newSector),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations', id] });
      setNewEmail('');
      setNewSector('');
      setIsOpen(false);
    },
  });

  const sendAllMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/campaigns/campaigns/${id}/invitations/send_all/`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations', id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (invitationId: number) => {
      await api.delete(`/campaigns/campaigns/${id}/invitations/${invitationId}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations', id] });
    },
  });

  return (
    <div>
      <Header title="Gerenciar Convites" />
      <div className="p-6 space-y-4">
        <div className="flex justify-between items-center flex-wrap gap-3">
          <p className="text-muted-foreground text-sm">
            {invitations?.count ?? 0} convites · {invitations?.results?.filter(i => i.status === 'completed').length ?? 0} respondidos
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => sendAllMutation.mutate()}
              disabled={sendAllMutation.isPending}
            >
              <Send className="h-4 w-4 mr-2" />
              {sendAllMutation.isPending ? 'Enviando...' : 'Enviar todos pendentes'}
            </Button>
            <Dialog open={isOpen} onOpenChange={setIsOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Adicionar convite
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Novo Convite</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-2">
                  <div className="space-y-2">
                    <Label>E-mail</Label>
                    <Input
                      type="email"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      placeholder="colaborador@empresa.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Setor</Label>
                    <Select onValueChange={setNewSector}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecionar setor" />
                      </SelectTrigger>
                      <SelectContent>
                        {sectors?.map((s) => (
                          <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    onClick={() => createMutation.mutate()}
                    disabled={!newEmail || !newSector || createMutation.isPending}
                  >
                    {createMutation.isPending ? 'Adicionando...' : 'Adicionar'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Lista de Convites</CardTitle>
            </CardHeader>
            <CardContent>
              {!invitations?.results?.length ? (
                <p className="text-muted-foreground text-sm py-4 text-center">Nenhum convite cadastrado.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-muted-foreground">
                        <th className="text-left py-2 pr-4">E-mail</th>
                        <th className="text-left py-2 pr-4">Setor</th>
                        <th className="text-left py-2 pr-4">Status</th>
                        <th className="text-left py-2 pr-4">Enviado em</th>
                        <th className="text-left py-2">Respondido em</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {invitations.results.map((inv) => (
                        <tr key={inv.id} className="border-b last:border-0 hover:bg-muted/30">
                          <td className="py-2 pr-4 font-medium">{inv.email}</td>
                          <td className="py-2 pr-4 text-muted-foreground">{inv.sector_name ?? inv.sector}</td>
                          <td className="py-2 pr-4">
                            <Badge variant={statusColors[inv.status] as 'default' | 'secondary' | 'destructive' | 'outline'}>
                              {statusLabels[inv.status]}
                            </Badge>
                          </td>
                          <td className="py-2 pr-4 text-muted-foreground">
                            {inv.sent_at ? formatDate(inv.sent_at) : '—'}
                          </td>
                          <td className="py-2 text-muted-foreground">
                            {inv.completed_at ? formatDate(inv.completed_at) : '—'}
                          </td>
                          <td className="py-2">
                            {inv.status !== 'completed' && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7"
                                onClick={() => deleteMutation.mutate(inv.id)}
                              >
                                <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
