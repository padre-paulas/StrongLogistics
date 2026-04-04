import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchOrders } from '../api/orders';
import { autoAssignOrders } from '../api/orders';
import PriorityBadge from '../components/PriorityBadge';
import StatusBadge from '../components/StatusBadge';
import LoadingSkeleton from '../components/LoadingSkeleton';
import RoleGuard from '../components/RoleGuard';
import OrderDetailDrawer from '../features/OrderDetailDrawer';
import AutoAssignModal from '../features/AutoAssignModal';
import CreateOrderModal from '../features/CreateOrderModal';
import type { Order, Priority, OrderStatus } from '../types';
import { format } from 'date-fns';
import { useToast } from '../context/ToastContext';

type SortKey = 'order_id' | 'priority' | 'status' | 'created_at';
type SortDir = 'asc' | 'desc';

function SortIcon({ col, sortKey, sortDir }: { col: SortKey; sortKey: SortKey; sortDir: SortDir }) {
  if (sortKey !== col) return <> ↕</>;
  return <>{sortDir === 'asc' ? ' ↑' : ' ↓'}</>;
}

export default function OrdersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('created_at');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showAutoAssign, setShowAutoAssign] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const { addToast } = useToast();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['orders', page, statusFilter, priorityFilter],
    queryFn: () => fetchOrders({
      page,
      ...(statusFilter && { status: statusFilter }),
      ...(priorityFilter && { priority: priorityFilter }),
    }),
  });

  const filteredOrders = useMemo(() => {
    let orders = data?.results ?? [];
    if (search) {
      const q = search.toLowerCase();
      orders = orders.filter(
        (o) => o.order_id.toLowerCase().includes(q) || o.delivery_point?.name?.toLowerCase().includes(q)
      );
    }
    if (dateFrom) orders = orders.filter((o) => new Date(o.created_at) >= new Date(dateFrom));
    if (dateTo) orders = orders.filter((o) => new Date(o.created_at) <= new Date(dateTo));
    return [...orders].sort((a, b) => {
      const aVal: string = String(a[sortKey as keyof Order] ?? '');
      const bVal: string = String(b[sortKey as keyof Order] ?? '');
      return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
  }, [data?.results, search, dateFrom, dateTo, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const handleAutoAssign = async () => {
    try {
      await autoAssignOrders();
      setShowAutoAssign(true);
    } catch {
      addToast('Failed to start auto-assign', 'error');
    }
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">Failed to load orders</p>
        <button onClick={() => refetch()} className="bg-blue-600 text-white px-4 py-2 rounded-lg">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <div className="flex gap-3">
          <RoleGuard allowedRoles={['admin', 'dispatcher']}>
            <button onClick={handleAutoAssign} className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
              🤖 Auto-assign
            </button>
          </RoleGuard>
          <button onClick={() => setShowCreate(true)} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
            + Create Order
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search by order ID or destination..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm flex-1 min-w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          {(['pending','dispatched','in_transit','delivered','cancelled'] as OrderStatus[]).map((s) => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Priorities</option>
          {(['normal','elevated','critical'] as Priority[]).map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-6"><LoadingSkeleton lines={6} /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left cursor-pointer" onClick={() => toggleSort('order_id')}>
                    Order ID<SortIcon col="order_id" sortKey={sortKey} sortDir={sortDir} />
                  </th>
                  <th className="px-4 py-3 text-left">Destination</th>
                  <th className="px-4 py-3 text-left">Resource</th>
                  <th className="px-4 py-3 text-left">Qty</th>
                  <th className="px-4 py-3 text-left cursor-pointer" onClick={() => toggleSort('priority')}>
                    Priority<SortIcon col="priority" sortKey={sortKey} sortDir={sortDir} />
                  </th>
                  <th className="px-4 py-3 text-left cursor-pointer" onClick={() => toggleSort('status')}>
                    Status<SortIcon col="status" sortKey={sortKey} sortDir={sortDir} />
                  </th>
                  <th className="px-4 py-3 text-left">Driver</th>
                  <th className="px-4 py-3 text-left cursor-pointer" onClick={() => toggleSort('created_at')}>
                    Created<SortIcon col="created_at" sortKey={sortKey} sortDir={sortDir} />
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredOrders.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-gray-500">No orders found</td>
                  </tr>
                ) : (
                  filteredOrders.map((order) => (
                    <tr
                      key={order.id}
                      onClick={() => setSelectedOrder(order)}
                      className="hover:bg-gray-50 cursor-pointer"
                    >
                      <td className="px-4 py-3 font-mono text-xs text-blue-600">#{order.order_id}</td>
                      <td className="px-4 py-3 text-gray-800">{order.delivery_point?.name}</td>
                      <td className="px-4 py-3 text-gray-600">{order.resource?.name}</td>
                      <td className="px-4 py-3 text-gray-600">{order.quantity} {order.resource?.unit}</td>
                      <td className="px-4 py-3"><PriorityBadge priority={order.priority} /></td>
                      <td className="px-4 py-3"><StatusBadge status={order.status} /></td>
                      <td className="px-4 py-3 text-gray-600">{order.driver?.full_name ?? '—'}</td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{format(new Date(order.created_at), 'MMM d, HH:mm')}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
        {/* Pagination */}
        {data && data.count > 20 && (
          <div className="px-4 py-3 border-t flex items-center justify-between text-sm text-gray-600">
            <span>Showing page {page} of {Math.ceil(data.count / 20)}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={!data.previous}
                className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!data.next}
                className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {selectedOrder && (
        <OrderDetailDrawer
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}
      {showAutoAssign && <AutoAssignModal isOpen={showAutoAssign} onClose={() => setShowAutoAssign(false)} />}
      {showCreate && <CreateOrderModal isOpen={showCreate} onClose={() => setShowCreate(false)} />}
    </div>
  );
}
