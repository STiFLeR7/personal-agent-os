import React, { useEffect, useState } from 'react';
import { Layers, Zap, Shield, Moon, Cpu, ToggleLeft, ToggleRight } from 'lucide-react';
import { fetchModes } from '../lib/api';

export const ModesView: React.FC = () => {
  const [modes, setModes] = useState<any[]>([]);

  useEffect(() => {
    const loadModes = async () => {
      try {
        const data = await fetchModes();
        setModes(data);
      } catch (e) {
        console.error(e);
      }
    };
    loadModes();
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto fade-in">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold tracking-tight text-dex-text-primary">Cognitive Modes</h2>
        <p className="text-sm text-dex-text-secondary">Switch between specialized operational profiles.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {modes.map((mode) => (
          <ModeCard key={mode.id} mode={mode} />
        ))}
      </div>
    </div>
  );
};

const ModeCard: React.FC<{ mode: any }> = ({ mode }) => {
  const [active, setActive] = useState(mode.active);
  
  const Icon = mode.id === 'deep-work' ? Zap : mode.id === 'privacy-plus' ? Shield : Cpu;

  return (
    <div className={`p-6 border rounded-[20px] transition-all flex flex-col gap-4 shadow-sm ${active ? 'bg-white border-dex-accent/20 ring-1 ring-dex-accent/5' : 'bg-[#FAFAFA] border-dex-border opacity-80'}`}>
       <div className="flex justify-between items-start">
          <div className={`p-2.5 rounded-xl ${active ? 'bg-dex-accent/10 text-dex-accent' : 'bg-dex-bg text-dex-text-secondary'}`}>
             <Icon size={20} />
          </div>
          <button onClick={() => setActive(!active)} className={`transition-colors ${active ? 'text-dex-accent' : 'text-dex-text-secondary opacity-40'}`}>
             {active ? <ToggleRight size={32}/> : <ToggleLeft size={32}/>}
          </button>
       </div>
       <div>
          <h4 className="text-[15px] font-bold text-dex-text-primary mb-1">{mode.name}</h4>
          <p className="text-[12px] text-dex-text-secondary leading-relaxed">
             Specialized profile for {mode.name.toLowerCase()} requirements.
          </p>
       </div>
    </div>
  );
};
