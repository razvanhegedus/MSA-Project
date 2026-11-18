import axios, { type InternalAxiosRequestConfig } from 'axios';
import type { TokenResponse } from '../types/api';

export const apiClient = axios.create({
  baseURL: '/v1',
  headers: { 'Content-Type': 'application/json' },
});

const credentialPaths = new Set(['/auth/login', '/auth/register', '/auth/refresh', '/auth/logout']);
const sessionEndListeners = new Set<() => void>();
let sessionVersion = 0;
let pendingRefresh: { version: number; request: Promise<void> } | undefined;

type SessionRequest = InternalAxiosRequestConfig & {
  sessionVersion?: number;
  retried?: boolean;
};

export function getAuthSessionVersion() {
  return sessionVersion;
}

function storeTokens(tokens: TokenResponse) {
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
}

export function startAuthSession(tokens: TokenResponse) {
  sessionVersion += 1;
  storeTokens(tokens);
  return sessionVersion;
}

export function endAuthSession() {
  sessionVersion += 1;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  sessionEndListeners.forEach((listener) => listener());
}

export function onAuthSessionEnd(listener: () => void) {
  sessionEndListeners.add(listener);
  return () => {
    sessionEndListeners.delete(listener);
  };
}

apiClient.interceptors.request.use((config: SessionRequest) => {
  const token = localStorage.getItem('access_token');
  if (token && !credentialPaths.has(config.url ?? '')) {
    config.sessionVersion = sessionVersion;
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
}, undefined, { synchronous: true });

function refreshSession(version: number, refreshToken: string) {
  if (pendingRefresh?.version === version) return pendingRefresh.request;

  const request = apiClient.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
    .then(({ data }) => {
      if (version === sessionVersion) storeTokens(data);
    })
    .finally(() => {
      if (pendingRefresh?.request === request) pendingRefresh = undefined;
    });
  pendingRefresh = { version, request };
  return request;
}

apiClient.interceptors.response.use(
  (response) => {
    const request = response.config as SessionRequest;
    if (request.sessionVersion !== undefined && request.sessionVersion !== sessionVersion) {
      throw new axios.CanceledError('The signed-in account changed.');
    }
    return response;
  },
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401) throw error;

    const request = error.config as SessionRequest | undefined;
    if (request?.sessionVersion === undefined || request.sessionVersion !== sessionVersion) throw error;

    const version = request.sessionVersion;
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken || request.retried) {
      endAuthSession();
      throw error;
    }

    request.retried = true;
    const currentAccessToken = localStorage.getItem('access_token');
    try {
      // A concurrent request may already have refreshed the token used by this request.
      if (request.headers.get('Authorization') === `Bearer ${currentAccessToken}`) {
        await refreshSession(version, refreshToken);
      }
    } catch (refreshError) {
      if (version === sessionVersion) endAuthSession();
      throw refreshError;
    }

    if (version !== sessionVersion) throw new axios.CanceledError('The signed-in account changed.');
    return apiClient(request);
  }
);
