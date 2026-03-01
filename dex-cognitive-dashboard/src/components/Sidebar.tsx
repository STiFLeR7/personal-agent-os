import React from 'react';
import { ICON_MAP, NAV_ITEMS } from '../constants';
import { ViewType } from '../types';
import { cn } from '../types';

interface SidebarProps {
  activeView: ViewType;
  onViewChange: (view: ViewType) => void;
  isOpen?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeView, onViewChange, isOpen = false }) => {
  return (
    <aside className={cn(
      "w-[240px] h-full bg-white border-r border-dex-border flex flex-col shrink-0 transition-transform duration-300 ease-in-out z-50",
      "fixed md:static inset-y-0 left-0",
      isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
    )}>
      <div className="p-6 mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-dex-accent rounded-lg flex items-center justify-center shadow-lg shadow-dex-accent/20">
            <span className="text-white font-bold text-lg">D</span>
          </div>
          <span className="font-bold text-xl tracking-tight">Dex</span>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = ICON_MAP[item.icon];
          return (
            <div
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={cn(
                "sidebar-item my-0.5",
                activeView === item.id && "sidebar-item-active bg-dex-sidebar-hover"
              )}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </div>
          );
        })}
      </nav>

      <div className="p-4 border-t border-dex-border bg-dex-bg/30">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-dex-accent/10 flex items-center justify-center text-[10px] font-bold text-dex-accent border border-dex-accent/20">
            JD
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold">Local Mode</span>
            <span className="text-[10px] text-dex-text-secondary opacity-70">v1.0.4-stable</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
