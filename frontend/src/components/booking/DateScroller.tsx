import React from 'react';

interface DateScrollerProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
  daysAhead?: number;
}

const DateScroller: React.FC<DateScrollerProps> = ({
  selectedDate,
  onDateChange,
  daysAhead = 7,
}) => {
  const dates = Array.from({ length: daysAhead }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() + i);
    return d;
  });

  const toIso = (d: Date) => d.toISOString().slice(0, 10);

  const formatDay = (d: Date) =>
    d.toLocaleDateString('en-GB', { weekday: 'short' }).toUpperCase();

  const formatDate = (d: Date) => d.getDate();

  return (
    <div className="sticky top-[53px] z-20 bg-white/95 backdrop-blur-sm border-b border-slate-200">
      <div className="flex gap-2 overflow-x-auto no-scrollbar py-2.5 px-4">
        {dates.map((d) => {
          const iso = toIso(d);
          const isActive = iso === selectedDate;
          const isToday = iso === toIso(new Date());

          return (
            <button
              key={iso}
              onClick={() => onDateChange(iso)}
              className={`flex-shrink-0 flex flex-col items-center px-3.5 py-2 rounded-xl min-w-[52px] transition-all active:scale-95 ${
                isActive
                  ? 'bg-slate-900 text-white font-semibold shadow-sm'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
              }`}
            >
              <span className="text-[10px] font-semibold tracking-wide">
                {isToday ? 'TODAY' : formatDay(d)}
              </span>
              <span className={`text-lg font-bold leading-tight ${isActive ? 'text-white' : 'text-slate-900'}`}>
                {formatDate(d)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default DateScroller;

