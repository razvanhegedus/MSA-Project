import React, { useId, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';

interface DateScrollerProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
  daysAhead?: number;
  title?: string;
  allowDateJump?: boolean;
}

const fullDateFormat = new Intl.DateTimeFormat('en-GB', { dateStyle: 'full' });

function formatLocalDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function startNear(date: string, today: string) {
  const start = new Date(`${date}T12:00:00`);
  start.setDate(start.getDate() - 2);
  const candidate = formatLocalDate(start);
  return candidate > today ? candidate : today;
}

const DateScroller: React.FC<DateScrollerProps> = ({
  selectedDate,
  onDateChange,
  daysAhead = 14,
  title = 'Select Match Date',
  allowDateJump = false,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const today = formatLocalDate(new Date());
  const [windowStart, setWindowStart] = useState(() => startNear(selectedDate, today));
  const start = allowDateJump && windowStart > today ? windowStart : today;

  const dates = Array.from({ length: daysAhead }, (_, index) => {
    const date = new Date(`${start}T12:00:00`);
    date.setDate(date.getDate() + index);
    return date;
  });

  const scroll = (direction: 'left' | 'right') => {
    scrollRef.current?.scrollBy({
      left: direction === 'left' ? -220 : 220,
      behavior: 'smooth',
    });
  };

  const jumpTo = (date: string) => {
    if (!date || date < today) return;
    setWindowStart(startNear(date, today));
    scrollRef.current?.scrollTo({ left: 0, behavior: 'instant' });
    onDateChange(date);
  };

  return (
    <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
      <div className="mb-3 flex items-center justify-between gap-2 px-1">
        <div className="flex items-center gap-2">
          <CalendarIcon className="h-4 w-4 shrink-0 text-emerald-600" />
          <h3 id={titleId} className="text-xs font-bold uppercase tracking-wider text-slate-900">
            {title}
          </h3>
        </div>
        <div className={`shrink-0 items-center gap-1.5 ${allowDateJump ? 'flex' : 'hidden sm:flex'}`}>
          <button
            type="button"
            onClick={() => scroll('left')}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800"
            aria-label="Previous days"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => scroll('right')}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800"
            aria-label="Next days"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        role="group"
        aria-labelledby={titleId}
        className="no-scrollbar flex gap-2.5 overflow-x-auto scroll-smooth px-0.5 py-1"
      >
        {dates.map((date) => {
          const iso = formatLocalDate(date);
          const isActive = iso === selectedDate;

          return (
            <button
              key={iso}
              type="button"
              aria-label={fullDateFormat.format(date)}
              aria-pressed={isActive}
              onClick={() => onDateChange(iso)}
              className={`flex min-w-[62px] shrink-0 flex-col items-center justify-center rounded-xl border px-3.5 py-2.5 transition-all active:scale-95 sm:min-w-[70px] sm:px-4 ${isActive
                ? 'border-slate-900 bg-slate-900 text-white shadow-md ring-2 ring-slate-900/10'
                : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300 hover:bg-slate-100'
              }`}
            >
              <span className={`text-[10px] font-bold uppercase tracking-wider ${isActive ? 'text-emerald-400' : 'text-slate-400'}`}>
                {iso === today ? 'Today' : date.toLocaleDateString('en-GB', { weekday: 'short' })}
              </span>
              <span className={`my-0.5 text-base font-black leading-tight sm:text-lg ${isActive ? 'text-white' : 'text-slate-900'}`}>
                {date.getDate()}
              </span>
              <span className={`text-[10px] font-medium ${isActive ? 'text-slate-300' : 'text-slate-400'}`}>
                {date.toLocaleDateString('en-GB', { month: 'short' })}
              </span>
            </button>
          );
        })}
      </div>

      {allowDateJump && (
        <label className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-slate-100 pt-3 text-xs font-semibold text-slate-600">
          Jump to date
          <input
            type="date"
            min={today}
            value={selectedDate}
            onChange={(event) => jumpTo(event.target.value)}
            className="min-w-0 max-w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-800 disabled:opacity-50"
          />
        </label>
      )}
    </div>
  );
};

export default DateScroller;
