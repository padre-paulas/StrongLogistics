import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import OfflineBanner from './OfflineBanner';
import ToastContainer from './ToastContainer';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/orders': 'Orders',
  '/map': 'Map',
  '/admin': 'Admin Panel',
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const title = pageTitles[location.pathname] || 'LogiFlow';
  const [_sidebarOpen, _setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <OfflineBanner />
        <TopBar title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
}
