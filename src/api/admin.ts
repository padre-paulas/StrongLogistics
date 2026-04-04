import {
  mockFetchUsers,
  mockDeactivateUser,
  mockFetchResources,
  mockAdminDeleteResource,
  mockFetchPoints,
  mockAdminDeletePoint,
} from './mockDb';
import type { User, Resource, DeliveryPoint } from '../types';

export async function fetchUsers(): Promise<User[]> {
  return mockFetchUsers();
}

export async function createUser(_payload: Partial<User> & { password?: string }): Promise<User> {
  throw new Error('Not implemented in mock');
}

export async function updateUser(_id: number, _payload: Partial<User>): Promise<User> {
  throw new Error('Not implemented in mock');
}

export async function deactivateUser(id: number): Promise<void> {
  return mockDeactivateUser(id);
}

export async function adminFetchResources(): Promise<Resource[]> {
  return mockFetchResources();
}

export async function adminCreateResource(_payload: Partial<Resource>): Promise<Resource> {
  throw new Error('Not implemented in mock');
}

export async function adminDeleteResource(id: number): Promise<void> {
  return mockAdminDeleteResource(id);
}

export async function adminFetchPoints(): Promise<DeliveryPoint[]> {
  return mockFetchPoints();
}

export async function adminCreatePoint(_payload: Partial<DeliveryPoint>): Promise<DeliveryPoint> {
  throw new Error('Not implemented in mock');
}

export async function adminUpdatePoint(_id: number, _payload: Partial<DeliveryPoint>): Promise<DeliveryPoint> {
  throw new Error('Not implemented in mock');
}

export async function adminDeletePoint(id: number): Promise<void> {
  return mockAdminDeletePoint(id);
}
