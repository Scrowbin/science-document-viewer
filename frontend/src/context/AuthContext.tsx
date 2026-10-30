import React, { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { AuthContext } from './AuthContextDefinition';
import type {
  User,
  LoginCredentials,
  RegisterData,
  AuthState,
  AuthContextType,
} from '../types/auth';

import { authApi } from '../api/authApi';
import { AUTH_EXPIRED_EVENT, clearStoredAuth } from '../api/client';

const STORAGE_USER_KEY = 'scidocs_auth_user';
const STORAGE_TOKEN_KEY = 'scidocs_auth_token';
const STORAGE_REFRESH_KEY = 'scidocs_refresh_token';
/** Legacy client-side "demo account" registry (held plain-text passwords). Removed; purged on load. */
const LEGACY_USERS_REGISTRY_KEY = 'scidocs_registered_users';

// Password reset needs a backend email flow that doesn't exist yet; don't pretend it worked.
const PASSWORD_RESET_UNAVAILABLE = {
  success: false,
  message: 'Password reset is not available yet. Please contact the administrator.',
};

const LOGGED_OUT: AuthState = { user: null, token: null, isAuthenticated: false, isLoading: false, error: null };

/** Old builds issued fake client-side tokens ("jwt-...") the backend never accepts. */
function isFakeToken(token: string | null): boolean {
  return !!token && token.startsWith('jwt-');
}

function apiErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError(err)) {
    if (!err.response) return 'Cannot reach the server. Check that the backend is running.';
    const status = err.response.status;
    const data = err.response.data as Record<string, unknown> | undefined;
    if (status === 401) return 'Incorrect username/email or password.';
    if (data && typeof data === 'object') {
      const first = Object.values(data)[0];
      if (typeof first === 'string') return first;
      if (Array.isArray(first) && typeof first[0] === 'string') return first[0];
    }
    return `${fallback} (HTTP ${status}).`;
  }
  return fallback;
}

/** Keeps tokens in exactly one storage: localStorage when "remember me", otherwise sessionStorage. */
function persistSession(user: User, access: string, refresh: string, remember: boolean): void {
  clearStoredAuth();
  const store = remember ? localStorage : sessionStorage;
  store.setItem(STORAGE_USER_KEY, JSON.stringify(user));
  store.setItem(STORAGE_TOKEN_KEY, access);
  store.setItem(STORAGE_REFRESH_KEY, refresh);
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>(() => {
    try {
      localStorage.removeItem(LEGACY_USERS_REGISTRY_KEY);
      const storedUser = localStorage.getItem(STORAGE_USER_KEY) || sessionStorage.getItem(STORAGE_USER_KEY);
      const storedToken = localStorage.getItem(STORAGE_TOKEN_KEY) || sessionStorage.getItem(STORAGE_TOKEN_KEY);
      if (isFakeToken(storedToken)) {
        clearStoredAuth();
        return LOGGED_OUT;
      }
      if (storedUser && storedToken) {
        return { user: JSON.parse(storedUser), token: storedToken, isAuthenticated: true, isLoading: false, error: null };
      }
    } catch (e) {
      console.error('Failed to parse cached auth state:', e);
    }
    // Default: unauthenticated user. Explicit login is required.
    return LOGGED_OUT;
  });

  // The API client signals an unrecoverable 401 (expired or invalid session): go back to logged out,
  // which sends the user to the login page.
  useEffect(() => {
    const onExpired = () =>
      setAuthState({ ...LOGGED_OUT, error: 'Your session has expired. Please sign in again.' });
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  }, []);

  const clearError = useCallback(() => {
    setAuthState((prev) => ({ ...prev, error: null }));
  }, []);

  /** Log in against the Django API (JWT). There is no offline or demo fallback. */
  const login = useCallback(async (credentials: LoginCredentials): Promise<boolean> => {
    setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const { user, tokens } = await authApi.login(credentials);
      persistSession(user, tokens.access, tokens.refresh, !!credentials.rememberMe);
      setAuthState({ user, token: tokens.access, isAuthenticated: true, isLoading: false, error: null });
      return true;
    } catch (err) {
      clearStoredAuth();
      setAuthState({ ...LOGGED_OUT, error: apiErrorMessage(err, 'Sign-in failed') });
      return false;
    }
  }, []);

  /** Register against the Django API. There is no offline or demo fallback. */
  const register = useCallback(async (data: RegisterData): Promise<boolean> => {
    setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const { user, tokens } = await authApi.register(data);
      persistSession(user, tokens.access, tokens.refresh, true);
      setAuthState({ user, token: tokens.access, isAuthenticated: true, isLoading: false, error: null });
      return true;
    } catch (err) {
      clearStoredAuth();
      setAuthState({ ...LOGGED_OUT, error: apiErrorMessage(err, 'Registration failed') });
      return false;
    }
  }, []);

  /** Log out current user (calls server-side blacklist & clears storage) */
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore errors on logout
    }
    clearStoredAuth();
    setAuthState(LOGGED_OUT);
  }, []);

  const requestPasswordReset = useCallback(async () => PASSWORD_RESET_UNAVAILABLE, []);
  const confirmPasswordReset = useCallback(async () => PASSWORD_RESET_UNAVAILABLE, []);

  const value: AuthContextType = {
    ...authState,
    login,
    register,
    logout,
    requestPasswordReset,
    confirmPasswordReset,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
