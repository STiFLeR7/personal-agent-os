import React, { useEffect, useState } from 'react';
import { Activity, Shield, Brain, Zap } from 'lucide-react';
import { fetchTelemetry, fetchActiveTasks } from '../lib/api';

export const DashboardView: React.FC = () => {
  const [telemetry, setTelemetry] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [telData, taskData] = await Promise.all([
          fetchTelemetry(),
          fetchActiveTasks()
        ]);
        setTelemetry(telData);
        setTasks(taskData);
      } catch (e) {
        console.error("Dashboard sync failed", e);
      }
    };
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 md:p-8 space-y-6 md:space-y-8 max-w-7xl mx-auto">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1.5 md:space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight">System Overview</h2>
          <p className="text-xs md:text-sm text-dex-text-secondary leading-relaxed max-w-lg">Dex is currently operating in <span className="text-dex-success font-semibold">Deep Work Mode</span> with {(telemetry?.success_rate * 100 || 98).toFixed(0)}% cognitive efficiency.</p>
        </div>
        <div className="flex items-center gap-2 md:gap-4 shrink-0">
          <button className="flex-1 md:flex-none px-3 md:px-4 py-2 bg-white border border-dex-border rounded-xl text-xs md:text-sm font-bold hover:bg-dex-sidebar-hover transition-all active:scale-95">
            Export
          </button>
          <button className="flex-1 md:flex-none px-3 md:px-4 py-2 bg-dex-accent text-white rounded-xl text-xs md:text-sm font-bold hover:opacity-90 shadow-lg shadow-dex-accent/20 transition-all active:scale-95">
            New Session
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        <div className="card bg-dex-accent text-white border-none p-5 md:p-6 space-y-4 shadow-lg shadow-dex-accent/20">
          <div className="flex items-center justify-between">
            <Brain size={20} className="md:w-6 md:h-6" />
            <span className="text-[10px] font-bold uppercase tracking-widest opacity-80">Avg Latency</span>
          </div>
          <div className="space-y-1">
            <div className="text-3xl md:text-4xl font-bold">{(telemetry?.avg_latency?.executor || 0).toFixed(0)}ms</div>
            <p className="text-[10px] md:text-xs opacity-80">Optimal processing threshold</p>
          </div>
        </div>
        
        <div className="card p-5 md:p-6 space-y-4">
          <div className="flex items-center justify-between">
            <Shield size={20} className="text-dex-success md:w-6 md:h-6" />
            <span className="text-[10px] font-bold text-dex-text-secondary uppercase tracking-widest">Privacy Status</span>
          </div>
          <div className="space-y-1">
            <div className="text-3xl md:text-4xl font-bold text-dex-text-primary">Secure</div>
            <p className="text-[10px] md:text-xs text-dex-text-secondary">All local buffers encrypted</p>
          </div>
        </div>

        <div className="card p-5 md:p-6 space-y-4 sm:col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between">
            <Zap size={20} className="text-dex-warning md:w-6 md:h-6" />
            <span className="text-[10px] font-bold text-dex-text-secondary uppercase tracking-widest">Active Tasks</span>
          </div>
          <div className="space-y-1">
            <div className="text-3xl md:text-4xl font-bold text-dex-text-primary">{tasks.length}</div>
            <p className="text-[10px] md:text-xs text-dex-text-secondary">Grounding and analysis processes</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
        <div className="lg:col-span-2 space-y-4 md:space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-base md:text-lg font-bold">Active Execution Traces</h3>
            <button className="text-[10px] md:text-xs text-dex-accent font-bold uppercase tracking-wider">View All</button>
          </div>
          <div className="space-y-3">
            {(!tasks || tasks.length === 0) ? (
              <div className="card p-8 text-center text-dex-text-secondary border-dashed opacity-50 italic text-sm">
                No active execution streams detected.
              </div>
            ) : (
              tasks.map(task => (
                <ActivityItem 
                  key={task?.task_id || Math.random()}
                  title={task?.task_id?.substring(0, 13) || 'Process'}
                  time="Live"
                  description={task?.execution_trace?.steps_executed?.map((s: any) => s.description).join(' → ') || 'Initializing...'}
                  icon={<Zap size={14} />}
                />
              ))
            )}
          </div>
        </div>

        <div className="space-y-4 md:space-y-6">
          <h3 className="text-base md:text-lg font-bold">Risk Distribution</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-1 gap-3">
            <RiskMetric label="Critical" count={telemetry?.risk_distribution?.high || 0} color="#FF3B30" />
            <RiskMetric label="Moderate" count={telemetry?.risk_distribution?.medium || 0} color="#FF9F0A" />
            <RiskMetric label="Standard" count={telemetry?.risk_distribution?.low || 0} color="#34C759" />
          </div>
          <button className="w-full py-3.5 bg-dex-sidebar-hover text-dex-text-primary rounded-xl text-xs md:text-sm font-bold hover:bg-dex-border/50 transition-all active:scale-[0.98]">
            Security Audit
          </button>
        </div>
      </div>
    </div>
  );
};

const ActivityItem: React.FC<{ title: string; time: string; description: string; icon: React.ReactNode }> = ({ title, time, description, icon }) => (
  <div className="card flex gap-4 p-4 hover:border-dex-accent/20 cursor-pointer group">
    <div className="w-10 h-10 rounded-xl bg-dex-sidebar-hover flex items-center justify-center text-dex-text-secondary group-hover:text-dex-accent transition-colors">
      {icon}
    </div>
    <div className="flex-1 space-y-1">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold font-mono">{title}</h4>
        <span className="text-[10px] text-dex-text-secondary font-mono">{time}</span>
      </div>
      <p className="text-xs text-dex-text-secondary leading-relaxed line-clamp-1">{description}</p>
    </div>
  </div>
);

const RiskMetric: React.FC<{ label: string; count: number; color: string }> = ({ label, count, color }) => (
  <div className="card flex items-center justify-between p-3">
    <div className="flex items-center gap-3">
      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-sm font-medium">{label}</span>
    </div>
    <div className="text-[12px] font-bold font-mono">
      {count}
    </div>
  </div>
);
