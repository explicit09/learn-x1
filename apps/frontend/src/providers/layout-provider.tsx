'use client';

import { ReactNode } from 'react';
import { AuthProvider } from '@/lib/hooks/useAuth';
import { AITutorProvider } from '@/lib/hooks/useAITutor';

export function LayoutProvider({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <AITutorProvider>
        {children}
      </AITutorProvider>
    </AuthProvider>
  );
}
