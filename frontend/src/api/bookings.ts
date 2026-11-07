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

export const useUserBookings = () => {
  return useQuery<BookingResponse[]>({
    queryKey: ['user-bookings'],
    queryFn: async () => {
      const { data } = await apiClient.get<BookingResponse[]>('/bookings/me');
      return data;
    },
  });
};

