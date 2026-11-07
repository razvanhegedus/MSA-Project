import React, { useRef } from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';

interface DateScrollerProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
  daysAhead?: number;
}

const DateScroller: React.FC<DateScrollerProps> = ({
  selectedDate,
  onDateChange,
  daysAhead = 14,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const dates = Array.from({ length: daysAhead }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() + i);
    return d;
  });

  const formatLocalDate = (d: Date) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const formatDay = (d: Date) =>
    d.toLocaleDateString('en-GB', { weekday: 'short' });

  const formatMonth = (d: Date) =>
    d.toLocaleDateString('en-GB', { month: 'short' });

  const formatDate = (d: Date) => d.getDate();

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const offset = direction === 'left' ? -220 : 220;
      scrollRef.current.scrollBy({ left: offset, behavior: 'smooth' });
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-3 sm:p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <CalendarIcon className="w-4 h-4 text-emerald-600" />
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Select Match Date
          </h3>
        </div>

        {/* Desktop Prev/Next Controls */}
        <div className="hidden sm:flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => scroll('left')}
            className="w-7 h-7 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors"
            aria-label="Previous days"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => scroll('right')}
            className="w-7 h-7 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors"
            aria-label="Next days"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Date Ribbon */}
      <div
        ref={scrollRef}
        className="flex gap-2.5 overflow-x-auto no-scrollbar scroll-smooth py-1 px-0.5"
      >
        {dates.map((d) => {
          const iso = formatLocalDate(d);
          const isActive = iso === selectedDate;
          const isToday = iso === formatLocalDate(new Date());

          return (
            <button
              key={iso}
              type="button"
              onClick={() => onDateChange(iso)}
              className={`flex-shrink-0 flex flex-col items-center justify-center py-2.5 px-3.5 sm:px-4 rounded-xl min-w-[62px] sm:min-w-[70px] border transition-all active:scale-95 ${
                isActive
                  ? 'bg-slate-900 text-white border-slate-900 shadow-md ring-2 ring-slate-900/10'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100 hover:border-slate-300'
              }`}
            >
              <span
                className={`text-[10px] font-bold uppercase tracking-wider ${
                  isActive ? 'text-emerald-400' : 'text-slate-400'
                }`}
              >
                {isToday ? 'Today' : formatDay(d)}
              </span>
              <span
                className={`text-base sm:text-lg font-black leading-tight my-0.5 ${
                  isActive ? 'text-white' : 'text-slate-900'
                }`}
              >
                {formatDate(d)}
              </span>
              <span
                className={`text-[10px] font-medium ${
                  isActive ? 'text-slate-300' : 'text-slate-400'
                }`}
              >
                {formatMonth(d)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default DateScroller;
