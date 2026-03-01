import React, { useEffect, useState } from 'react';
import { Bell, Clock, Calendar, CheckCircle2, AlertTriangle } from 'lucide-react';
import { fetchReminders } from '../lib/api';

export const RemindersView: React.FC = () => {
  const [reminders, setReminders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadReminders = async () => {
      try {
        const data = await fetchReminders();
        setReminders(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadReminders();
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto fade-in">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight">Active Reminders</h2>
          <p className="text-sm text-dex-text-secondary">Deterministic schedule monitoring from Dex Daemon.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#E8F5E9] border border-[#C8E6C9] rounded-full">
           <div className="w-1.5 h-1.5 bg-[#34C759] rounded-full mr-1" />
           <span className="text-[11px] font-medium text-[#2E7D32]">Daemon Online</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? (
          <div className="col-span-full py-12 text-center text-dex-text-secondary animate-pulse">Synchronizing with core...</div>
        ) : reminders.length === 0 ? (
          <div className="col-span-full py-24 border border-dashed border-dex-border rounded-3xl text-center text-dex-text-secondary">
             <Bell size={48} className="mx-auto mb-4 opacity-10" />
             <p className="text-sm">No active reminders in the pipeline.</p>
          </div>
        ) : (
          reminders.map((rem) => (
            <div key={rem.id} className={`card p-6 flex flex-col gap-4 border-l-4 ${rem.is_active ? 'border-l-dex-accent' : 'border-l-dex-border opacity-60'}`}>
               <div className="flex justify-between items-start">
                  <div className="p-2 bg-dex-sidebar-hover rounded-lg text-dex-accent">
                     <Clock size={18} />
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${rem.is_active ? 'bg-blue-50 text-dex-accent' : 'bg-gray-100 text-dex-text-secondary'}`}>
                     {rem.is_active ? 'Active' : 'Triggered'}
                  </span>
               </div>
               
               <div>
                  <h4 className="text-sm font-semibold text-dex-text-primary mb-1">{rem.message}</h4>
                  <div className="flex items-center gap-3 text-[11px] text-dex-text-secondary font-mono">
                     <span className="flex items-center gap-1"><Calendar size={12}/> {new Date(rem.scheduled_time).toLocaleDateString()}</span>
                     <span>•</span>
                     <span>{new Date(rem.scheduled_time).toLocaleTimeString()}</span>
                  </div>
               </div>

               <div className="pt-4 border-t border-dex-bg flex justify-between items-center mt-auto">
                  <span className="text-[10px] text-dex-text-secondary uppercase font-bold tracking-widest">Priority: {rem.priority}</span>
                  <button className="text-[11px] font-bold text-dex-accent hover:underline">Manage</button>
               </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
