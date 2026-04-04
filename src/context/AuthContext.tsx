import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, Role } from '../types';
import apiClient from '../api/client';

interface AuthContextType {
  user: User | null;
  role: Role | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string, role: Role) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        // ignore
      }
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await apiClient.post('/api/auth/login/', { email, password });
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
  }, []);

  const signup = useCallback(async (email: string, password: string, fullName: string, role: Role) => {
    const { data } = await apiClient.post('/api/auth/register/', { email, password, full_name: fullName, role });
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, role: user?.role ?? null, login, signup, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
