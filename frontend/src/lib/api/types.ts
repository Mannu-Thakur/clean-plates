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

export interface MealSession {
  meal_type: 'breakfast' | 'lunch' | 'dinner' | string | null;
  start_time: string;
  end_time: string;
  entry_count: number;
  is_active: boolean;
  session_name?: string;
  entry_count_today?: number;
  total_waste_today_grams?: number;
}

export interface LiveWasteEntry {
  id: string;
  student_name?: string | null;
  student_roll_number?: string | null;
  student_device_id?: string | null;
  student_id?: string | null;
  device_id: string;
  weight_grams: number;
  meal_type: string;
  food_items: Array<string | { name: string; grams?: number | null }>;
  severity: 'low' | 'medium' | 'high' | string;
  plate_image_path?: string | null;
  timestamp: string;
}

export interface DeviceStatus {
  id: string;
  name?: string;
  edge_node_name?: string;
  mess_name?: string | null;
  status: 'online' | 'offline' | 'warning' | 'decommissioned' | string;
  cpu_percent?: number | null;
  ram_percent?: number | null;
  temperature?: number | null;
  last_heartbeat?: string | null;
  ip_address?: string | null;
  firmware_version?: string | null;
  uptime_seconds?: number | null;
}

export interface MonitoringAlert {
  id?: string;
  notification_id?: string;
  subject?: string;
  message?: string;
  reason?: string;
  rule_name?: string;
  priority?: string;
  type?: string;
  alert_type?: string;
  timestamp?: string;
  acknowledged?: boolean;
}

export interface DeviceHealthSnapshot {
  recorded_at: string;
  cpu_percent: number;
  ram_percent: number;
  disk_percent?: number | null;
  storage_percent?: number | null;
  temperature?: number | null;
  connectivity?: boolean;
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

export interface NotificationStats {
  unread: number;
  sent_today: number;
  failed: number;
  pending: number;
}

export interface NotificationDeliveryItem {
  recipient_id: string;
  recipient_email?: string | null;
  channel: string;
  status: string;
  delivered_at?: string | null;
  error?: string | null;
}

export interface NotificationDelivery {
  notification_id: string;
  total_recipients: number;
  delivered: number;
  failed: number;
  pending: number;
  deliveries: NotificationDeliveryItem[];
}

export interface NotificationPreference {
  type: string;
  dashboard: boolean;
  email: boolean;
}

export interface ReportItem {
  id: string;
  type: string;
  format: string;
  status: string;
  file_size?: number | null;
  generated_by?: string;
  generated_at?: string | null;
  created_at: string;
}

export interface ReportSchedule {
  id: string;
  report_type: string;
  format: string;
  frequency: string;
  day_of_week?: string | null;
  time_of_day: string;
  email_recipients: string[];
  auto_email: boolean;
  active: boolean;
  last_run?: string | null;
  next_run?: string | null;
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
