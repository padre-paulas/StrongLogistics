import { mockFetchDashboardStats } from './mockDb';
import type { DashboardStats } from '../types';

export async function fetchDashboardStats(): Promise<DashboardStats> {
  return mockFetchDashboardStats();
}
