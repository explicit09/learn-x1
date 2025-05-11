'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import type { ReactElement } from 'react';

type User = {
  id: string;
  name: string;
  email: string;
  role: string;
  organization_id: string;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: any) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Mock user for development
  const mockUser: User = {
    id: '1',
    name: 'Test User',
    email: 'test@example.com',
    role: 'admin',
    organization_id: '1'
  };

  const [user, setUser] = useState<User | null>(mockUser);
  const [isLoading, setIsLoading] = useState(false);

  const login = async (email: string, password: string) => {
    // Mock login for development
    console.log('Mock login:', { email, password });
    setUser(mockUser);
  };

  const logout = async () => {
    // Mock logout for development
    console.log('Mock logout');
    return Promise.resolve();
  };

  const register = async (userData: any) => {
    // Mock register for development
    console.log('Mock register:', userData);
    setUser(mockUser);
  };

  const contextValue: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
