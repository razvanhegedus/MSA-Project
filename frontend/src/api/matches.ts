import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import {
  MatchResponse,
  MatchDetailResponse,
  JoinMatchPayload,
  MatchCreatePayload,
  MatchUpdatePayload,
} from '../types/api';

export const useOpenMatches = (city?: string, enabled = true) => {
  return useQuery<MatchResponse[]>({
    queryKey: ['open-matches', city],
    enabled,
    queryFn: async ({ signal }) => {
      const { data } = await apiClient.get<MatchResponse[]>('/matches', {
        params: { city },
        signal,
      });
      return data;
    },
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
};

export const useMatchDetail = (matchId: string) => {
  return useQuery<MatchDetailResponse>({
    queryKey: ['match-detail', matchId],
    queryFn: async ({ signal }) => {
      const { data } = await apiClient.get<MatchDetailResponse>(`/matches/${matchId}`, { signal });
      return data;
    },
    enabled: Boolean(matchId),
  });
};

export const useJoinMatch = (matchId: string) => {
  const queryClient = useQueryClient();

  return useMutation<MatchDetailResponse, Error, JoinMatchPayload>({
    mutationFn: async (payload: JoinMatchPayload) => {
      const { data } = await apiClient.post<MatchDetailResponse>(
        `/matches/${matchId}/join`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['open-matches'] });
      void queryClient.invalidateQueries({ queryKey: ['match-detail', matchId] });
      void queryClient.invalidateQueries({ queryKey: ['pitch-availability'] });
      void queryClient.invalidateQueries({ queryKey: ['user-bookings'] });
      void queryClient.invalidateQueries({ queryKey: ['my-matches'] });
    },
  });
};

export const useMyMatches = (userId: string | undefined) => {
  return useQuery<MatchDetailResponse[]>({
    queryKey: ['my-matches', userId],
    enabled: Boolean(userId),
    queryFn: async ({ signal }) => {
      const { data } = await apiClient.get<MatchDetailResponse[]>('/matches/me', { signal });
      return data;
    },
    staleTime: 15_000,
  });
};

export const useCreateMatchFromBooking = () => {
  const queryClient = useQueryClient();

  return useMutation<MatchDetailResponse, Error, MatchCreatePayload>({
    mutationFn: async (payload: MatchCreatePayload) => {
      const { data } = await apiClient.post<MatchDetailResponse>('/matches', payload);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['user-bookings'] });
      void queryClient.invalidateQueries({ queryKey: ['my-matches'] });
      void queryClient.invalidateQueries({ queryKey: ['open-matches'] });
      void queryClient.invalidateQueries({ queryKey: ['pitch-availability'] });
    },
  });
};

export const useUpdateMatch = (matchId: string) => {
  const queryClient = useQueryClient();

  return useMutation<MatchDetailResponse, Error, MatchUpdatePayload>({
    mutationFn: async (payload: MatchUpdatePayload) => {
      const { data } = await apiClient.patch<MatchDetailResponse>(`/matches/${matchId}`, payload);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['user-bookings'] });
      void queryClient.invalidateQueries({ queryKey: ['my-matches'] });
      void queryClient.invalidateQueries({ queryKey: ['open-matches'] });
      void queryClient.invalidateQueries({ queryKey: ['pitch-availability'] });
      void queryClient.invalidateQueries({ queryKey: ['match-detail', matchId] });
    },
  });
};

