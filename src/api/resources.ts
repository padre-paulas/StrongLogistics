import { mockFetchResources } from './mockDb';
import type { Resource } from '../types';

export async function fetchResources(): Promise<Resource[]> {
  return mockFetchResources();
}
