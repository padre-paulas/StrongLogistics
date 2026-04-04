import {
  mockFetchOrders,
  mockFetchOrder,
  mockUpdateOrderStatus,
  mockCreateOrder,
  mockAutoAssignOrders,
  mockConfirmAutoAssign,
} from './mockDb';
import type { Order, PaginatedResponse, AutoAssignPlan } from '../types';

export async function fetchOrders(params?: Record<string, string | number>): Promise<PaginatedResponse<Order>> {
  return mockFetchOrders(params);
}

export async function fetchOrder(id: number): Promise<Order> {
  return mockFetchOrder(id);
}

export async function updateOrderStatus(id: number, status: string): Promise<Order> {
  return mockUpdateOrderStatus(id, status);
}

export async function createOrder(payload: {
  delivery_point: number;
  resource: number;
  quantity: number;
  priority: string;
  notes?: string;
}): Promise<Order> {
  return mockCreateOrder(payload);
}

export async function autoAssignOrders(): Promise<AutoAssignPlan> {
  return mockAutoAssignOrders();
}

export async function confirmAutoAssign(planId: string): Promise<void> {
  return mockConfirmAutoAssign(planId);
}
