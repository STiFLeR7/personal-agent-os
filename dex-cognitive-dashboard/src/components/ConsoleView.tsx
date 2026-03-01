import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { ExecutionResult } from '../types';
import { runTask } from '../lib/api';
import Markdown from 'react-markdown';

export const ConsoleView: React.FC = () => {
  const [input, setInput] = useState('');
  const [results, setResults] = useState<ExecutionResult[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [results]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const newResult: ExecutionResult = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      command: input,
      output: '',
      status: 'pending',
    };

    setResults(prev => [...prev, newResult]);
    setInput('');
    setIsStreaming(true);

    try {
      const startTime = Date.now();
      const response = await runTask(input);
      
      const latency = Date.now() - startTime;
      
      setResults(prev => prev.map(r => 
        r.id === newResult.id 
          ? { ...r, output: response.message || 'Task accepted and running...', status: 'success', latency } 
          : r
      ));
    } catch (error) {
      console.error('API Error:', error);
      setResults(prev => prev.map(r => 
        r.id === newResult.id 
          ? { ...r, output: 'Failed to connect to Dex backend. Please ensure the server is running.', status: 'error' } 
          : r
      ));
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto px-8 py-6">
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-6 pb-24 scroll-smooth">
        {results.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-40">
            <div className="w-12 h-12 rounded-2xl border-2 border-dashed border-dex-text-secondary flex items-center justify-center">
              <span className="text-xl font-bold">?</span>
            </div>
            <div>
              <p className="text-sm font-medium">No commands executed yet</p>
              <p className="text-xs">Ask Dex to analyze data, summarize notes, or manage tasks.</p>
            </div>
          </div>
        )}
        
        <AnimatePresence initial={false}>
          {results.map((result) => (
            <motion.div
              key={result.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              <div className="flex items-center gap-3 text-dex-text-secondary">
                <span className="text-[10px] font-mono uppercase tracking-widest">{result.timestamp}</span>
                <div className="h-[1px] flex-1 bg-dex-border" />
                {result.latency && (
                  <span className="text-[10px] font-mono">{result.latency}ms</span>
                )}
              </div>
              
              <div className="pl-4 border-l-2 border-dex-border">
                <p className="text-sm font-medium text-dex-text-primary">{result.command}</p>
              </div>

              <div className="card bg-white shadow-sm">
                {result.status === 'pending' ? (
                  <div className="flex items-center gap-2 text-dex-text-secondary py-2">
                    <Loader2 size={14} className="animate-spin" />
                    <span className="text-xs">Thinking...</span>
                  </div>
                ) : (
                  <div className="prose prose-sm max-w-none text-dex-text-primary leading-relaxed">
                    <Markdown>{result.output}</Markdown>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div className="fixed bottom-8 left-[calc(240px+50%)] -translate-x-1/2 w-full max-w-2xl px-8">
        <div className="glass rounded-2xl p-2 shadow-2xl shadow-black/5 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask Dex to do something..."
            className="flex-1 bg-transparent border-none outline-none px-4 py-2 text-sm placeholder:text-dex-text-secondary"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="w-10 h-10 bg-dex-accent text-white rounded-xl flex items-center justify-center hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStreaming ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
};
