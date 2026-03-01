import React from 'react';
import { ViewType } from '../types';
import { NAV_ITEMS } from '../constants';
import { Menu, Zap } from 'lucide-react';

interface TopNavProps {
  activeView: ViewType;
  onMenuClick?: () => void;
}

export const TopNav: React.FC<TopNavProps> = ({ activeView, onMenuClick }) => {
  const currentItem = NAV_ITEMS.find(item => item.id === activeView);

  return (
    <header className="h-16 border-b border-dex-border flex items-center justify-between px-4 md:px-8 bg-white/80 backdrop-blur-md sticky top-0 z-30">
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <button 
          onClick={onMenuClick}
          className="p-2 -ml-2 hover:bg-dex-sidebar-hover rounded-lg md:hidden transition-colors"
        >
          <Menu size={20} className="text-dex-text-secondary" />
        </button>

        <div className="flex flex-col">
          <h1 className="text-base md:text-lg font-bold leading-tight">{currentItem?.label || 'Dex'}</h1>
          <p className="hidden xs:block text-[10px] md:text-xs text-dex-text-secondary font-medium opacity-80">
            {activeView === 'dashboard' ? 'Overview of your cognitive workspace' : 
             activeView === 'console' ? 'Direct command and control interface' :
             currentItem?.label ? `Manage your ${currentItem.label.toLowerCase()}` : 'Cognitive workspace'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        <div className="flex items-center gap-2 px-2.5 py-1 bg-dex-success/10 border border-dex-success/20 rounded-full">
          <div className="w-1.5 h-1.5 bg-dex-success rounded-full animate-pulse shadow-[0_0_4px_rgba(52,199,89,0.5)]" />
          <span className="text-[10px] font-bold text-dex-success uppercase tracking-wider hidden sm:inline">Deep Work</span>
          <span className="text-[10px] font-bold text-dex-success uppercase tracking-wider sm:hidden">Online</span>
        </div>
        
        <div className="hidden xs:flex h-6 w-[1px] bg-dex-border mx-1 md:mx-2" />
        
        <div className="hidden md:flex items-center gap-2 text-dex-text-secondary">
          <span className="text-[11px] font-mono font-medium">Latency: 14ms</span>
        </div>
      </div>
    </header>
  );
};
