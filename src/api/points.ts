import {
  mockFetchPoints,
  mockFetchPointOrders,
  mockFetchNearbyPoints,
} from './mockDb';
import type { DeliveryPoint, Order, NearbyPoint } from '../types';

export async function fetchPoints(): Promise<DeliveryPoint[]> {
  return mockFetchPoints();
}

export async function fetchPointOrders(pointId: number): Promise<Order[]> {
  return mockFetchPointOrders(pointId);
}

export async function fetchNearbyPoints(pointId: number, resourceId: number, _radiusKm = 50): Promise<NearbyPoint[]> {
  return mockFetchNearbyPoints(pointId, resourceId);
}
