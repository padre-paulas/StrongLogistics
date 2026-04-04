export type Role = 'admin' | 'dispatcher' | 'driver';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export type Priority = 'normal' | 'elevated' | 'critical';
export type OrderStatus = 'pending' | 'dispatched' | 'in_transit' | 'delivered' | 'cancelled';

export interface DeliveryPoint {
  id: number;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  stock: StockItem[];
}

export interface StockItem {
  resource_id: number;
  resource_name: string;
  quantity: number;
}

export interface Resource {
  id: number;
  name: string;
  unit: string;
  description?: string;
}

export interface Driver {
  id: number;
  full_name: string;
  email: string;
  is_available: boolean;
  vehicle_plate?: string;
}

export interface Order {
  id: number;
  order_id: string;
  delivery_point: DeliveryPoint;
  resource: Resource;
  quantity: number;
  priority: Priority;
  status: OrderStatus;
  driver?: Driver;
  notes?: string;
  created_at: string;
  updated_at: string;
  status_history: StatusHistoryEntry[];
}

export interface StatusHistoryEntry {
  status: OrderStatus;
  timestamp: string;
  changed_by: string;
  notes?: string;
}

export interface DashboardStats {
  total_active_orders: number;
  critical_priority: number;
  pending_dispatch: number;
  available_drivers: number;
  recent_orders: Order[];
}

export interface Notification {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AutoAssignPlan {
  plan_id: string;
  assignments: DriverAssignment[];
  total_distance_km: number;
  estimated_time_minutes: number;
}

export interface DriverAssignment {
  driver: Driver;
  orders: Order[];
  total_distance_km: number;
  estimated_time_minutes: number;
}

export interface RouteInfo {
  distance_km: number;
  estimated_time_minutes: number;
}

export interface NearbyPoint {
  point: DeliveryPoint;
  distance_km: number;
  available_quantity: number;
}
