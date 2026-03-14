'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreateCampaign } from '@/hooks/use-campaigns';

export default function NewCampaignPage() {
  const router = useRouter();
  const { mutateAsync: createCampaign, isPending } = useCreateCampaign();
  const [form, setForm] = useState({
    name: '',
    start_date: '',
    end_date: '',
  });
  const [error, setError] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!form.name || !form.start_date || !form.end_date) {
      setError('Preencha todos os campos.');
      return;
    }
    if (form.end_date <= form.start_date) {
      setError('A data de encerramento deve ser posterior à data de início.');
      return;
    }
    try {
      const campaign = await createCampaign({ ...form, status: 'draft' });
      router.push(`/campaigns/${campaign.id}`);
    } catch {
      setError('Erro ao criar campanha. Tente novamente.');
    }
  }

  return (
    <div>
      <Header title="Nova Campanha" />
      <div className="p-6 max-w-xl">
        <Card>
          <CardHeader>
            <CardTitle>Criar Campanha de Avaliação</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
                  {error}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="name">Nome da campanha *</Label>
                <Input
                  id="name"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  placeholder="Ex: Pesquisa Clima 2025 – 1º Semestre"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start_date">Data de início *</Label>
                  <Input
                    id="start_date"
                    name="start_date"
                    type="date"
                    value={form.start_date}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_date">Data de encerramento *</Label>
                  <Input
                    id="end_date"
                    name="end_date"
                    type="date"
                    value={form.end_date}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => router.back()}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={isPending}>
                  {isPending ? 'Criando...' : 'Criar campanha'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
