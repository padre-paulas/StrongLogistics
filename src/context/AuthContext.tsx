import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, Role } from '../types';

interface AuthContextType {
  user: User | null;
  role: Role | null;
  login: (email: string, role: Role) => Promise<void>;
  signup: (email: string, fullName: string, role: Role) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

let mockIdCounter = 1;

function createMockUser(email: string, fullName: string, role: Role): User {
  return { id: mockIdCounter++, email, full_name: fullName, role, is_active: true };
}

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

  const login = useCallback(async (email: string, role: Role) => {
    const mockUser = createMockUser(email, email.split('@')[0], role);
    localStorage.setItem('user', JSON.stringify(mockUser));
    setUser(mockUser);
  }, []);

  const signup = useCallback(async (email: string, fullName: string, role: Role) => {
    const mockUser = createMockUser(email, fullName, role);
    localStorage.setItem('user', JSON.stringify(mockUser));
    setUser(mockUser);
  }, []);

  const logout = useCallback(() => {
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
