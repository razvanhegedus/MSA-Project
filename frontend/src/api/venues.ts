import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import { VenueResponse, PitchResponse } from '../types/api';

export const useVenues = (city?: string, surfaceType?: string) => {
  return useQuery<VenueResponse[]>({
    queryKey: ['venues', city, surfaceType],
    queryFn: async () => {
      const { data } = await apiClient.get<VenueResponse[]>('/venues', {
        params: {
          ...(city ? { city } : {}),
          ...(surfaceType ? { surface_type: surfaceType } : {}),
        },
      });
      return data;
    },
    staleTime: 60_000,
  });
};

export const useVenuePitches = (venueId: string) => {
  return useQuery<PitchResponse[]>({
    queryKey: ['venue-pitches', venueId],
    queryFn: async () => {
      const { data } = await apiClient.get<PitchResponse[]>(`/venues/${venueId}/pitches`);
      return data;
    },
    enabled: Boolean(venueId),
    staleTime: 60_000,
  });
};

export const usePitch = (pitchId: string) => {
  return useQuery<PitchResponse>({
    queryKey: ['pitch', pitchId],
    queryFn: async () => {
      const { data } = await apiClient.get<PitchResponse>(`/pitches/${pitchId}`);
      return data;
    },
    enabled: Boolean(pitchId),
    staleTime: 60_000,
  });
};

