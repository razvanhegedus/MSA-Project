import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  apiClient,
  endAuthSession,
  getAuthSessionVersion,
  onAuthSessionEnd,
  startAuthSession,
} from '../api/client';
import { UserResponse, LoginPayload, RegisterPayload, TokenResponse } from '../types/api';

interface AuthContextValue {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearPrivateQueries = useCallback(() => {
    queryClient.removeQueries({ queryKey: ['user-bookings'] });
    queryClient.removeQueries({ queryKey: ['my-matches'] });
  }, [queryClient]);

  const fetchMe = useCallback(async (version: number) => {
    try {
      const { data } = await apiClient.get<UserResponse>('/auth/me');
      if (version !== getAuthSessionVersion()) throw new Error('The signed-in account changed.');
      setUser(data);
    } catch (error) {
      if (version === getAuthSessionVersion()) endAuthSession();
      throw error;
    } finally {
      if (version === getAuthSessionVersion()) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthSessionEnd(() => {
      clearPrivateQueries();
      setUser(null);
      setIsLoading(false);
    });

    if (localStorage.getItem('access_token')) {
      void fetchMe(getAuthSessionVersion()).catch(() => undefined);
    } else {
      setIsLoading(false);
    }

    return unsubscribe;
  }, [clearPrivateQueries, fetchMe]);

  const login = useCallback(async (payload: LoginPayload) => {
    const previousVersion = getAuthSessionVersion();
    const { data } = await apiClient.post<TokenResponse>('/auth/login', payload);
    if (previousVersion !== getAuthSessionVersion()) throw new Error('The signed-in account changed.');

    clearPrivateQueries();
    await fetchMe(startAuthSession(data));
  }, [clearPrivateQueries, fetchMe]);

  const register = useCallback(async (payload: RegisterPayload) => {
    await apiClient.post('/auth/register', payload);
    await login({ email: payload.email, password: payload.password });
  }, [login]);

  const logout = useCallback(() => {
    const refreshToken = localStorage.getItem('refresh_token');
    endAuthSession();
    if (refreshToken) {
      void apiClient.post('/auth/logout', { refresh_token: refreshToken }).catch(() => undefined);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: Boolean(user),
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};
