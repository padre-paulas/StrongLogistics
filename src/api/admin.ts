import apiClient from './client';
import type { User, Resource, DeliveryPoint } from '../types';

export async function fetchUsers(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/api/admin/users/');
  return data;
}

export async function createUser(payload: Partial<User> & { password?: string }): Promise<User> {
  const { data } = await apiClient.post<User>('/api/admin/users/', payload);
  return data;
}

export async function updateUser(id: number, payload: Partial<User>): Promise<User> {
  const { data } = await apiClient.patch<User>(`/api/admin/users/${id}/`, payload);
  return data;
}

export async function deactivateUser(id: number): Promise<void> {
  await apiClient.patch(`/api/admin/users/${id}/`, { is_active: false });
}

export async function adminFetchResources(): Promise<Resource[]> {
  const { data } = await apiClient.get<Resource[]>('/api/resources/');
  return data;
}

export async function adminCreateResource(payload: Partial<Resource>): Promise<Resource> {
  const { data } = await apiClient.post<Resource>('/api/resources/', payload);
  return data;
}

export async function adminDeleteResource(id: number): Promise<void> {
  await apiClient.delete(`/api/resources/${id}/`);
}

export async function adminFetchPoints(): Promise<DeliveryPoint[]> {
  const { data } = await apiClient.get<DeliveryPoint[]>('/api/points/');
  return data;
}

export async function adminCreatePoint(payload: Partial<DeliveryPoint>): Promise<DeliveryPoint> {
  const { data } = await apiClient.post<DeliveryPoint>('/api/points/', payload);
  return data;
}

export async function adminUpdatePoint(id: number, payload: Partial<DeliveryPoint>): Promise<DeliveryPoint> {
  const { data } = await apiClient.patch<DeliveryPoint>(`/api/points/${id}/`, payload);
  return data;
}

export async function adminDeletePoint(id: number): Promise<void> {
  await apiClient.delete(`/api/points/${id}/`);
}
