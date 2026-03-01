import { 
  LayoutDashboard, 
  Terminal, 
  Database, 
  History, 
  Bell, 
  FileText, 
  BarChart3, 
  Layers, 
  Settings,
  Zap,
  Shield,
  Moon,
  Cpu
} from 'lucide-react';
import { NavItem, Mode } from './types';

export const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
  { id: 'console', label: 'Console', icon: 'Terminal' },
  { id: 'memory', label: 'Memory', icon: 'Database' },
  { id: 'timeline', label: 'Timeline', icon: 'History' },
  { id: 'reminders', label: 'Reminders', icon: 'Bell' },
  { id: 'notes', label: 'Notes', icon: 'FileText' },
  { id: 'telemetry', label: 'Telemetry', icon: 'BarChart3' },
  { id: 'modes', label: 'Modes', icon: 'Layers' },
  { id: 'settings', label: 'Settings', icon: 'Settings' },
];

export const INITIAL_MODES: Mode[] = [
  { 
    id: 'deep-work', 
    name: 'Deep Work', 
    description: 'Focus mode with restricted notifications and high cognitive priority.', 
    icon: 'Zap', 
    active: true,
    color: '#34C759'
  },
  { 
    id: 'privacy-plus', 
    name: 'Privacy+', 
    description: 'Enhanced data isolation and local-only processing where possible.', 
    icon: 'Shield', 
    active: false,
    color: '#0A84FF'
  },
  { 
    id: 'low-power', 
    name: 'Eco Mode', 
    description: 'Reduced token usage and lower frequency telemetry.', 
    icon: 'Moon', 
    active: false,
    color: '#FF9F0A'
  },
  { 
    id: 'research', 
    name: 'Research', 
    description: 'Expanded context window and web-grounding enabled.', 
    icon: 'Cpu', 
    active: false,
    color: '#AF52DE'
  }
];

export const ICON_MAP: Record<string, any> = {
  LayoutDashboard,
  Terminal,
  Database,
  History,
  Bell,
  FileText,
  BarChart3,
  Layers,
  Settings,
  Zap,
  Shield,
  Moon,
  Cpu
};
