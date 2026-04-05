import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import OfflineBanner from './OfflineBanner';
import ToastContainer from './ToastContainer';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const pageTitles: Record<string, string> = {
    '/dashboard': t('nav.dashboard'),
    '/orders': t('nav.orders'),
    '/map': t('nav.map'),
    '/admin': t('nav.admin'),
    '/settings': t('nav.settings'),
  };

  const title = pageTitles[location.pathname] || 'StrongLogistics';

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:rounded focus:shadow"
      >
        Skip to main content
      </a>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <OfflineBanner />
        <TopBar title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main id="main-content" className="flex-1 overflow-y-auto p-4 sm:p-6">
          {children}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
}
