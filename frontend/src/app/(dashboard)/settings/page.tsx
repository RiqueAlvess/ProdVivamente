'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useAuthStore } from '@/store/auth-store';
import { useAuth } from '@/hooks/use-auth';
import api from '@/lib/api';

export default function SettingsPage() {
  const { user } = useAuthStore();
  const { logout } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: 'As senhas não coincidem.' });
      return;
    }
    if (newPassword.length < 8) {
      setMessage({ type: 'error', text: 'A senha deve ter pelo menos 8 caracteres.' });
      return;
    }
    setIsSaving(true);
    setMessage(null);
    try {
      await api.post('/auth/change-password/', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setMessage({ type: 'success', text: 'Senha alterada com sucesso!' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch {
      setMessage({ type: 'error', text: 'Erro ao alterar a senha. Verifique a senha atual.' });
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div>
      <Header title="Configurações" />
      <div className="p-6 max-w-2xl space-y-6">
        {/* Profile */}
        <Card>
          <CardHeader>
            <CardTitle>Perfil</CardTitle>
            <CardDescription>Informações da sua conta</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nome</Label>
                <Input value={user?.first_name ?? ''} disabled />
              </div>
              <div className="space-y-2">
                <Label>Sobrenome</Label>
                <Input value={user?.last_name ?? ''} disabled />
              </div>
            </div>
            <div className="space-y-2">
              <Label>E-mail</Label>
              <Input value={user?.email ?? ''} disabled />
            </div>
            <div className="space-y-2">
              <Label>Função</Label>
              <Input value={user?.role ?? ''} disabled className="capitalize" />
            </div>
            <p className="text-xs text-muted-foreground">
              Para alterar seus dados de perfil, entre em contato com o administrador.
            </p>
          </CardContent>
        </Card>

        {/* Change Password */}
        <Card>
          <CardHeader>
            <CardTitle>Alterar Senha</CardTitle>
            <CardDescription>Mantenha sua conta segura</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleChangePassword} className="space-y-4">
              {message && (
                <div
                  className={`p-3 rounded-md text-sm ${
                    message.type === 'success'
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : 'bg-red-50 text-red-700 border border-red-200'
                  }`}
                >
                  {message.text}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Senha atual</Label>
                <Input
                  id="currentPassword"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="newPassword">Nova senha</Label>
                <Input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirmar nova senha</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" disabled={isSaving}>
                {isSaving ? 'Salvando...' : 'Alterar senha'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Separator />

        {/* Danger Zone */}
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600">Zona de perigo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">Encerrar sessão</p>
                <p className="text-sm text-muted-foreground">Sair de todos os dispositivos</p>
              </div>
              <Button variant="destructive" onClick={logout}>
                Sair
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
