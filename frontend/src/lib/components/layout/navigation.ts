import {
  Activity,
  BarChart3,
  Bell,
  ClipboardList,
  Cpu,
  FileText,
  Gauge,
  Home,
  ScrollText,
  Settings,
  ShieldAlert,
  SlidersHorizontal,
  Users
} from '@lucide/svelte';

export const navItems = [
  {
    href: '/dashboard',
    label: 'Overview',
    icon: Home,
    roles: [
      'super_admin',
      'institution_admin',
      'mess_admin',
      'analytics_viewer'
    ]
  },
  {
    href: '/dashboard/monitoring',
    label: 'Monitoring',
    icon: Activity,
    roles: [
      'super_admin',
      'institution_admin',
      'mess_admin',
      'analytics_viewer',
      'staff_operator'
    ]
  },
  {
    href: '/dashboard/analytics',
    label: 'Analytics',
    icon: BarChart3,
    roles: [
      'super_admin',
      'institution_admin',
      'mess_admin',
      'analytics_viewer'
    ]
  },
  {
    href: '/dashboard/students',
    label: 'Students',
    icon: Users,
    roles: [
      'super_admin',
      'institution_admin',
      'mess_admin',
      'analytics_viewer'
    ]
  },
  {
    href: '/dashboard/warnings',
    label: 'Warnings',
    icon: ShieldAlert,
    roles: ['super_admin', 'institution_admin', 'mess_admin']
  },
  {
    href: '/dashboard/rules',
    label: 'Rules',
    icon: Gauge,
    roles: ['super_admin', 'institution_admin']
  },
  {
    href: '/dashboard/notifications',
    label: 'Notifications',
    icon: Bell,
    roles: ['super_admin', 'institution_admin', 'mess_admin']
  },
  {
    href: '/dashboard/reports',
    label: 'Reports',
    icon: FileText,
    roles: [
      'super_admin',
      'institution_admin',
      'mess_admin',
      'analytics_viewer'
    ]
  },
  {
    href: '/dashboard/devices',
    label: 'Devices',
    icon: Cpu,
    roles: ['super_admin', 'institution_admin', 'mess_admin']
  },
  {
    href: '/dashboard/config',
    label: 'Config',
    icon: SlidersHorizontal,
    roles: ['super_admin', 'institution_admin', 'mess_admin']
  },
  {
    href: '/dashboard/settings',
    label: 'Settings',
    icon: Settings,
    roles: ['super_admin', 'institution_admin']
  },
  {
    href: '/dashboard/audit',
    label: 'Audit',
    icon: ScrollText,
    roles: ['super_admin', 'institution_admin']
  }
];

export const quickActions = [
  { href: '/dashboard/reports', label: 'Reports', icon: ClipboardList },
  { href: '/dashboard/monitoring', label: 'Live', icon: Activity }
];
