import api from './api';
import type { AuthTokens, LoginCredentials, User } from '@/types';

export async function login(credentials: LoginCredentials): Promise<{ tokens: AuthTokens; user: User }> {
  const { data: tokens } = await api.post<AuthTokens>('/auth/token/', credentials);
  localStorage.setItem('access_token', tokens.access);
  localStorage.setItem('refresh_token', tokens.refresh);

  const { data: user } = await api.get<User>('/auth/me/');
  return { tokens, user };
}

export async function logout(): Promise<void> {
  try {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      await api.post('/auth/token/blacklist/', { refresh });
    }
  } catch {
    // ignore errors on logout
  } finally {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export async function refreshToken(): Promise<string | null> {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) return null;

  try {
    const { data } = await api.post<{ access: string }>('/auth/token/refresh/', { refresh });
    localStorage.setItem('access_token', data.access);
    return data.access;
  } catch {
    localStorage.clear();
    return null;
  }
}
