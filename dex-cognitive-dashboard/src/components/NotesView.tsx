import React, { useEffect, useState } from 'react';
import { StickyNote, FileText, Search, Plus, Clock, ChevronRight } from 'lucide-react';
import { fetchNotes } from '../lib/api';

export const NotesView: React.FC = () => {
  const [notes, setNotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadNotes = async () => {
      try {
        const data = await fetchNotes();
        setNotes(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadNotes();
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto fade-in h-full flex flex-col">
      <div className="flex items-center justify-between shrink-0">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight">Dex Notes</h2>
          <p className="text-sm text-dex-text-secondary">Semantic thought storage and reference library.</p>
        </div>
        <button className="px-4 py-2 bg-dex-accent text-white rounded-xl text-sm font-medium hover:opacity-90 transition-opacity flex items-center gap-2 shadow-sm">
          <Plus size={16} /> New Note
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 overflow-y-auto pb-8">
        {loading ? (
          <div className="col-span-full text-center animate-pulse py-12">Retrieving archives...</div>
        ) : notes.length === 0 ? (
          <div className="col-span-full py-24 text-center opacity-40 border-2 border-dashed border-dex-border rounded-3xl">
             <StickyNote size={48} className="mx-auto mb-4" />
             <p className="text-sm font-medium">No notes recorded in the current data directory.</p>
          </div>
        ) : (
          notes.map((note, i) => (
            <div key={i} className="card p-6 flex flex-col gap-4 group cursor-pointer hover:border-dex-accent/30 transition-all shadow-sm bg-white">
               <div className="flex items-center justify-between">
                  <div className="p-2 bg-dex-bg rounded-lg text-dex-text-secondary group-hover:text-dex-accent transition-colors">
                     <FileText size={18} />
                  </div>
                  <span className="text-[10px] font-mono text-dex-text-secondary uppercase">Markdown</span>
               </div>
               
               <div>
                  <h4 className="text-sm font-bold text-dex-text-primary mb-2 truncate">{note.filename}</h4>
                  <p className="text-xs text-dex-text-secondary leading-relaxed line-clamp-4 font-serif italic">
                     "{note.content}"
                  </p>
               </div>

               <div className="pt-4 border-t border-dex-bg mt-auto flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-[10px] text-dex-text-secondary">
                     <Clock size={12}/> Recent
                  </div>
                  <ChevronRight size={14} className="text-dex-text-secondary opacity-0 group-hover:opacity-100 transition-opacity" />
               </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
