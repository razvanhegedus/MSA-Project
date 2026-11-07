import React from 'react';
import { Users, Lock, CheckCircle2 } from 'lucide-react';
import { TimeSlot } from '../../types/api';

interface TimeSlotSelectorProps {
  slots: TimeSlot[];
  selectedSlot?: TimeSlot | null;
  onSelectAvailableSlot: (slot: TimeSlot) => void;
  onSelectOpenLobby: (matchId: string) => void;
}

const TimeSlotSelector: React.FC<TimeSlotSelectorProps> = ({
  slots,
  selectedSlot,
  onSelectAvailableSlot,
  onSelectOpenLobby,
}) => {
  const formatHour = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  if (slots.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-400 bg-white rounded-2xl border border-slate-200 p-8">
        <Lock className="w-8 h-8 mb-2 opacity-40" />
        <p className="text-sm font-medium">No slots available for this date</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex flex-wrap items-center justify-between text-xs font-medium text-slate-600 bg-white border border-slate-200 p-3 rounded-2xl shadow-sm gap-2">
        <span className="flex items-center gap-1.5 font-semibold text-emerald-800">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block shadow-sm" /> Available
        </span>
        <span className="flex items-center gap-1.5 font-semibold text-amber-800">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block shadow-sm" /> Open Lobby (+1)
        </span>
        <span className="flex items-center gap-1.5 font-semibold text-slate-400">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-300 inline-block" /> Occupied
        </span>
      </div>

      {/* Responsive Grid: 3 cols on mobile, 4 on sm/md, 5 on lg, 6 on xl */}
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2.5">
        {slots.map((slot) => {
          const isSelected = selectedSlot?.start_time === slot.start_time;
          const timeLabel = `${formatHour(slot.start_time)}–${formatHour(slot.end_time)}`;

          if (slot.status === 'OCCUPIED') {
            return (
              <button
                key={slot.start_time}
                disabled
                className="flex flex-col items-center justify-center p-3 rounded-xl bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed opacity-60 select-none"
                aria-label={`${timeLabel} – Booked`}
              >
                <span className="text-xs font-semibold line-through">{timeLabel}</span>
                <span className="mt-1 flex items-center gap-1 text-[11px]">
                  <Lock className="w-3 h-3" /> Booked
                </span>
              </button>
            );
          }

          if (slot.status === 'OPEN_LOBBY') {
            return (
              <button
                key={slot.start_time}
                onClick={() => slot.open_match_id && onSelectOpenLobby(slot.open_match_id)}
                className="flex flex-col items-center justify-center p-3 rounded-xl bg-amber-50 text-amber-900 border border-amber-300 ring-1 ring-amber-400/40 hover:bg-amber-100/80 active:scale-[0.98] transition cursor-pointer shadow-sm"
                aria-label={`${timeLabel} – Open Lobby, ${slot.spots_left ?? 0} spots left`}
              >
                <span className="text-xs font-bold">{timeLabel}</span>
                <span className="mt-1 flex items-center gap-1 text-[11px] font-semibold text-amber-700">
                  <Users className="w-3.5 h-3.5" />
                  +{slot.spots_left ?? '?'} needed
                </span>
              </button>
            );
          }

          // AVAILABLE
          return (
            <button
              key={slot.start_time}
              onClick={() => onSelectAvailableSlot(slot)}
              className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all active:scale-[0.98] cursor-pointer shadow-sm ${
                isSelected
                  ? 'border-emerald-600 bg-emerald-600 text-white shadow-md ring-2 ring-emerald-500/30'
                  : 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:border-emerald-500 hover:bg-emerald-100/70'
              }`}
              aria-label={`${timeLabel} – Available, ${slot.price} RON`}
            >
              <span className="text-xs font-bold">{timeLabel}</span>
              <span
                className={`mt-1 flex items-center gap-1 text-[11px] font-semibold ${
                  isSelected ? 'text-emerald-100' : 'text-emerald-700'
                }`}
              >
                {isSelected && <CheckCircle2 className="w-3 h-3" />}
                {slot.price} RON
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default TimeSlotSelector;
