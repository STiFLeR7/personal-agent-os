import React, { useEffect, useState } from 'react';
import { History, ShieldCheck, Clock, Zap, CheckCircle2 } from 'lucide-react';
import { fetchActiveTasks } from '../lib/api';

export const TimelineView: React.FC = () => {
  const [tasks, setTasks] = useState<any[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchActiveTasks();
        setTasks(data);
      } catch (e) {
        console.error(e);
      }
    };
    loadData();
  }, []);

  return (
    <div className="max-w-[800px] mx-auto py-8 flex flex-col gap-6 fade-in">
       <h3 className="text-[22px] font-bold tracking-tight mb-2 text-dex-text-primary">Execution History</h3>
       {tasks.length > 0 ? (
         tasks.map((task: any) => (
           <TimelineItem key={task.task_id} task={task} />
         ))
       ) : (
         <div className="p-12 text-center border border-dashed border-dex-border rounded-2xl text-dex-text-secondary">
            <History size={32} className="mx-auto mb-4 opacity-10" />
            <p className="text-sm">No historical execution data found</p>
         </div>
       )}
    </div>
  );
};

const TimelineItem: React.FC<{ task: any }> = ({ task }) => {
  const trace = task.execution_trace;
  return (
    <div className="bg-white border border-dex-border rounded-[16px] overflow-hidden hover:border-dex-accent/20 transition-colors">
       <div className="p-6 flex items-center justify-between">
          <div className="flex flex-col gap-1">
             <span className="text-[10px] text-dex-text-secondary font-mono uppercase tracking-wider">Session: {task.task_id.substring(0, 8)}</span>
             <h4 className="text-[15px] font-semibold text-dex-text-primary">
                {trace.steps_executed[0]?.description || 'Autonomous Task Sequence'}
             </h4>
          </div>
          <div className="flex items-center gap-6">
             <div className="flex flex-col items-end">
                <span className="text-[10px] text-dex-text-secondary uppercase tracking-widest">Latency</span>
                <span className="text-[13px] font-bold font-mono">
                   {trace.steps_executed.reduce((acc: number, s: any) => acc + (s.duration_ms || 0), 0)}ms
                </span>
             </div>
             <div className="px-3 py-1 bg-dex-sidebar-hover rounded-full text-[11px] font-medium text-dex-text-primary border border-dex-border">
                {trace.steps_executed.length} Tool Calls
             </div>
          </div>
       </div>
       <div className="px-6 py-3 border-t border-dex-bg bg-[#FAFAFA] flex items-center justify-between">
          <div className="flex items-center gap-4">
             <div className="flex items-center gap-1.5 text-[11px] font-medium text-dex-warning">
                <ShieldCheck size={12} /> Medium Risk
             </div>
             <div className="flex items-center gap-1.5 text-[11px] font-medium text-dex-success">
                <CheckCircle2 size={12} /> Verified
             </div>
          </div>
          <span className="text-[11px] text-dex-text-secondary flex items-center gap-1.5">
             <Clock size={12}/> Just now
          </span>
       </div>
    </div>
  );
}
