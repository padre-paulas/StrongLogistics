import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import i18n from '../i18n';

export type AppLanguage = 'en' | 'pt';
export type AppTheme = 'light' | 'dark';

export interface NotificationPreferences {
  criticalAlerts: boolean;
  statusUpdates: boolean;
  driverUpdates: boolean;
}

interface PreferencesContextType {
  theme: AppTheme;
  language: AppLanguage;
  notifications: NotificationPreferences;
  setTheme: (theme: AppTheme) => void;
  setLanguage: (lang: AppLanguage) => void;
  setNotifications: (prefs: NotificationPreferences) => void;
}

const defaultNotifications: NotificationPreferences = {
  criticalAlerts: true,
  statusUpdates: true,
  driverUpdates: false,
};

const PreferencesContext = createContext<PreferencesContextType | null>(null);

function loadTheme(): AppTheme {
  const stored = localStorage.getItem('theme');
  if (stored === 'dark' || stored === 'light') return stored;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function loadLanguage(): AppLanguage {
  const stored = localStorage.getItem('lang');
  if (stored === 'en' || stored === 'pt') return stored;
  return 'en';
}

function loadNotifications(): NotificationPreferences {
  const stored = localStorage.getItem('notificationPrefs');
  if (stored) {
    try {
      return { ...defaultNotifications, ...JSON.parse(stored) };
    } catch {
      // ignore
    }
  }
  return defaultNotifications;
}

export function PreferencesProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<AppTheme>(loadTheme);
  const [language, setLanguageState] = useState<AppLanguage>(loadLanguage);
  const [notifications, setNotificationsState] = useState<NotificationPreferences>(loadNotifications);

  // Apply dark mode class to document root
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const setTheme = useCallback((t: AppTheme) => setThemeState(t), []);

  const setLanguage = useCallback((lang: AppLanguage) => {
    setLanguageState(lang);
    localStorage.setItem('lang', lang);
    i18n.changeLanguage(lang);
  }, []);

  const setNotifications = useCallback((prefs: NotificationPreferences) => {
    setNotificationsState(prefs);
    localStorage.setItem('notificationPrefs', JSON.stringify(prefs));
  }, []);

  return (
    <PreferencesContext.Provider value={{ theme, language, notifications, setTheme, setLanguage, setNotifications }}>
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  const ctx = useContext(PreferencesContext);
  if (!ctx) throw new Error('usePreferences must be used within PreferencesProvider');
  return ctx;
}
