import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Loader2, Calendar, Users, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import MobileHeader from '../components/layout/MobileHeader';
import { useAIChat } from '../api/ai';
import { AIChatHistoryMessage, ToolCallPayload } from '../types/api';

interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
  tools?: ToolCallPayload[];
}

const QUICK_PROMPTS = [
  'Find me a 3G pitch tomorrow at 20:00',
  'Open lobbies needing a goalkeeper',
  'Draft a +1 announcement for 7v7 tonight',
  'Pitches available this Saturday',
];

const AIAssistantPage: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatTurn[]>([
    {
      role: 'assistant',
      content:
        'Salut! 👋 I\'m your AI Football Concierge. I can search available pitches in real time, find open lobbies needing players, and help you write catchy +1 announcements. What can I do for you?',
    },
  ]);
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement>(null);
  const chatMutation = useAIChat();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, chatMutation.isPending]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || chatMutation.isPending) return;

    const newMessages: ChatTurn[] = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setInput('');

    const history: AIChatHistoryMessage[] = newMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    chatMutation.mutate(
      { message: text, history },
      {
        onSuccess: (data) => {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: data.reply, tools: data.invoked_tools },
          ]);
        },
      }
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col h-[82vh] bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <MobileHeader
        title="AI Scout"
        rightElement={
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
            <Sparkles className="h-4 w-4" />
          </div>
        }
      />

      {/* Desktop Top Header Bar inside the card */}
      <div className="hidden lg:flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center text-white shadow-sm">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">AI Concierge & Matchmaker</h2>
            <p className="text-xs text-slate-500">Autonomous live pitch queries and squad formation</p>
          </div>
        </div>
        <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
          Connected to Live PG Database
        </span>
      </div>

      {/* Conversation Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-emerald-600 text-white rounded-br-sm'
                  : 'bg-slate-100 text-slate-800 rounded-bl-sm border border-slate-200/50 shadow-sm'
              }`}
            >
              {msg.content}
            </div>

            {/* Tool result cards */}
            {msg.tools?.map((tool, tIdx) => (
              <div key={tIdx} className="mt-2 w-full max-w-[85%] sm:max-w-[75%] space-y-2">
                {tool.tool_name === 'search_pitches' &&
                  tool.result_summary.map((pitch, pIdx) => (
                    <div
                      key={pIdx}
                      onClick={() => {
                        if (typeof pitch.pitch_id === 'string') {
                          navigate(`/pitches/${pitch.pitch_id}`);
                        }
                      }}
                      className="flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50 p-3 cursor-pointer hover:bg-emerald-100/60 active:scale-[0.98] transition-all"
                    >
                      <div>
                        <p className="text-xs font-bold text-emerald-950">
                          {String(pitch.venue_name ?? '')} — {String(pitch.pitch_name ?? '')}
                        </p>
                        <p className="text-[11px] text-emerald-700 flex items-center gap-1 mt-0.5">
                          <Calendar className="w-3 h-3" />
                          {String(pitch.slot ?? '')} · {String(pitch.hourly_rate ?? '')} RON/h
                        </p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    </div>
                  ))}

                {tool.tool_name === 'find_open_lobbies' &&
                  tool.result_summary.map((lobby, lIdx) => (
                    <div
                      key={lIdx}
                      onClick={() => {
                        if (typeof lobby.match_id === 'string') {
                          navigate(`/matches?highlight=${lobby.match_id}`);
                        }
                      }}
                      className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 p-3 cursor-pointer hover:bg-amber-100/60 active:scale-[0.98] transition-all"
                    >
                      <div>
                        <p className="text-xs font-bold text-amber-950">
                          {String(lobby.venue_name ?? '')} ({String(lobby.spots_left ?? '?')} spots left)
                        </p>
                        <p className="text-[11px] text-amber-800 flex items-center gap-1 mt-0.5">
                          <Users className="w-3 h-3" />
                          Needed:{' '}
                          {Array.isArray(lobby.needed_positions) && lobby.needed_positions.length > 0
                            ? (lobby.needed_positions as string[]).join(', ')
                            : 'Any Player'}
                        </p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-amber-600 flex-shrink-0" />
                    </div>
                  ))}
              </div>
            ))}
          </div>
        ))}

        {chatMutation.isPending && (
          <div className="flex items-center gap-2 text-xs text-slate-400 pl-2">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-emerald-500" />
            Analyzing pitch calendar & lobbies…
          </div>
        )}
      </div>

      {/* Quick prompts */}
      <div className="flex gap-2 overflow-x-auto px-4 py-2 border-t border-slate-100 no-scrollbar flex-shrink-0 bg-slate-50/50">
        {QUICK_PROMPTS.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setInput(p)}
            className="whitespace-nowrap rounded-full bg-white border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300 flex-shrink-0 transition-colors shadow-2xs"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input */}
      <form
        onSubmit={handleSend}
        className="flex items-center gap-2 border-t border-slate-200 px-4 py-3 bg-white flex-shrink-0"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for available pitches, goalkeeper-needed lobbies, or match posts…"
          className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-xs sm:text-sm focus:border-emerald-500 focus:bg-white focus:outline-none transition-all"
        />
        <button
          type="submit"
          disabled={chatMutation.isPending || !input.trim()}
          className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white disabled:opacity-40 hover:bg-emerald-700 flex-shrink-0 shadow-sm transition-all"
        >
          {chatMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </form>
    </div>
  );
};

export default AIAssistantPage;
