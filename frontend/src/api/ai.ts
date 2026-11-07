import { useMutation } from '@tanstack/react-query';
import { apiClient } from './client';
import { AIChatRequest, AIChatResponse } from '../types/api';

export const useAIChat = () => {
  return useMutation<AIChatResponse, Error, AIChatRequest>({
    mutationFn: async (payload: AIChatRequest) => {
      const { data } = await apiClient.post<AIChatResponse>('/ai/chat', payload);
      return data;
    },
  });
};

