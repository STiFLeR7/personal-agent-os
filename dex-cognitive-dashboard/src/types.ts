import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type ViewType = 
  | 'dashboard' 
  | 'console' 
  | 'memory' 
  | 'timeline' 
  | 'reminders' 
  | 'notes' 
  | 'telemetry' 
  | 'modes' 
  | 'settings';

export interface NavItem {
  id: ViewType;
  label: string;
  icon: string;
}

export interface ExecutionResult {
  id: string;
  timestamp: string;
  command: string;
  output: string;
  status: 'success' | 'error' | 'pending';
  latency?: number;
  tokens?: number;
}

export interface Mode {
  id: string;
  name: string;
  description: string;
  icon: string;
  active: boolean;
  color: string;
}
