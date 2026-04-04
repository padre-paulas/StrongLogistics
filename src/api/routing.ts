import type { RouteBlockage } from '../types';
import {
  mockGetBlockedRoutes,
  mockBlockRoute,
  mockUnblockRoute,
  mockIsPointBlocked,
} from './mockDb';

export function getBlockedRoutes(): Promise<RouteBlockage[]> {
  return mockGetBlockedRoutes();
}

export function blockRoute(pointId: number, reason: string): Promise<RouteBlockage> {
  return mockBlockRoute(pointId, reason);
}

export function unblockRoute(id: string): Promise<void> {
  return mockUnblockRoute(id);
}

export function isPointBlocked(pointId: number): boolean {
  return mockIsPointBlocked(pointId);
}
