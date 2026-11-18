import { useEffect, useId, useRef, useState } from 'react';
import { isAxiosError } from 'axios';
import { X } from 'lucide-react';
import { useManageReservation, useReservationAvailability } from '../../api/bookings';
import type { BookingResponse, TimeSlot } from '../../types/api';
import DateScroller from './DateScroller';
import TimeSlotSelector, { type TimeSlotOption } from './TimeSlotSelector';

export type ReservationAction = 'move' | 'cancel';

interface ManageReservationDialogProps {
  action: ReservationAction;
  booking: BookingResponse;
  onClose: () => void;
  onSuccess: () => void;
}

const hourMs = 60 * 60 * 1000;
const dateTimeFormat = new Intl.DateTimeFormat('en-GB', {
  dateStyle: 'medium',
  timeStyle: 'short',
});
const timeFormat = new Intl.DateTimeFormat('en-GB', { timeStyle: 'short' });

function localDate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

function moveTimeSlots(slotDays: TimeSlot[][], booking: BookingResponse, date: string): TimeSlotOption[] {
  const originalStart = Date.parse(booking.start_time);
  const duration = Date.parse(booking.end_time) - originalStart;
  const hours = duration / hourMs;
  const now = Date.now();

  return slotDays.flatMap((day) => day.flatMap((slot, index): TimeSlotOption[] => {
    const start = new Date(slot.start_time);
    if (localDate(start) !== date) return [];

    const startTime = start.getTime();
    const window = day.slice(index, index + hours);
    const fits = window.length === hours && window.every((hour, offset) => (
      hour.status === 'AVAILABLE' &&
      Date.parse(hour.start_time) === startTime + offset * hourMs &&
      Date.parse(hour.end_time) === startTime + (offset + 1) * hourMs
    ));
    const isCurrent = startTime === originalStart;
    const isPast = slot.status === 'PAST' || startTime <= now;

    return [{
      start_time: slot.start_time,
      end_time: new Date(startTime + duration).toISOString(),
      price: booking.total_price,
      status: isPast ? 'PAST' : fits && !isCurrent ? 'AVAILABLE' : 'OCCUPIED',
      unavailableLabel: isCurrent ? 'Current slot' : 'Unavailable',
    }];
  }));
}

export default function ManageReservationDialog({
  action,
  booking,
  onClose,
  onSuccess,
}: ManageReservationDialogProps) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const moving = action === 'move';
  const [date, setDate] = useState(() => localDate(new Date(booking.start_time)));
  const [startTime, setStartTime] = useState('');
  const availability = useReservationAvailability(booking, moving ? date : '');
  const change = useManageReservation(booking.id);
  const slots = moveTimeSlots(availability.data ?? [], booking, date);
  const selectedSlot = slots.find((slot) => slot.status === 'AVAILABLE' && slot.start_time === startTime);
  const canMove = Boolean(selectedSlot) && !availability.isError;
  const hasLobby = Boolean(booking.match || booking.open_match_id);
  const affectsLobby = hasLobby && (!moving || !booking.match ||
    booking.match.status === 'OPEN' || booking.match.status === 'FULL');
  const title = moving ? 'Move reservation' : 'Cancel reservation';

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
    return () => dialog?.close();
  }, []);

  const dismiss = () => {
    dialogRef.current?.close();
    onClose();
  };

  const selectDate = (newDate: string) => {
    if (newDate === date) return;
    setDate(newDate);
    setStartTime('');
    change.reset();
  };

  const errorDetail = isAxiosError<{ detail?: unknown }>(change.error)
    ? change.error.response?.data?.detail
    : undefined;
  const errorMessage = typeof errorDetail === 'string'
    ? errorDetail
    : 'We couldn’t update your reservation. Please try again.';

  const submit = () => {
    if (change.isPending || (moving && !canMove)) return;
    change.mutate(moving ? { action: 'move', startTime } : { action: 'cancel' }, {
      onSuccess: () => {
        dismiss();
        onSuccess();
      },
      onError: (error) => {
        if (moving && isAxiosError(error) && error.response?.status === 409) {
          setStartTime('');
          void availability.refetch();
        }
      },
    });
  };

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (!change.isPending) dismiss();
      }}
      className={`m-auto w-[calc(100%-2rem)] overflow-hidden rounded-2xl border border-slate-200 bg-white p-0 text-slate-900 shadow-xl backdrop:bg-slate-900/50 ${moving ? 'max-w-2xl' : 'max-w-lg'}`}
    >
      <form
        aria-busy={change.isPending}
        onSubmit={(event) => { event.preventDefault(); submit(); }}
        className="flex max-h-[calc(100dvh-2rem-2px)] flex-col"
      >
        <div className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-100 px-4 py-3 sm:px-6 sm:py-4">
          <div className="min-w-0 space-y-1">
            <h2 id={titleId} className="text-lg font-black">{title}</h2>
            <p className="break-words text-sm font-semibold text-slate-700">
              {booking.pitch_name ?? 'Football Pitch'} · {booking.venue_name ?? 'Venue'}
            </p>
            <p className="text-sm text-slate-600">
              {dateTimeFormat.format(Date.parse(booking.start_time))}–{timeFormat.format(Date.parse(booking.end_time))}
            </p>
          </div>
          <button
            type="button"
            aria-label="Close"
            onClick={dismiss}
            disabled={change.isPending}
            className="shrink-0 rounded-lg p-2 text-slate-500 hover:bg-slate-100 disabled:opacity-50"
          >
            <X size={20} />
          </button>
        </div>

        <div className="min-h-0 space-y-3 overflow-y-auto px-4 py-4 sm:px-6">
          {moving ? (
            <fieldset disabled={change.isPending} className="min-w-0 space-y-3">
              <DateScroller
                selectedDate={date}
                onDateChange={selectDate}
                title="Select new date"
                allowDateJump
              />
              {availability.isLoading ? (
                <p role="status" className="text-sm text-slate-600">Checking availability…</p>
              ) : availability.isError ? (
                <p role="alert" className="text-sm text-red-700">
                  Couldn’t load available times.{' '}
                  <button type="button" onClick={() => void availability.refetch()} className="font-semibold underline">
                    Try again
                  </button>
                </p>
              ) : (
                <>
                  {!slots.some((slot) => slot.status === 'AVAILABLE') && (
                    <p className="text-sm text-slate-600">No available times fit this reservation on that date.</p>
                  )}
                  {slots.length > 0 && (
                    <TimeSlotSelector
                      slots={slots}
                      selectedSlot={selectedSlot}
                      onSelectAvailableSlot={(slot) => {
                        setStartTime(slot.start_time);
                        change.reset();
                      }}
                    />
                  )}
                </>
              )}
            </fieldset>
          ) : (
            <p className="text-sm text-slate-700">Cancelling releases your slot and keeps the reservation in your history.</p>
          )}
          {affectsLobby && (
            <p className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-900">
              {moving
                ? 'The linked match lobby will move to the new time with its current players.'
                : 'The linked match lobby will also be cancelled.'}
            </p>
          )}
        </div>

        <div className="shrink-0 space-y-2 border-t border-slate-100 px-4 py-3 sm:px-6">
          {change.isError && <p role="alert" className="text-sm text-red-700">{errorMessage}</p>}
          <div className="grid grid-cols-2 gap-2 sm:flex sm:justify-end">
            <button
              type="button"
              onClick={dismiss}
              disabled={change.isPending}
              className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 sm:px-4"
            >
              Keep reservation
            </button>
            <button
              type="submit"
              disabled={change.isPending || (moving && !canMove)}
              className={`rounded-xl px-3 py-2.5 text-sm font-bold text-white disabled:opacity-50 sm:px-4 ${
                moving ? 'bg-emerald-700 hover:bg-emerald-800' : 'bg-red-700 hover:bg-red-800'
              }`}
            >
              {moving ? 'Confirm move' : 'Confirm cancellation'}
            </button>
          </div>
        </div>
      </form>
    </dialog>
  );
}
