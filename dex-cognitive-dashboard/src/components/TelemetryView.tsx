import React, { useEffect, useState } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { Cpu, Activity, Database, Zap } from 'lucide-react';
import { fetchTelemetry, fetchActiveTasks } from '../lib/api';

export const TelemetryView: React.FC = () => {
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
        console.error(e);
      }
    };
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartData = [
    { name: 'Planner', val: telemetry?.avg_latency?.planner || 0 },
    { name: 'Executor', val: telemetry?.avg_latency?.executor || 0 },
    { name: 'Verifier', val: telemetry?.avg_latency?.verifier || 0 },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto fade-in">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          label="Success Rate" 
          value={`${(telemetry?.success_rate * 100 || 0).toFixed(1)}%`} 
          change="Live" 
          icon={<Zap size={18} className="text-dex-success" />} 
        />
        <MetricCard 
          label="Total Tasks" 
          value={telemetry?.total_tasks || 0} 
          change="+1" 
          icon={<Activity size={18} className="text-dex-accent" />} 
        />
        <MetricCard 
          label="Active Streams" 
          value={tasks.length} 
          change="Steady" 
          icon={<Cpu size={18} className="text-dex-warning" />} 
        />
        <MetricCard 
          label="Risk High" 
          value={telemetry?.risk_distribution?.high || 0} 
          change="Shielded" 
          icon={<Database size={18} className="text-dex-text-primary" />} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Latency Distribution (ms)</h3>
            <span className="text-[10px] font-mono text-dex-text-secondary uppercase">By Component</span>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E5E7" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6B6B6B' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6B6B6B' }} />
                <Tooltip />
                <Area type="monotone" dataKey="val" stroke="#0A84FF" fill="#0A84FF20" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Tool Usage Intensity</h3>
            <span className="text-[10px] font-mono text-dex-text-secondary uppercase">Frequency</span>
          </div>
          <div className="space-y-4">
             {Object.entries(telemetry?.tool_usage || {}).map(([tool, count]: [any, any]) => (
               <div key={tool} className="flex items-center justify-between">
                  <span className="text-xs font-mono text-dex-text-secondary">{tool}</span>
                  <div className="flex-1 mx-4 h-1 bg-dex-bg rounded-full overflow-hidden">
                     <div className="h-full bg-dex-accent" style={{ width: `${Math.min(100, (count / 10) * 100)}%` }} />
                  </div>
                  <span className="text-xs font-bold">{count}</span>
               </div>
             ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricCard: React.FC<{ label: string; value: string; change: string; icon: React.ReactNode }> = ({ label, value, change, icon }) => (
  <div className="card flex flex-col justify-between h-32">
    <div className="flex items-center justify-between">
      <span className="text-xs font-medium text-dex-text-secondary">{label}</span>
      {icon}
    </div>
    <div className="space-y-1">
      <div className="text-2xl font-bold tracking-tight">{value}</div>
      <div className={`text-[10px] font-medium ${change.startsWith('+') ? 'text-dex-success' : 'text-dex-danger'}`}>
        {change} <span className="text-dex-text-secondary font-normal">vs last period</span>
      </div>
    </div>
  </div>
);
