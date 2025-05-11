'use client';

import { LayoutProvider } from '@/providers/layout-provider';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <LayoutProvider>{children}</LayoutProvider>;
}
