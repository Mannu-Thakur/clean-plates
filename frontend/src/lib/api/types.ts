export type Dict<T = unknown> = Record<string, T>;

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  last_login?: string | null;
}

export interface LoginResponse {
  tokens: TokenPair;
  user: User;
}

export interface StoredSession {
  tokens: TokenPair;
  user: User;
  remember: boolean;
  savedAt: number;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface KpiOverview {
  total_waste_today_grams: number;
  total_waste_week_grams: number;
  total_waste_month_grams: number;
  avg_daily_waste_grams: number;
  waste_reduction_pct: number | null;
  peak_waste_time: string | null;
  total_active_students: number;
  students_under_warning: number;
  students_under_penalty: number;
  active_devices: number;
  offline_devices: number;
  alerts_today: number;
  rule_violations_today: number;
}

export interface Student {
  id: string;
  device_id: string;
  status: string;
  sustainability_score: number;
  warning_count: number;
  penalty_count: number;
  avg_waste_grams: number;
  is_active: boolean;
  mapping?: {
    name: string;
    roll_number: string;
    branch: string;
    year: number;
    hostel?: string | null;
    room_number?: string | null;
    email?: string | null;
  } | null;
  created_at: string;
  total_waste_grams?: number;
}

export interface WasteEntry {
  id: string;
  student_id: string;
  device_id: string;
  weight_grams: number;
  meal_type: string;
  food_items: Array<{ name: string; grams?: number | null }>;
  severity: string;
  timestamp: string;
  student_name?: string | null;
  student_device_id: string;
  plate_image_path?: string | null;
}

export interface Device {
  id: string;
  device_serial?: string;
  edge_node_name: string;
  institution_name?: string;
  mess_name: string;
  hostel_name?: string | null;
  status: string;
  ip_address?: string | null;
  firmware_version?: string | null;
  last_heartbeat?: string | null;
  last_sync?: string | null;
  active_since?: string | null;
  cpu_percent?: number | null;
  ram_percent?: number | null;
  temperature?: number | null;
}

export interface NotificationItem {
  id: string;
  type: string;
  channel: string;
  subject: string;
  body?: string;
  status: string;
  recipient_type: string;
  is_read: boolean;
  scheduled_at?: string | null;
  sent_at?: string | null;
  created_at: string;
}

export interface ReportItem {
  id: string;
  type: string;
  format: string;
  status: string;
  file_size?: number | null;
  generated_at?: string | null;
  created_at: string;
}

export interface RuleItem {
  id: string;
  name: string;
  description?: string | null;
  type: string;
  priority: string;
  active: boolean;
  conditions: unknown[];
  actions: unknown[];
  execution_count: number;
  last_triggered_at?: string | null;
  created_at: string;
  updated_at: string;
}
