import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import MobileHeader from '../components/layout/MobileHeader';
import DateScroller from '../components/booking/DateScroller';
import TimeSlotSelector from '../components/booking/TimeSlotSelector';
import BookingDrawer from '../components/booking/BookingDrawer';
import { usePitch } from '../api/venues';
import { usePitchAvailability, useCreateBooking } from '../api/bookings';
import { TimeSlot, BookingCreatePayload } from '../types/api';

const PitchDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const today = new Date().toISOString().slice(0, 10);
  const [selectedDate, setSelectedDate] = useState(today);
  const [drawerSlot, setDrawerSlot] = useState<TimeSlot | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const pitchId = id ?? '';
  const { data: pitch, isLoading: pitchLoading, isError: pitchError } = usePitch(pitchId);
  const { data: slots = [], isLoading: slotsLoading, isError: slotsError } = usePitchAvailability(
    pitchId,
    selectedDate
  );
  const createBooking = useCreateBooking(pitchId, selectedDate);

  const handleSelectAvailableSlot = (slot: TimeSlot) => {
    setDrawerSlot(slot);
  };

  const handleSelectOpenLobby = (matchId: string) => {
    navigate(`/matches?highlight=${matchId}`);
  };

  const handleConfirmBooking = (payload: BookingCreatePayload) => {
    createBooking.mutate(payload, {
      onSuccess: () => {
        setDrawerSlot(null);
        setSuccessMessage(
          payload.create_open_lobby
            ? '🏆 Booking confirmed! Open lobby created.'
            : '✅ Pitch booked successfully!'
        );
        setTimeout(() => setSuccessMessage(null), 4000);
      },
      onError: () => {
        setDrawerSlot(null);
      },
    });
  };

  if (pitchLoading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-20 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        <p className="text-sm text-slate-500">Loading pitch details…</p>
      </div>
    );
  }

  if (pitchError || !pitch) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-20 gap-2">
        <AlertCircle className="w-8 h-8 text-red-400" />
        <p className="text-sm font-medium text-red-500">Pitch not found</p>
      </div>
    );
  }

  return (
    <>
      <MobileHeader title={pitch.name} showBack />

      {/* Success toast */}
      {successMessage && (
        <div className="mx-4 mt-3 flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-sm font-medium text-emerald-800">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          {successMessage}
        </div>
      )}

      {/* Pitch info banner */}
      <div className="mx-4 mt-3 bg-white border border-slate-200 rounded-2xl p-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs text-slate-500 font-medium">{pitch.surface_type.replace(/_/g, ' ')}</p>
            <p className="text-sm font-bold text-slate-900 mt-0.5">
              {pitch.team_size_capacity}v{pitch.team_size_capacity} · {pitch.name}
            </p>
          </div>
          <div className="text-right">
            <span className="text-lg font-bold text-slate-900">{pitch.hourly_rate}</span>
            <span className="text-xs text-slate-500"> RON/h</span>
          </div>
        </div>
      </div>

      {/* Date scroller */}
      <DateScroller selectedDate={selectedDate} onDateChange={setSelectedDate} />

      {/* Slot grid */}
      <div className="flex-1 px-4 py-4">
        {slotsLoading ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
            <p className="text-sm text-slate-400">Loading availability…</p>
          </div>
        ) : slotsError ? (
          <div className="flex flex-col items-center justify-center py-12 gap-2 text-slate-400">
            <AlertCircle className="w-7 h-7 text-red-400" />
            <p className="text-sm font-medium text-red-400">Could not load slots</p>
          </div>
        ) : (
          <TimeSlotSelector
            slots={slots}
            onSelectAvailableSlot={handleSelectAvailableSlot}
            onSelectOpenLobby={handleSelectOpenLobby}
          />
        )}
      </div>

      {/* Booking drawer */}
      <BookingDrawer
        isOpen={Boolean(drawerSlot)}
        slot={drawerSlot}
        pitchId={pitchId}
        pitchName={pitch.name}
        venueName={pitch.venue_id}
        onClose={() => setDrawerSlot(null)}
        onConfirm={handleConfirmBooking}
        isLoading={createBooking.isPending}
      />
    </>
  );
};

export default PitchDetailPage;
