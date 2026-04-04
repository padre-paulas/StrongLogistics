import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchUsers, deactivateUser, adminFetchResources, adminDeleteResource, adminFetchPoints, adminDeletePoint } from '../api/admin';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { useToast } from '../context/ToastContext';

type Tab = 'users' | 'resources' | 'points';

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('users');
  const qc = useQueryClient();
  const { addToast } = useToast();

  const { data: users, isLoading: loadingUsers } = useQuery({ queryKey: ['admin-users'], queryFn: fetchUsers });
  const { data: resources, isLoading: loadingResources } = useQuery({ queryKey: ['admin-resources'], queryFn: adminFetchResources });
  const { data: points, isLoading: loadingPoints } = useQuery({ queryKey: ['admin-points'], queryFn: adminFetchPoints });

  const deactivateMutation = useMutation({
    mutationFn: deactivateUser,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-users'] }); addToast('User deactivated', 'success'); },
    onError: () => addToast('Failed to deactivate user', 'error'),
  });

  const deleteResourceMutation = useMutation({
    mutationFn: adminDeleteResource,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-resources'] }); addToast('Resource deleted', 'success'); },
    onError: () => addToast('Failed to delete resource', 'error'),
  });

  const deletePointMutation = useMutation({
    mutationFn: adminDeletePoint,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-points'] }); addToast('Point deleted', 'success'); },
    onError: () => addToast('Failed to delete point', 'error'),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
      <div className="flex gap-2 border-b">
        {(['users', 'resources', 'points'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
              tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'users' && (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {loadingUsers ? <div className="p-6"><LoadingSkeleton lines={4} /></div> : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-left">Email</th>
                  <th className="px-4 py-3 text-left">Role</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {users?.length === 0 && <tr><td colSpan={5} className="text-center py-8 text-gray-500">No users</td></tr>}
                {users?.map((u) => (
                  <tr key={u.id}>
                    <td className="px-4 py-3 font-medium">{u.full_name}</td>
                    <td className="px-4 py-3 text-gray-600">{u.email}</td>
                    <td className="px-4 py-3"><span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">{u.role}</span></td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {u.is_active && (
                        <button
                          onClick={() => deactivateMutation.mutate(u.id)}
                          className="text-red-500 hover:text-red-700 text-xs"
                        >
                          Deactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'resources' && (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {loadingResources ? <div className="p-6"><LoadingSkeleton lines={4} /></div> : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-left">Unit</th>
                  <th className="px-4 py-3 text-left">Description</th>
                  <th className="px-4 py-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {resources?.length === 0 && <tr><td colSpan={4} className="text-center py-8 text-gray-500">No resources</td></tr>}
                {resources?.map((r) => (
                  <tr key={r.id}>
                    <td className="px-4 py-3 font-medium">{r.name}</td>
                    <td className="px-4 py-3 text-gray-600">{r.unit}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{r.description ?? '—'}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => deleteResourceMutation.mutate(r.id)}
                        className="text-red-500 hover:text-red-700 text-xs"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'points' && (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {loadingPoints ? <div className="p-6"><LoadingSkeleton lines={4} /></div> : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-left">Address</th>
                  <th className="px-4 py-3 text-left">Coordinates</th>
                  <th className="px-4 py-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {points?.length === 0 && <tr><td colSpan={4} className="text-center py-8 text-gray-500">No delivery points</td></tr>}
                {points?.map((p) => (
                  <tr key={p.id}>
                    <td className="px-4 py-3 font-medium">{p.name}</td>
                    <td className="px-4 py-3 text-gray-600">{p.address}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs font-mono">{p.latitude}, {p.longitude}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => deletePointMutation.mutate(p.id)}
                        className="text-red-500 hover:text-red-700 text-xs"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
