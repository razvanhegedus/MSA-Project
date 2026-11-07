import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import { MatchResponse, MatchDetailResponse, JoinMatchPayload } from '../types/api';

export const useOpenMatches = (city?: string, status = 'OPEN') => {
  return useQuery<MatchResponse[]>({
    queryKey: ['open-matches', city, status],
    queryFn: async () => {
      const { data } = await apiClient.get<MatchResponse[]>('/matches', {
        params: { status, ...(city ? { city } : {}) },
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
    queryFn: async () => {
      const { data } = await apiClient.get<MatchDetailResponse>(`/matches/${matchId}`);
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
    },
  });
};

