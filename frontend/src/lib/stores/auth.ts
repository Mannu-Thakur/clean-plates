import { browser } from '$app/environment';
import { writable } from 'svelte/store';
import {
  api,
  clearStoredSession,
  persistSession,
  readStoredSession,
  updateStoredUser
} from '$lib/api/client';
import type { LoginResponse, TokenPair, User } from '$lib/api/types';

export interface AuthState {
  ready: boolean;
  loading: boolean;
  user: User | null;
  tokens: TokenPair | null;
  error: string | null;
}

const initialSession = readStoredSession();

export const auth = writable<AuthState>({
  ready: false,
  loading: false,
  user: initialSession?.user ?? null,
  tokens: initialSession?.tokens ?? null,
  error: null
});

let initPromise: Promise<void> | null = null;

export function initAuth() {
  if (initPromise) return initPromise;
  initPromise = (async () => {
    const session = readStoredSession();
    if (!session) {
      auth.set({
        ready: true,
        loading: false,
        user: null,
        tokens: null,
        error: null
      });
      return;
    }
    auth.set({
      ready: false,
      loading: true,
      user: session.user,
      tokens: session.tokens,
      error: null
    });
    try {
      const user = await api.get<User>('/auth/me');
      updateStoredUser(user);
      const updated = readStoredSession();
      auth.set({
        ready: true,
        loading: false,
        user,
        tokens: updated?.tokens ?? session.tokens,
        error: null
      });
    } catch {
      // api.get already attempted token refresh internally on 401.
      // If we still failed, the refresh token is also invalid — clear session.
      const stillValid = readStoredSession();
      if (stillValid) {
        // The request() interceptor refreshed tokens successfully but the
        // retry still failed for another reason. Keep the session and
        // use the cached user rather than logging out.
        auth.set({
          ready: true,
          loading: false,
          user: stillValid.user,
          tokens: stillValid.tokens,
          error: null
        });
      } else {
        auth.set({
          ready: true,
          loading: false,
          user: null,
          tokens: null,
          error: 'Session expired'
        });
      }
      // Reset so next navigation can retry
      initPromise = null;
    }
  })();
  return initPromise;
}

export async function login(
  email: string,
  password: string,
  remember: boolean
) {
  auth.update((state) => ({ ...state, loading: true, error: null }));
  try {
    const response = await api.post<LoginResponse>(
      '/auth/login',
      { email, password, remember_me: remember },
      { skipAuth: true }
    );
    persistSession(response.tokens, response.user, remember);
    // Reset initPromise so next initAuth() re-validates with the fresh token
    initPromise = null;
    auth.set({
      ready: true,
      loading: false,
      user: response.user,
      tokens: response.tokens,
      error: null
    });
    return response.user;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Login failed';
    auth.update((state) => ({ ...state, loading: false, error: message }));
    throw error;
  }
}

export async function logout() {
  const session = readStoredSession();
  try {
    if (session?.tokens.refresh_token) {
      await api.post('/auth/logout', {
        refresh_token: session.tokens.refresh_token
      });
    }
  } catch {
    // The client should clear local credentials even if the server token is already gone.
  }
  clearStoredSession();
  auth.set({
    ready: true,
    loading: false,
    user: null,
    tokens: null,
    error: null
  });
}

if (browser) {
  window.addEventListener('cleanplates:session-change', () => {
    const session = readStoredSession();
    auth.update((state) => ({
      ...state,
      user: session?.user ?? null,
      tokens: session?.tokens ?? null
    }));
  });
}
