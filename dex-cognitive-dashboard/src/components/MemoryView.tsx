import React, { useState, useEffect } from 'react';
import { Search, FileText, ChevronRight, MoreVertical, Database } from 'lucide-react';
import { searchMemory } from '../lib/api';

export const MemoryView: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsStreaming] = useState(false);

  const handleSearch = async (val: string) => {
    setQuery(val);
    if (val.length < 2) {
      setResults([]);
      return;
    }
    
    setIsStreaming(true);
    try {
      const data = await searchMemory(val);
      setResults(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-160px)] border-t border-dex-border fade-in">
      {/* Left Sidebar: Memory Tree */}
      <div className="w-80 border-r border-dex-border flex flex-col bg-white">
        <div className="p-4 border-b border-dex-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-dex-text-secondary" size={14} />
            <input 
              type="text" 
              value={query}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search local memory..." 
              className="w-full bg-dex-bg border border-dex-border rounded-lg pl-9 pr-4 py-2 text-xs outline-none focus:border-dex-accent transition-colors"
            />
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <div>
            <span className="text-[10px] font-bold text-dex-text-secondary uppercase tracking-widest block mb-4">Semantic Matches</span>
            <div className="space-y-1">
              {results.length === 0 ? (
                <div className="text-[11px] text-dex-text-secondary italic px-2">
                  {query.length > 1 ? 'No matches found.' : 'Enter a query to search...'}
                </div>
              ) : (
                results.map((res, i) => (
                  <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-md text-xs hover:bg-dex-sidebar-hover cursor-pointer text-dex-text-primary border border-transparent hover:border-dex-border">
                    <Database size={12} className="text-dex-accent opacity-60" />
                    <span className="line-clamp-1">{res.content}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Right Content: Memory Panel */}
      <div className="flex-1 bg-dex-bg overflow-y-auto p-8">
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight">Intelligence Graph</h2>
            
            {results.length > 0 ? (
              results.map((res, i) => (
                <div key={i} className="card p-6 space-y-4 fade-in">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-dex-text-secondary">
                      <FileText size={14} />
                      <span className="text-[10px] font-bold uppercase tracking-widest">Entry ID: {res.id}</span>
                    </div>
                    <span className="text-[10px] font-mono text-dex-accent">Score: {(res.score * 100).toFixed(1)}%</span>
                  </div>
                  <p className="text-sm text-dex-text-primary leading-relaxed">
                    {res.content}
                  </p>
                  <div className="flex flex-wrap gap-2 pt-2">
                    {Object.entries(res.metadata).map(([k, v]: [any, any]) => (
                      <span key={k} className="px-2 py-0.5 bg-dex-sidebar-hover border border-dex-border rounded text-[10px] text-dex-text-secondary">
                        {k}: {String(v)}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="py-24 text-center text-dex-text-secondary opacity-40">
                <Database size={48} className="mx-auto mb-4" />
                <p className="text-sm font-medium">Global Knowledge Base</p>
                <p className="text-xs">Search for topics or tasks to retrieve context.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
