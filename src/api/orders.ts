import apiClient from './client';
import type { Order, PaginatedResponse, AutoAssignPlan } from '../types';

export async function fetchOrders(params?: Record<string, string | number>): Promise<PaginatedResponse<Order>> {
  const { data } = await apiClient.get<PaginatedResponse<Order>>('/api/orders/', { params });
  return data;
}

export async function fetchOrder(id: number): Promise<Order> {
  const { data } = await apiClient.get<Order>(`/api/orders/${id}/`);
  return data;
}

export async function updateOrderStatus(id: number, status: string): Promise<Order> {
  const { data } = await apiClient.patch<Order>(`/api/orders/${id}/`, { status });
  return data;
}

export async function createOrder(payload: {
  delivery_point: number;
  resource: number;
  quantity: number;
  priority: string;
  notes?: string;
}): Promise<Order> {
  const { data } = await apiClient.post<Order>('/api/orders/', payload);
  return data;
}

export async function autoAssignOrders(): Promise<AutoAssignPlan> {
  const { data } = await apiClient.post<AutoAssignPlan>('/api/orders/auto-assign/');
  return data;
}

export async function confirmAutoAssign(planId: string): Promise<void> {
  await apiClient.post('/api/orders/auto-assign/confirm/', { plan_id: planId });
}
