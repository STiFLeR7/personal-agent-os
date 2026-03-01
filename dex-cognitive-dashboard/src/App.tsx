/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopNav } from './components/TopNav';
import { ConsoleView } from './components/ConsoleView';
import { DashboardView } from './components/DashboardView';
import { MemoryView } from './components/MemoryView';
import { TimelineView } from './components/TimelineView';
import { TelemetryView } from './components/TelemetryView';
import { ModesView } from './components/ModesView';
import { RemindersView } from './components/RemindersView';
import { NotesView } from './components/NotesView';
import { SettingsView } from './components/SettingsView';
import { ViewType } from './types';
import { motion, AnimatePresence } from 'motion/react';

export default function App() {
  const [activeView, setActiveView] = useState<ViewType>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardView />;
      case 'console':
        return <ConsoleView />;
      case 'memory':
        return <MemoryView />;
      case 'timeline':
        return <TimelineView />;
      case 'reminders':
        return <RemindersView />;
      case 'notes':
        return <NotesView />;
      case 'telemetry':
        return <TelemetryView />;
      case 'modes':
        return <ModesView />;
      case 'settings':
        return <SettingsView />;
      default:
        return (
          <div className="flex items-center justify-center h-full text-dex-text-secondary">
            <div className="text-center space-y-2">
              <h3 className="text-lg font-medium">View Under Construction</h3>
              <p className="text-sm">The {activeView} module is being calibrated.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-dex-bg selection:bg-dex-accent/20">
      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar 
        activeView={activeView} 
        onViewChange={(view) => {
          setActiveView(view);
          setSidebarOpen(false);
        }} 
        isOpen={sidebarOpen}
      />
      
      <main className="flex-1 flex flex-col min-w-0 relative h-full">
        <TopNav activeView={activeView} onMenuClick={() => setSidebarOpen(true)} />
        
        <div className="flex-1 overflow-y-auto overflow-x-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="h-full"
            >
              {renderView()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
