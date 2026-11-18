import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import { TimeSlot, BookingCreatePayload, BookingResponse } from '../types/api';

export const usePitchAvailability = (pitchId: string, targetDate: string) => {
  return useQuery<TimeSlot[]>({
    queryKey: ['pitch-availability', pitchId, targetDate],
    queryFn: async () => {
      const { data } = await apiClient.get<TimeSlot[]>(
        `/pitches/${pitchId}/availability`,
        { params: { target_date: targetDate } }
      );
      return data;
    },
    enabled: Boolean(pitchId) && Boolean(targetDate),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
};

export const useCreateBooking = (pitchId: string, targetDate: string) => {
  const queryClient = useQueryClient();

  return useMutation<BookingResponse, Error, BookingCreatePayload>({
    mutationFn: async (payload: BookingCreatePayload) => {
      const { data } = await apiClient.post<BookingResponse>('/bookings', payload);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['pitch-availability', pitchId, targetDate],
      });
      void queryClient.invalidateQueries({ queryKey: ['pitch-availability'] });
      void queryClient.invalidateQueries({ queryKey: ['user-bookings'] });
      void queryClient.invalidateQueries({ queryKey: ['open-matches'] });
    },
  });
};

export const useUserBookings = (userId: string | undefined) => {
  return useQuery<BookingResponse[]>({
    queryKey: ['user-bookings', userId],
    enabled: Boolean(userId),
    queryFn: async ({ signal }) => {
      const { data } = await apiClient.get<BookingResponse[]>('/bookings/me', { signal });
      return data;
    },
  });
};

// Availability is requested by UTC day. A local calendar day can include slots from
// adjacent UTC days, so retain the boundaries for venue-hours validation.
function getUtcDates(localDate: string): string[] {
  const start = new Date(localDate + 'T00:00:00');
  if (Number.isNaN(start.getTime())) return [];

  const end = new Date(start);
  end.setDate(end.getDate() + 1);
  const dates: string[] = [];
  for (const date = new Date(start); date < end; date.setUTCHours(24, 0, 0, 0)) {
    dates.push(date.toISOString().slice(0, 10));
  }
  return dates;
}

export const useReservationAvailability = (booking: BookingResponse, localDate: string) => {
  const dates = localDate ? getUtcDates(localDate) : [];

  return useQuery<TimeSlot[][]>({
    queryKey: ['user-bookings', booking.booked_by_user_id, 'availability', booking.id, localDate],
    queryFn: ({ signal }) => Promise.all(dates.map(async (targetDate) => {
      const { data } = await apiClient.get<TimeSlot[]>(`/bookings/${booking.id}/availability`, {
        params: { target_date: targetDate },
        signal,
      });
      return data;
    })),
    enabled: dates.length > 0,
  });
};

type ReservationChange = { action: 'move'; startTime: string } | { action: 'cancel' };

export const useManageReservation = (bookingId: string) => {
  const queryClient = useQueryClient();

  return useMutation<BookingResponse, Error, ReservationChange>({
    mutationFn: async (change) => {
      const path = `/bookings/${bookingId}`;
      const { data } = change.action === 'move'
        ? await apiClient.patch<BookingResponse>(path, { start_time: change.startTime })
        : await apiClient.delete<BookingResponse>(path);
      return data;
    },
    onSuccess: (booking) => {
      const bookingsKey = ['user-bookings', booking.booked_by_user_id];
      queryClient.setQueryData<BookingResponse[]>(bookingsKey, (bookings) => bookings
        ?.map((item) => item.id === booking.id ? booking : item)
        .sort((left, right) => Date.parse(right.start_time) - Date.parse(left.start_time)));
      void queryClient.invalidateQueries({ queryKey: bookingsKey, exact: true });
      void queryClient.invalidateQueries({ queryKey: ['pitch-availability', booking.pitch_id] });
      if (booking.match || booking.open_match_id) {
        const matchId = booking.match?.id ?? booking.open_match_id;
        void queryClient.invalidateQueries({ queryKey: ['my-matches'] });
        void queryClient.invalidateQueries({ queryKey: ['open-matches'] });
        void queryClient.invalidateQueries({ queryKey: ['match-detail', matchId] });
      }
    },
  });
};
