import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login as authLogin, logout as authLogout } from '@/lib/auth';
import { useAuthStore } from '@/store/auth-store';
import type { LoginCredentials } from '@/types';

export function useAuth() {
  const { user, isAuthenticated, setUser, logout: storeLogout } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function login(credentials: LoginCredentials) {
    setIsLoading(true);
    setError(null);
    try {
      const { user } = await authLogin(credentials);
      setUser(user);
      router.push('/dashboard');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError?.response?.data?.detail || 'Credenciais inválidas. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  }

  async function logout() {
    await authLogout();
    storeLogout();
    router.push('/login');
  }

  return { user, isAuthenticated, isLoading, error, login, logout };
}
