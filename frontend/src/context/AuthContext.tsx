import React, { useState, useEffect, useCallback } from 'react';
import { AuthContext } from './AuthContextDefinition';
import type {
  User,
  LoginCredentials,
  RegisterData,
  AuthState,
  AuthContextType,
} from '../types/auth';

import { authApi } from '../api/authApi';

const STORAGE_USER_KEY = 'scidocs_auth_user';
const STORAGE_TOKEN_KEY = 'scidocs_auth_token';
const STORAGE_REFRESH_KEY = 'scidocs_refresh_token';
const STORAGE_USERS_REGISTRY_KEY = 'scidocs_registered_users';

// Pre-seeded default demo accounts for instant testing
const DEFAULT_DEMO_USERS: Array<{ user: User; passwordHash: string }> = [
  {
    user: {
      id: 'usr-1',
      name: 'Dr. Sarah Jenkins',
      email: 'sarah.jenkins@stanford.edu',
      institution: 'Stanford AI & Medicine Lab',
      avatarUrl: '',
      role: 'Principal Investigator',
      createdAt: '2025-01-15T08:00:00Z',
    },
    passwordHash: 'Password123!',
  },
  {
    user: {
      id: 'usr-2',
      name: 'Alex Morgan',
      email: 'demo@research.org',
      institution: 'Open Science Foundation',
      avatarUrl: '',
      role: 'Research Fellow',
      createdAt: '2025-02-01T10:30:00Z',
    },
    passwordHash: 'Password123!',
  },
];

// Helper to get registered users pool from localStorage
function getRegisteredUsers(): Array<{ user: User; passwordHash: string }> {
  try {
    const raw = localStorage.getItem(STORAGE_USERS_REGISTRY_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_USERS_REGISTRY_KEY, JSON.stringify(DEFAULT_DEMO_USERS));
      return DEFAULT_DEMO_USERS;
    }
    return JSON.parse(raw);
  } catch {
    return DEFAULT_DEMO_USERS;
  }
}

// Helper to save registered users pool
function saveRegisteredUsers(users: Array<{ user: User; passwordHash: string }>): void {
  try {
    localStorage.setItem(STORAGE_USERS_REGISTRY_KEY, JSON.stringify(users));
  } catch (err) {
    console.error('Failed to persist users registry:', err);
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>(() => {
    // Check initial user in localStorage or sessionStorage
    try {
      const storedUser = localStorage.getItem(STORAGE_USER_KEY) || sessionStorage.getItem(STORAGE_USER_KEY);
      const storedToken = localStorage.getItem(STORAGE_TOKEN_KEY) || sessionStorage.getItem(STORAGE_TOKEN_KEY);
      if (storedUser && storedToken) {
        return {
          user: JSON.parse(storedUser),
          token: storedToken,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        };
      }
    } catch (e) {
      console.error('Failed to parse cached auth state:', e);
    }
    // Default: unauthenticated user. Explicit login is required.
    return {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    };
  });

  // Ensure initial registry is initialized
  useEffect(() => {
    getRegisteredUsers();
  }, []);

  const clearError = useCallback(() => {
    setAuthState((prev) => ({ ...prev, error: null }));
  }, []);

  /**
   * Log in with email & password (Live Django API first, fallback to demo accounts)
   */
  const login = useCallback(async (credentials: LoginCredentials): Promise<boolean> => {
    setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));

    // 1. Attempt Live Django DRF Token API
    try {
      const { user, tokens } = await authApi.login(credentials);
      if (credentials.rememberMe) {
        localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
        localStorage.setItem(STORAGE_TOKEN_KEY, tokens.access);
        localStorage.setItem(STORAGE_REFRESH_KEY, tokens.refresh);
      } else {
        sessionStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
        sessionStorage.setItem(STORAGE_TOKEN_KEY, tokens.access);
      }

      setAuthState({
        user,
        token: tokens.access,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      return true;
    } catch (apiErr) {
      console.warn('Live API auth unreachable or failed, trying local demo fallback:', apiErr);
    }

    // 2. Demo Registry Fallback (offline / local development)
    const registry = getRegisteredUsers();
    const cleanEmail = credentials.email.trim().toLowerCase();

    const matched = registry.find(
      (entry) => entry.user.email.toLowerCase() === cleanEmail
    );

    if (!matched) {
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'No account found with this email address.',
      }));
      return false;
    }

    if (matched.passwordHash !== credentials.password) {
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Incorrect password. Please verify your credentials.',
      }));
      return false;
    }

    // Success with local demo credentials
    const fakeToken = `jwt-${matched.user.id}-${Date.now()}`;
    if (credentials.rememberMe) {
      localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(matched.user));
      localStorage.setItem(STORAGE_TOKEN_KEY, fakeToken);
    } else {
      sessionStorage.setItem(STORAGE_USER_KEY, JSON.stringify(matched.user));
      sessionStorage.setItem(STORAGE_TOKEN_KEY, fakeToken);
    }

    setAuthState({
      user: matched.user,
      token: fakeToken,
      isAuthenticated: true,
      isLoading: false,
      error: null,
    });
    return true;
  }, []);

  /**
   * Register a new user account (Live Django API first, fallback to demo accounts)
   */
  const register = useCallback(async (data: RegisterData): Promise<boolean> => {
    setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));

    // 1. Attempt Live Django DRF Registration
    try {
      const { user, tokens } = await authApi.register(data);
      localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
      localStorage.setItem(STORAGE_TOKEN_KEY, tokens.access);
      localStorage.setItem(STORAGE_REFRESH_KEY, tokens.refresh);

      setAuthState({
        user,
        token: tokens.access,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      return true;
    } catch (apiErr) {
      console.warn('Live API registration failed or unreachable, trying local fallback:', apiErr);
    }

    // 2. Demo Registry Fallback
    const registry = getRegisteredUsers();
    const cleanEmail = data.email.trim().toLowerCase();

    const existing = registry.find(
      (entry) => entry.user.email.toLowerCase() === cleanEmail
    );

    if (existing) {
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'An account with this email address already exists.',
      }));
      return false;
    }

    const newUser: User = {
      id: `usr-${Date.now()}`,
      name: data.name.trim(),
      email: cleanEmail,
      institution: data.institution?.trim() || 'Independent Researcher',
      avatarUrl: '',
      role: 'Researcher',
      createdAt: new Date().toISOString(),
    };

    const newRegistry = [...registry, { user: newUser, passwordHash: data.password }];
    saveRegisteredUsers(newRegistry);

    const token = `jwt-${newUser.id}-${Date.now()}`;
    localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(newUser));
    localStorage.setItem(STORAGE_TOKEN_KEY, token);

    setAuthState({
      user: newUser,
      token,
      isAuthenticated: true,
      isLoading: false,
      error: null,
    });
    return true;
  }, []);

  /**
   * Log out current user (calls server-side blacklist & clears storage)
   */
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore errors on logout
    }
    localStorage.removeItem(STORAGE_USER_KEY);
    localStorage.removeItem(STORAGE_TOKEN_KEY);
    localStorage.removeItem(STORAGE_REFRESH_KEY);
    sessionStorage.removeItem(STORAGE_USER_KEY);
    sessionStorage.removeItem(STORAGE_TOKEN_KEY);
    sessionStorage.removeItem(STORAGE_REFRESH_KEY);

    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  }, []);


  /**
   * Request password reset instructions
   */
  const requestPasswordReset = useCallback(
    async (email: string): Promise<{ success: boolean; message: string }> => {
      await new Promise((res) => setTimeout(res, 400));
      const cleanEmail = email.trim().toLowerCase();
      const registry = getRegisteredUsers();
      const user = registry.find((u) => u.user.email.toLowerCase() === cleanEmail);

      if (!user) {
        return {
          success: false,
          message: 'No account registered with this email address.',
        };
      }

      return {
        success: true,
        message: 'A 6-digit verification code has been sent to your email address.',
      };
    },
    []
  );

  /**
   * Confirm password reset with 6-digit code and new password
   */
  const confirmPasswordReset = useCallback(
    async (
      email: string,
      code: string,
      newPassword: string
    ): Promise<{ success: boolean; message: string }> => {
      await new Promise((res) => setTimeout(res, 450));
      const cleanEmail = email.trim().toLowerCase();
      const registry = getRegisteredUsers();
      const userIdx = registry.findIndex((u) => u.user.email.toLowerCase() === cleanEmail);

      if (userIdx === -1) {
        return { success: false, message: 'Account not found.' };
      }

      // Allow any 6-digit code for testing mock or specifically '123456'
      if (!/^\d{6}$/.test(code.trim())) {
        return { success: false, message: 'Invalid verification code. Please enter 6 digits.' };
      }

      registry[userIdx].passwordHash = newPassword;
      saveRegisteredUsers(registry);

      return {
        success: true,
        message: 'Your password has been reset successfully. You can now log in.',
      };
    },
    []
  );

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

