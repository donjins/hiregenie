import React, { useState, useRef, useEffect } from 'react';
import { chatService } from '../services/api';
import { Send, Sparkles, User, Bot, Loader } from 'lucide-react';

interface Message {
  sender: 'recruiter' | 'assistant';
  text: string;
  timestamp: Date;
}

export const ChatAssistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'assistant',
      text: "Hello! I am HireGenie's recruitment AI assistant. I can fetch candidate stats, screen matching scores, generate interview questions, book available time slots, and dispatch templates.\n\nTry asking me:\n- *\"Show me the top 5 Python developers\"*\n- *\"Rank candidates with more than 3 years of React experience\"*\n- *\"Which applicants match this job above 85%?\"*\n- *\"Schedule an interview with John for tomorrow afternoon\"*\n- *\"What is the company policy for interview travel reimbursement?\"*",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim()) return;
    
    // Add Recruiter message
    const newMsg: Message = { sender: 'recruiter', text: textToSend, timestamp: new Date() };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await chatService.sendMessage(textToSend);
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: res.response,
        timestamp: new Date()
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: "I encountered an issue trying to process that query. Please make sure the backend is active.",
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "Show me the top five Python developers",
    "Rank candidates with more than 3 years of React experience",
    "Which applicants match this job above 85%?",
    "Schedule an interview with John Doe for tomorrow afternoon",
    "What is the policy for interview travel reimbursement?"
  ];

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col bg-white dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/40 rounded-2xl shadow-sm overflow-hidden transition-colors">
      {/* Header */}
      <div className="p-5 border-b border-slate-100 dark:border-slate-800/60 flex items-center justify-between bg-slate-50/50 dark:bg-slate-950/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 text-white flex items-center justify-center shadow shadow-brand-500/10">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-outfit font-bold text-base text-slate-800 dark:text-white">AI Recruiting Assistant</h2>
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">LangChain Orchestrated</span>
          </div>
        </div>
        <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-400 px-3 py-1 rounded-full animate-pulse">
          Agent Online
        </span>
      </div>

      {/* Messages Canvas */}
      <div className="flex-1 p-6 overflow-y-auto space-y-6">
        {messages.map((msg, idx) => (
          <div 
            key={idx} 
            className={`flex items-start gap-4 ${msg.sender === 'recruiter' ? 'justify-end' : ''}`}
          >
            {msg.sender === 'assistant' && (
              <div className="w-9 h-9 rounded-xl bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 flex items-center justify-center shrink-0 shadow-sm border border-brand-100 dark:border-brand-900/50">
                <Bot className="w-5 h-5" />
              </div>
            )}
            
            <div className={`max-w-[70%] p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
              msg.sender === 'recruiter'
                ? 'bg-gradient-to-tr from-brand-600 to-indigo-600 text-white shadow-md shadow-brand-500/5 rounded-tr-none'
                : 'bg-slate-50 dark:bg-slate-800/40 text-slate-800 dark:text-slate-200 rounded-tl-none border border-slate-100 dark:border-slate-800/60'
            }`}>
              {msg.text}
              <span className={`text-[10px] block mt-2 text-right ${msg.sender === 'recruiter' ? 'text-white/60' : 'text-slate-400'}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            {msg.sender === 'recruiter' && (
              <div className="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 shadow-sm border border-indigo-100 dark:border-indigo-900/50">
                <User className="w-5 h-5" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-start gap-4">
            <div className="w-9 h-9 rounded-xl bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 flex items-center justify-center shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div className="bg-slate-50 dark:bg-slate-800/40 p-4 rounded-2xl rounded-tl-none flex items-center gap-2 border border-slate-100 dark:border-slate-800/60">
              <Loader className="w-4 h-4 animate-spin text-brand-600" />
              <span className="text-xs text-slate-400 font-semibold animate-pulse-slow">Agent thinking...</span>
            </div>
          </div>
        )}
        <div ref={scrollRef}></div>
      </div>

      {/* Quick Suggestions list */}
      <div className="px-6 py-3 border-t border-slate-100 dark:border-slate-800/40 bg-slate-50/20 flex gap-2 overflow-x-auto whitespace-nowrap">
        {suggestions.map((sug, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(sug)}
            className="text-[11px] font-bold text-slate-500 hover:text-brand-600 dark:text-slate-400 dark:hover:text-brand-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1.5 rounded-full hover:border-brand-300 dark:hover:border-brand-500 transition-colors shadow-sm"
          >
            {sug}
          </button>
        ))}
      </div>

      {/* Input controls */}
      <div className="p-4 border-t border-slate-100 dark:border-slate-800/60 bg-white dark:bg-slate-900">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type recruiter instructions or query..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
            className="flex-1 px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
          />
          <button
            onClick={() => handleSend(input)}
            className="px-5 py-3 bg-gradient-to-tr from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white rounded-xl flex items-center justify-center shadow-md active:scale-95 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
