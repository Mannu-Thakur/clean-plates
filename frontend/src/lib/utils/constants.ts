export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  INSTITUTION_ADMIN: 'institution_admin',
  MESS_ADMIN: 'mess_admin',
  ANALYTICS_VIEWER: 'analytics_viewer',
  STAFF_OPERATOR: 'staff_operator'
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];

export const MEAL_TYPES = ['breakfast', 'lunch', 'dinner'] as const;
export type MealType = (typeof MEAL_TYPES)[number];

export const WARNING_LEVELS = ['yellow', 'orange', 'red'] as const;
export type WarningLevel = (typeof WARNING_LEVELS)[number];

export const STUDENT_STATUSES = ['green', 'yellow', 'orange', 'red'] as const;
export type StudentStatus = (typeof STUDENT_STATUSES)[number];

export const PENALTY_TYPES = [
  'points',
  'monetary',
  'restriction',
  'suspension'
] as const;
export type PenaltyType = (typeof PENALTY_TYPES)[number];

export const REPORT_TYPES = [
  'overview',
  'students',
  'warnings',
  'devices',
  'analytics'
] as const;
export type ReportType = (typeof REPORT_TYPES)[number];

export const REPORT_FORMATS = ['pdf', 'xlsx', 'csv'] as const;
export type ReportFormat = (typeof REPORT_FORMATS)[number];

export const PAGE_SIZES = [25, 50, 100] as const;
export const DEFAULT_PAGE_SIZE = 25;

export const PERIOD_OPTIONS = [
  { value: 'today', label: 'Today' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
  { value: 'semester', label: 'This Semester' }
] as const;
