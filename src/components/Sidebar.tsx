import { NavLink } from 'react-router-dom';
import RoleGuard from './RoleGuard';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/orders', label: 'Orders', icon: '📦' },
  { to: '/map', label: 'Map', icon: '🗺️' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col min-h-screen shrink-0">
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white">🚚 StrongLogistics</h1>
        <p className="text-gray-400 text-xs mt-1">Logistics Dashboard</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'
              }`
            }
          >
            <span>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
        <RoleGuard allowedRoles={['admin']}>
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'
              }`
            }
          >
            <span>⚙️</span>
            Admin
          </NavLink>
        </RoleGuard>
      </nav>
    </aside>
  );
}
