'use client';

import { useAuthStore } from '@/store/auth-store';
import { Notifications } from './notifications';

interface HeaderProps {
  title?: string;
}

export function Header({ title }: HeaderProps) {
  const { user } = useAuthStore();

  return (
    <header className="h-16 border-b bg-background flex items-center justify-between px-6">
      <div>
        {title && <h1 className="text-lg font-semibold">{title}</h1>}
      </div>
      <div className="flex items-center gap-3">
        <Notifications />
        <div className="text-sm text-right hidden sm:block">
          <p className="font-medium">{user?.first_name} {user?.last_name}</p>
          <p className="text-muted-foreground text-xs capitalize">
            {user?.role === 'rh' ? 'RH' : user?.role === 'lideranca' ? 'Liderança' : user?.role}
          </p>
        </div>
      </div>
    </header>
  );
}
