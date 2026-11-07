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
    <>
      <MobileHeader
        title="AI Scout"
        rightElement={
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
            <Sparkles className="h-4 w-4" />
          </div>
        }
      />

      {/* Conversation Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-emerald-600 text-white rounded-br-sm'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm shadow-sm'
              }`}
            >
              {msg.content}
            </div>

            {/* Tool result cards */}
            {msg.tools?.map((tool, tIdx) => (
              <div key={tIdx} className="mt-2 w-full max-w-[92%] space-y-2">
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
            Checking live slots…
          </div>
        )}
      </div>

      {/* Quick prompts */}
      <div className="flex gap-2 overflow-x-auto px-4 py-2 border-t border-slate-100 no-scrollbar flex-shrink-0">
        {QUICK_PROMPTS.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setInput(p)}
            className="whitespace-nowrap rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 flex-shrink-0 transition-colors"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input */}
      <form
        onSubmit={handleSend}
        className="flex items-center gap-2 border-t border-slate-200 px-4 py-3 pb-4 flex-shrink-0 bg-white"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for pitches, lobbies, or announcements…"
          className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm focus:border-emerald-500 focus:bg-white focus:outline-none"
        />
        <button
          type="submit"
          disabled={chatMutation.isPending || !input.trim()}
          className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white disabled:opacity-40 hover:bg-emerald-700 flex-shrink-0"
        >
          {chatMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </form>
    </>
  );
};

export default AIAssistantPage;

