import React, { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Shield, Cpu, Zap, Bell, Monitor, Globe, Database } from 'lucide-react';
import { fetchConfig } from '../lib/api';

export const SettingsView: React.FC = () => {
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const data = await fetchConfig();
        setConfig(data);
      } catch (e) {
        console.error(e);
      }
    };
    loadConfig();
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-4xl mx-auto fade-in">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold tracking-tight text-dex-text-primary">System Calibration</h2>
        <p className="text-sm text-dex-text-secondary">Global parameters for the Dex Cognitive Operating Layer.</p>
      </div>

      <div className="space-y-6">
        <SettingsSection title="Reasoning Engine" icon={<Cpu size={18} />}>
           <SettingRow label="LLM Provider" value={config?.llm_provider || 'Loading...'} />
           <SettingRow label="Model Identifier" value={config?.llm_model || 'Loading...'} />
           <SettingRow label="Temperature" value="0.7 (Standard)" />
        </SettingsSection>

        <SettingsSection title="Notification Channels" icon={<Bell size={18} />}>
           <SettingToggle label="Desktop Notifications" active={true} />
           <SettingToggle label="Discord Integration" active={config?.discord_enabled || false} />
           <SettingToggle label="WhatsApp (Twilio)" active={false} />
        </SettingsSection>

        <SettingsSection title="Security & Privacy" icon={<Shield size={18} />}>
           <SettingRow label="Risk Threshold" value="Medium (Human-in-the-loop)" />
           <SettingToggle label="Local Execution Policy" active={true} />
           <SettingRow label="Data Residency" value="D:\personal-agent-os\.agentic_os" />
        </SettingsSection>

        <SettingsSection title="Developer Controls" icon={<Database size={18} />}>
           <SettingToggle label="Debug Mode Tracing" active={config?.debug_mode || false} />
           <SettingRow label="API Interface" value="http://0.0.0.0:8000" />
        </SettingsSection>
      </div>
    </div>
  );
};

const SettingsSection: React.FC<{ title: string; icon: React.ReactNode; children: React.ReactNode }> = ({ title, icon, children }) => (
  <div className="bg-white border border-dex-border rounded-2xl overflow-hidden shadow-sm">
    <div className="px-6 py-4 bg-[#FAFAFA] border-b border-dex-bg flex items-center gap-3">
       <div className="text-dex-accent">{icon}</div>
       <h3 className="text-xs font-bold uppercase tracking-widest text-dex-text-primary">{title}</h3>
    </div>
    <div className="divide-y divide-dex-bg">
       {children}
    </div>
  </div>
);

const SettingRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="px-6 py-4 flex items-center justify-between group hover:bg-dex-bg transition-colors">
     <span className="text-sm font-medium text-dex-text-secondary">{label}</span>
     <span className="text-sm font-bold text-dex-text-primary font-mono">{value}</span>
  </div>
);

const SettingToggle: React.FC<{ label: string; active: boolean }> = ({ label, active }) => (
  <div className="px-6 py-4 flex items-center justify-between group hover:bg-dex-bg transition-colors">
     <span className="text-sm font-medium text-dex-text-secondary">{label}</span>
     <div className={`w-10 h-5 rounded-full relative transition-colors ${active ? 'bg-dex-accent' : 'bg-dex-border'}`}>
        <div className={`absolute top-1 w-3 h-3 rounded-full bg-white transition-all ${active ? 'left-6' : 'left-1'}`} />
     </div>
  </div>
);
