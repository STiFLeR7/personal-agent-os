"use client";

import { useEffect, useState } from "react";
import { 
  Activity, 
  Database, 
  ShieldCheck, 
  Terminal, 
  LayoutDashboard,
  Settings,
  AlertTriangle,
  CheckCircle2,
  Clock,
  History,
  Bell,
  StickyNote,
  Cpu,
  ChevronRight,
  Plus,
  Zap,
  ToggleLeft,
  ToggleRight,
  Search,
  FileText,
  Workflow
} from "lucide-react";
import { fetchTelemetry, fetchActiveTasks, searchMemory } from "@/lib/api";

export default function Dashboard() {
  const [activeView, setActiveView] = useState("Dashboard");
  const [telemetry, setTelemetry] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
        console.error("Dashboard Sync Failed", e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen bg-[#F7F7F8] text-[#111111]">
      {/* 5. Sidebar Design */}
      <aside className="w-[240px] bg-white border-r border-[#E5E5E7] flex flex-col shrink-0 z-20">
        <div className="h-16 flex items-center px-6 gap-3">
          <div className="w-6 h-6 bg-[#0A84FF] rounded-md flex items-center justify-center">
             <Cpu size={14} className="text-white" />
          </div>
          <span className="text-[14px] font-bold tracking-tight uppercase">Dex OS</span>
        </div>

        <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
          <SidebarItem icon={<LayoutDashboard size={18}/>} label="Dashboard" active={activeView === "Dashboard"} onClick={() => setActiveView("Dashboard")} />
          <SidebarItem icon={<Zap size={18}/>} label="Console" active={activeView === "Console"} onClick={() => setActiveView("Console")} />
          <SidebarItem icon={<Database size={18}/>} label="Memory" active={activeView === "Memory"} onClick={() => setActiveView("Memory")} />
          <SidebarItem icon={<History size={18}/>} label="Timeline" active={activeView === "Timeline"} onClick={() => setActiveView("Timeline")} />
          <SidebarItem icon={<Bell size={18}/>} label="Reminders" active={activeView === "Reminders"} onClick={() => setActiveView("Reminders")} />
          <SidebarItem icon={<StickyNote size={18}/>} label="Notes" active={activeView === "Notes"} onClick={() => setActiveView("Notes")} />
          <SidebarItem icon={<Activity size={18}/>} label="Telemetry" active={activeView === "Telemetry"} onClick={() => setActiveView("Telemetry")} />
          <SidebarItem icon={<Workflow size={18}/>} label="Modes" active={activeView === "Modes"} onClick={() => setActiveView("Modes")} />
          <SidebarItem icon={<Settings size={18}/>} label="Settings" active={activeView === "Settings"} onClick={() => setActiveView("Settings")} />
        </nav>

        <div className="p-4 border-t border-[#E5E5E7] bg-[#FAFAFA]">
           <div className="flex items-center gap-2 mb-1">
             <div className="w-1.5 h-1.5 bg-[#34C759] rounded-full" />
             <span className="text-[12px] text-[#6B6B6B]">Local Instance</span>
           </div>
        </div>
      </aside>

      {/* Main Panel */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#F7F7F8] overflow-hidden">
        {/* 6. Top Navigation */}
        <header className="h-[64px] border-b border-[#E5E5E7] px-8 flex items-center justify-between bg-white/50 backdrop-blur-md shrink-0">
           <div>
             <h2 className="text-[16px] font-semibold tracking-tight">{activeView}</h2>
             <p className="text-[11px] text-[#6B6B6B]">Personal AI Control Interface</p>
           </div>
           
           <div className="flex items-center gap-4">
              {/* Mode indicator badge */}
              <div className="flex items-center bg-[#E8F5E9] border border-[#C8E6C9] px-3 py-1 rounded-full">
                 <div className="w-1.5 h-1.5 bg-[#34C759] rounded-full mr-2" />
                 <span className="text-[11px] font-medium text-[#2E7D32]">Deep Work Mode</span>
              </div>
              <span className="text-[11px] text-[#6B6B6B] font-medium border-l border-[#E5E5E7] pl-4">Local Mode</span>
           </div>
        </header>

        {/* Active View */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-[1280px] mx-auto p-[24px]">
             {activeView === "Dashboard" && <OverviewView telemetry={telemetry} tasks={tasks} />}
             {activeView === "Console" && <ConsoleView tasks={tasks} />}
             {activeView === "Memory" && <MemoryExplorer />}
             {activeView === "Timeline" && <TimelineView tasks={tasks} />}
             {activeView === "Modes" && <ModesView />}
             {activeView === "Telemetry" && <TelemetryView telemetry={telemetry} />}
          </div>
        </div>
      </div>
    </div>
  );
}

function SidebarItem({ icon, label, active, onClick }: any) {
  return (
    <div 
      onClick={onClick}
      className={`
        flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-all relative
        ${active ? 'bg-[#F0F0F2] text-[#111111] font-medium' : 'text-[#6B6B6B] hover:bg-[#F0F0F2] hover:text-[#111111]'}
      `}
    >
      {active && <div className="absolute left-0 top-2 bottom-2 w-[2px] bg-[#0A84FF] rounded-full" />}
      <span className={active ? 'text-[#0A84FF]' : ''}>{icon}</span>
      <span className="text-[14px]">{label}</span>
    </div>
  );
}

/* --- 7.1 Console View --- */
function ConsoleView({ tasks }: any) {
  return (
    <div className="max-w-[720px] mx-auto py-12 flex flex-col gap-12 fade-in">
       {/* Centered Command Box */}
       <div className="w-full">
          <div className="relative">
             <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#6B6B6B]">
                <Zap size={20} />
             </div>
             <input 
               type="text" 
               placeholder="Ask Dex to do something..." 
               className="w-full h-[56px] pl-12 pr-6 bg-white border border-[#E5E5E7] rounded-[12px] text-[15px] focus:outline-none focus:border-[#0A84FF] transition-all"
             />
          </div>
       </div>

       {/* Results Area */}
       <div className="flex flex-col gap-4">
          {tasks.length > 0 ? (
            tasks.map((task: any) => (
              <ResultCard key={task.task_id} task={task} />
            ))
          ) : (
            <div className="py-24 text-center text-[#6B6B6B]">
               <Terminal size={40} className="mx-auto mb-4 opacity-10" />
               <p className="text-sm">Dex is ready for instructions</p>
            </div>
          )}
       </div>
    </div>
  );
}

function ResultCard({ task }: any) {
  const trace = task.execution_trace;
  return (
    <div className="bg-white p-[16px] rounded-[16px] border border-[#E5E5E7] shadow-none fade-in">
       <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-2">
             <span className="text-[12px] font-mono text-[#6B6B6B]">{task.task_id.slice(0, 8)}</span>
             <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${trace.status === 'running' ? 'bg-[#FFF3E0] text-[#E65100]' : 'bg-[#E8F5E9] text-[#2E7D32]'}`}>
               {trace.status}
             </span>
          </div>
          {trace.status === 'running' && (
            <div className="flex gap-1">
               <div className="w-1 h-1 bg-[#6B6B6B] rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
               <div className="w-1 h-1 bg-[#6B6B6B] rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
               <div className="w-1 h-1 bg-[#6B6B6B] rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
            </div>
          )}
       </div>
       <div className="space-y-3">
          {trace.steps_executed.map((step: any, i: number) => (
             <div key={i} className="flex items-center gap-3 text-[13px]">
                <CheckCircle2 size={14} className="text-[#34C759]" />
                <span className="text-[#111111]">{step.description}</span>
                <span className="ml-auto text-[11px] text-[#6B6B6B] font-mono">{step.duration_ms}ms</span>
             </div>
          ))}
       </div>
    </div>
  );
}

/* --- 7.2 Timeline View --- */
function TimelineView({ tasks }: any) {
  return (
    <div className="max-w-[800px] mx-auto py-8 flex flex-col gap-6 fade-in">
       <h3 className="text-[22px] font-bold tracking-tight mb-2">Execution History</h3>
       {tasks.length > 0 ? (
         tasks.map((task: any) => (
           <TimelineItem key={task.task_id} task={task} />
         ))
       ) : (
         <div className="p-12 text-center border border-dashed border-[#E5E5E7] rounded-2xl text-[#6B6B6B]">
            <History size={32} className="mx-auto mb-4 opacity-10" />
            <p className="text-sm">No historical execution data found</p>
         </div>
       )}
    </div>
  );
}

function TimelineItem({ task }: any) {
  const trace = task.execution_trace;
  return (
    <div className="bg-white border border-[#E5E5E7] rounded-[16px] overflow-hidden">
       <div className="p-[16px] flex items-center justify-between bg-white">
          <div className="flex flex-col gap-0.5">
             <span className="text-[11px] text-[#6B6B6B] font-mono uppercase tracking-wider">Task Session</span>
             <h4 className="text-[14px] font-semibold text-[#111111]">Deterministic Plan Execution</h4>
          </div>
          <div className="flex items-center gap-4">
             <div className="flex flex-col items-end">
                <span className="text-[11px] text-[#6B6B6B]">Latency</span>
                <span className="text-[12px] font-bold">428ms</span>
             </div>
             <div className="px-3 py-1 bg-[#F2F2F7] rounded-full text-[11px] font-medium text-[#111111]">
                {trace.steps_executed.length} Tool Calls
             </div>
          </div>
       </div>
       <div className="px-[16px] py-[12px] border-t border-[#F2F2F7] bg-[#FAFAFA] flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#FF9F0A]">
             <ShieldCheck size={12} /> Medium Risk
          </div>
          <span className="text-[11px] text-[#6B6B6B] ml-auto">Verified by Dex Core</span>
       </div>
    </div>
  );
}

/* --- 7.3 Memory Explorer --- */
function MemoryExplorer() {
  return (
    <div className="h-[calc(100vh-160px)] flex bg-white border border-[#E5E5E7] rounded-[16px] overflow-hidden fade-in">
       {/* Left: Memory Tree */}
       <div className="w-1/3 border-r border-[#E5E5E7] flex flex-col">
          <div className="p-4 border-b border-[#E5E5E7]">
             <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6B6B6B]" />
                <input 
                  type="text" 
                  placeholder="Filter context..." 
                  className="w-full h-8 pl-9 bg-[#F2F2F7] border-none rounded-md text-[13px] focus:ring-1 focus:ring-[#0A84FF]"
                />
             </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
             <MemoryGroup label="Project Contexts">
                <MemoryNode label="personal-agent-os" active />
                <MemoryNode label="cognitive-dashboard" />
             </MemoryGroup>
             <MemoryGroup label="Recent Sessions">
                <MemoryNode label="Dashboard Setup" />
                <MemoryNode label="Risk Engine Logic" />
             </MemoryGroup>
          </div>
       </div>
       {/* Right: Content Panel */}
       <div className="flex-1 bg-[#FAFAFA] flex flex-col">
          <div className="h-12 border-b border-[#E5E5E7] px-6 flex items-center justify-between bg-white">
             <span className="text-[13px] font-semibold">personal-agent-os</span>
             <div className="flex gap-2">
                <button className="p-1 hover:bg-[#F2F2F7] rounded text-[#6B6B6B]"><Settings size={14}/></button>
             </div>
          </div>
          <div className="flex-1 p-8 text-[14px] leading-relaxed text-[#6B6B6B] overflow-y-auto">
             <h3 className="text-[18px] font-bold text-[#111111] mb-4">Semantic Context Layer</h3>
             <p className="mb-4">This project-level context maintains information regarding the Phase 4 Cognitive Core upgrade. It tracks the integration of the Gemini Reasoning Layer and the Risk Engine.</p>
             <div className="p-4 bg-white border border-[#E5E5E7] rounded-lg space-y-2">
                <div className="flex justify-between text-[12px]"><span className="font-medium text-[#111111]">Total Embeddings</span><span>1,428</span></div>
                <div className="flex justify-between text-[12px]"><span className="font-medium text-[#111111]">Storage Index</span><span>SQLite/HNSW</span></div>
             </div>
          </div>
       </div>
    </div>
  );
}

function MemoryGroup({ label, children }: any) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[11px] font-bold text-[#A1A1A1] uppercase tracking-wider mb-2">{label}</span>
      {children}
    </div>
  );
}

function MemoryNode({ label, active }: any) {
  return (
    <div className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer text-[13px] ${active ? 'bg-[#F2F2F7] text-[#111111] font-medium' : 'text-[#6B6B6B] hover:bg-[#F2F2F7]'}`}>
      <FileText size={14} className={active ? 'text-[#0A84FF]' : 'opacity-40'} />
      {label}
    </div>
  );
}

/* --- 7.4 Telemetry Dashboard --- */
function OverviewView({ telemetry, tasks }: any) {
  return (
    <div className="flex flex-col gap-[32px] fade-in">
       {/* 7.4 Metric Cards */}
       <div className="grid grid-cols-4 gap-[16px]">
          <TelemetryCard title="Execution Success" value={`${(telemetry?.success_rate * 100 || 0).toFixed(1)}%`} label="System" />
          <TelemetryCard title="Mean Latency" value={`${(telemetry?.avg_latency?.executor || 0).toFixed(0)}ms`} label="Core" />
          <TelemetryCard title="Active Streams" value={tasks.length} label="Live" />
          <TelemetryCard title="Risk Gating" value={telemetry?.risk_distribution?.high || 0} label="Intervention" />
       </div>

       {/* Charts Row */}
       <div className="grid grid-cols-12 gap-[24px]">
          <div className="col-span-8 bg-white border border-[#E5E5E7] rounded-[16px] p-[24px]">
             <h3 className="text-[15px] font-semibold mb-8">Performance Distribution</h3>
             <div className="h-[200px] flex items-end gap-1 px-4">
                {[30, 45, 25, 60, 80, 50, 40, 70, 90, 65, 55, 75, 85, 60, 40].map((h, i) => (
                  <div key={i} className="flex-1 bg-[#F2F2F7] rounded-t-sm relative group">
                     <div className="absolute bottom-0 left-0 right-0 bg-[#0A84FF]/20 rounded-t-sm" style={{height: `${h}%`}} />
                  </div>
                ))}
             </div>
             <div className="flex justify-between mt-4 px-4 text-[10px] text-[#A1A1A1] font-mono">
                <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>23:59</span>
             </div>
          </div>

          <div className="col-span-4 flex flex-col gap-6">
             <div className="bg-white border border-[#E5E5E7] rounded-[16px] p-[24px]">
                <h3 className="text-[14px] font-bold mb-4">Risk Profile</h3>
                <div className="space-y-4">
                   <RiskRow label="Critical" count={telemetry?.risk_distribution?.high || 0} color="#FF3B30" />
                   <RiskRow label="Moderate" count={telemetry?.risk_distribution?.medium || 0} color="#FF9F0A" />
                   <RiskRow label="Standard" count={telemetry?.risk_distribution?.low || 0} color="#34C759" />
                </div>
             </div>
          </div>
       </div>
    </div>
  );
}

function TelemetryCard({ title, value, label }: any) {
  return (
    <div className="bg-white border border-[#E5E5E7] p-[24px] rounded-[16px] shadow-none">
       <span className="text-[11px] font-bold text-[#A1A1A1] uppercase tracking-wider block mb-2">{title}</span>
       <div className="text-[28px] font-bold tracking-tight mb-1">{value}</div>
       <span className="text-[11px] text-[#6B6B6B]">{label} Mode</span>
    </div>
  );
}

function RiskRow({ label, count, color }: any) {
  const width = Math.min(100, (count / 10) * 100);
  return (
    <div className="flex flex-col gap-1.5">
       <div className="flex justify-between text-[12px]">
          <span className="text-[#6B6B6B]">{label}</span>
          <span className="font-bold">{count}</span>
       </div>
       <div className="h-1 bg-[#F2F2F7] rounded-full overflow-hidden">
          <div className="h-full rounded-full" style={{width: `${width}%`, backgroundColor: color}} />
       </div>
    </div>
  );
}

/* --- 7.5 Mode Control Panel --- */
function ModesView() {
  return (
    <div className="max-w-[960px] py-8 fade-in">
       <h3 className="text-[22px] font-bold tracking-tight mb-8">Operational Modes</h3>
       <div className="grid grid-cols-3 gap-6">
          <ModeCard icon={<Zap size={20}/>} name="Performance Mode" desc="Full resource allocation for rapid execution sequences." />
          <ModeCard icon={<ShieldCheck size={20}/>} name="Strict Safety" desc="Elevates verification thresholds for all tool operations." active />
          <ModeCard icon={<Clock size={20}/>} name="Delayed Execution" desc="Buffers tasks for scheduled batch processing." />
          <ModeCard icon={<Cpu size={20}/>} name="Deep Work" desc="Restricts notification throughput to critical alerts only." active />
          <ModeCard icon={<Database size={20}/>} name="Context Heavy" desc="Expands memory retrieval scope for planning." />
       </div>
    </div>
  );
}

function ModeCard({ icon, name, desc, active }: any) {
  return (
    <div className={`p-6 border rounded-[16px] transition-all flex flex-col gap-4 ${active ? 'bg-[#F2F2F7] border-[#0A84FF20]' : 'bg-white border-[#E5E5E7]'}`}>
       <div className="flex justify-between items-start">
          <div className={`p-2 rounded-lg ${active ? 'bg-white text-[#0A84FF]' : 'bg-[#F7F7F8] text-[#6B6B6B]'}`}>{icon}</div>
          <button className={`p-0.5 rounded-full ${active ? 'text-[#0A84FF]' : 'text-[#A1A1A1]'}`}>
             {active ? <ToggleRight size={28}/> : <ToggleLeft size={28}/>}
          </button>
       </div>
       <div>
          <h4 className="text-[15px] font-bold mb-1">{name}</h4>
          <p className="text-[12px] text-[#6B6B6B] leading-relaxed">{desc}</p>
       </div>
    </div>
  );
}

function TelemetryView({ telemetry }: any) {
  return (
    <div className="py-24 text-center text-[#6B6B6B] fade-in">
       <Activity size={48} className="mx-auto mb-4 opacity-10" />
       <h3 className="text-[18px] font-bold text-[#111111] mb-2">Advanced Telemetry Diagnostics</h3>
       <p className="text-sm max-w-[400px] mx-auto">This panel provides node-level latency distribution and token utilization metrics for the Gemini Reasoning Layer.</p>
    </div>
  );
}
