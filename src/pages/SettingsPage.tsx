import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { usePreferences } from '../context/PreferencesContext';
import { useToast } from '../context/ToastContext';
import type { AppTheme, AppLanguage, NotificationPreferences } from '../context/PreferencesContext';

type Tab = 'appearance' | 'language' | 'notifications';

export default function SettingsPage() {
  const { t } = useTranslation();
  const { theme, language, notifications, setTheme, setLanguage, setNotifications } = usePreferences();
  const { addToast } = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('appearance');

  // Local copies for the notifications form
  const [localNotifs, setLocalNotifs] = useState<NotificationPreferences>({ ...notifications });

  const handleSaveNotifications = () => {
    setNotifications(localNotifs);
    addToast(t('settings.saved'), 'success');
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: 'appearance', label: t('settings.tabs.appearance') },
    { id: 'language', label: t('settings.tabs.language') },
    { id: 'notifications', label: t('settings.tabs.notifications') },
  ];

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        {t('settings.title')}
      </h1>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab.id
                ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Appearance tab */}
      {activeTab === 'appearance' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-6">
          <div>
            <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100 mb-1">
              {t('settings.appearance.heading')}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('settings.appearance.darkModeDesc')}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ThemeButton
              value="light"
              current={theme}
              label={t('settings.appearance.light')}
              icon="☀️"
              onClick={(v) => { setTheme(v as AppTheme); addToast(t('settings.saved'), 'success'); }}
            />
            <ThemeButton
              value="dark"
              current={theme}
              label={t('settings.appearance.dark')}
              icon="🌙"
              onClick={(v) => { setTheme(v as AppTheme); addToast(t('settings.saved'), 'success'); }}
            />
          </div>
        </div>
      )}

      {/* Language tab */}
      {activeTab === 'language' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-6">
          <div>
            <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100 mb-1">
              {t('settings.language.heading')}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('settings.language.desc')}
            </p>
          </div>
          <div className="flex flex-col gap-3">
            {(['en', 'pt'] as AppLanguage[]).map((lang) => (
              <button
                key={lang}
                onClick={() => { setLanguage(lang); addToast(t('settings.saved'), 'success'); }}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg border text-sm font-medium transition-colors text-left ${
                  language === lang
                    ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-400'
                    : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-300 dark:hover:border-blue-500 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                <span className="text-lg">{lang === 'en' ? '🇬🇧' : '🇧🇷'}</span>
                <span>{t(`settings.language.${lang}`)}</span>
                {language === lang && (
                  <span className="ml-auto text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">
                    ✓
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Notifications tab */}
      {activeTab === 'notifications' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-6">
          <div>
            <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100 mb-1">
              {t('settings.notifications.heading')}
            </h2>
          </div>
          <div className="space-y-4">
            <ToggleRow
              label={t('settings.notifications.criticalAlerts')}
              desc={t('settings.notifications.criticalAlertsDesc')}
              value={localNotifs.criticalAlerts}
              onChange={(v) => setLocalNotifs((p) => ({ ...p, criticalAlerts: v }))}
            />
            <ToggleRow
              label={t('settings.notifications.statusUpdates')}
              desc={t('settings.notifications.statusUpdatesDesc')}
              value={localNotifs.statusUpdates}
              onChange={(v) => setLocalNotifs((p) => ({ ...p, statusUpdates: v }))}
            />
            <ToggleRow
              label={t('settings.notifications.driverUpdates')}
              desc={t('settings.notifications.driverUpdatesDesc')}
              value={localNotifs.driverUpdates}
              onChange={(v) => setLocalNotifs((p) => ({ ...p, driverUpdates: v }))}
            />
          </div>
          <button
            onClick={handleSaveNotifications}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg text-sm font-medium"
          >
            {t('settings.saved')}
          </button>
        </div>
      )}
    </div>
  );
}

function ThemeButton({
  value,
  current,
  label,
  icon,
  onClick,
}: {
  value: string;
  current: string;
  label: string;
  icon: string;
  onClick: (v: string) => void;
}) {
  return (
    <button
      onClick={() => onClick(value)}
      className={`flex-1 flex flex-col items-center gap-2 py-4 rounded-xl border-2 text-sm font-medium transition-colors ${
        current === value
          ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
          : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-blue-300 dark:hover:border-blue-500 hover:bg-gray-50 dark:hover:bg-gray-700'
      }`}
    >
      <span className="text-2xl">{icon}</span>
      {label}
    </button>
  );
}

function ToggleRow({
  label,
  desc,
  value,
  onChange,
}: {
  label: string;
  desc: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-3 border-b border-gray-100 dark:border-gray-700 last:border-0">
      <div>
        <p className="text-sm font-medium text-gray-800 dark:text-gray-100">{label}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{desc}</p>
      </div>
      <button
        role="switch"
        aria-checked={value}
        onClick={() => onChange(!value)}
        className={`relative shrink-0 w-11 h-6 rounded-full transition-colors ${
          value ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
            value ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}
