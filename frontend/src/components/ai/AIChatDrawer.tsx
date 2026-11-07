import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, X, Send, Calendar, Users, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAIChat } from '../../api/ai';
import { AIChatHistoryMessage, ToolCallPayload } from '../../types/api';

interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
  tools?: ToolCallPayload[];
}

const QUICK_PROMPTS = [
  'Free 3G pitches tonight at 20:00',
  'Lobbies needing a Goalkeeper',
  'Write a +1 announcement for 6v6',
];

const AIChatDrawer: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatTurn[]>([
    {
      role: 'assistant',
      content: 'Salut! 👋 Looking for a free pitch tonight or need an extra player (+1) for your squad?',
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

  const handleQuickPrompt = (prompt: string) => {
    setInput(prompt);
  };

  const getSummaryItems = (tool: ToolCallPayload) => {
    return tool.result_summary;
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          aria-label="Open AI Football Concierge"
          className="fixed bottom-20 right-4 lg:bottom-8 lg:right-8 z-40 flex items-center gap-2 rounded-full bg-emerald-600 px-4 py-3.5 text-white shadow-xl hover:bg-emerald-700 active:scale-95 transition-all"
        >
          <Sparkles className="w-5 h-5" />
          <span className="text-sm font-semibold">AI Scout</span>
        </button>
      )}

      {/* Slide-Up Bottom Sheet on Mobile, Floating Drawer on Desktop */}
      {isOpen && (
        <div className="fixed inset-0 lg:inset-auto lg:bottom-8 lg:right-8 z-50 flex flex-col justify-end lg:justify-start bg-black/50 lg:bg-transparent backdrop-blur-sm lg:backdrop-blur-none pointer-events-auto">
          <div className="max-w-md mx-auto w-full flex h-[82vh] lg:h-[620px] lg:w-[420px] flex-col rounded-t-3xl lg:rounded-2xl bg-white shadow-2xl border border-slate-200">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 flex-shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">AI Matchmaking Assistant</h3>
                  <p className="text-xs text-slate-500">Live pitch & lobby search</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Conversation Stream */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-emerald-600 text-white rounded-br-sm'
                        : 'bg-slate-100 text-slate-800 rounded-bl-sm'
                    }`}
                  >
                    {msg.content}
                  </div>

                  {/* Interactive Tool Result Cards */}
                  {msg.tools?.map((tool, tIdx) => (
                    <div key={tIdx} className="mt-2 w-full max-w-[90%] space-y-2">
                      {tool.tool_name === 'search_pitches' &&
                        getSummaryItems(tool).map((pitch, pIdx) => (
                          <div
                            key={pIdx}
                            onClick={() => {
                              setIsOpen(false);
                              if (typeof pitch.pitch_id === 'string') {
                                navigate(`/pitches/${pitch.pitch_id}`);
                              }
                            }}
                            className="flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 cursor-pointer hover:bg-emerald-100/60"
                          >
                            <div>
                              <p className="text-xs font-bold text-emerald-950">
                                {String(pitch.venue_name ?? '')} — {String(pitch.pitch_name ?? '')}
                              </p>
                              <p className="text-[11px] text-emerald-700 flex items-center gap-1 mt-0.5">
                                <Calendar className="w-3 h-3" />
                                {String(pitch.slot ?? '')} • {String(pitch.hourly_rate ?? '')} RON/h
                              </p>
                            </div>
                            <ArrowRight className="w-4 h-4 text-emerald-600" />
                          </div>
                        ))}

                      {tool.tool_name === 'find_open_lobbies' &&
                        getSummaryItems(tool).map((lobby, lIdx) => (
                          <div
                            key={lIdx}
                            onClick={() => {
                              setIsOpen(false);
                              if (typeof lobby.match_id === 'string') {
                                navigate(`/matches?highlight=${lobby.match_id}`);
                              }
                            }}
                            className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 p-3 cursor-pointer hover:bg-amber-100/60"
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
                            <ArrowRight className="w-4 h-4 text-amber-600" />
                          </div>
                        ))}
                    </div>
                  ))}
                </div>
              ))}

              {chatMutation.isPending && (
                <div className="flex items-center gap-2 text-xs text-slate-400 pl-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                  Checking live database slots…
                </div>
              )}
            </div>

            {/* Quick Prompt Chips */}
            <div className="flex gap-2 overflow-x-auto px-4 py-2 border-t border-slate-100 no-scrollbar flex-shrink-0">
              {QUICK_PROMPTS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => handleQuickPrompt(suggestion)}
                  className="whitespace-nowrap rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 flex-shrink-0"
                >
                  {suggestion}
                </button>
              ))}
            </div>

            {/* Input Form */}
            <form
              onSubmit={handleSend}
              className="flex items-center gap-2 border-t border-slate-200 p-3 pb-6 flex-shrink-0"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask for pitches, open lobbies, or announcements…"
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm focus:border-emerald-500 focus:bg-white focus:outline-none"
              />
              <button
                type="submit"
                disabled={chatMutation.isPending || !input.trim()}
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white disabled:opacity-40 hover:bg-emerald-700"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default AIChatDrawer;

