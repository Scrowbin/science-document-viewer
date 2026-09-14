/**
 * Authentication and User Identity Types
 */

export interface User {
  id: string;
  name: string;
  email: string;
  institution?: string;
  avatarUrl?: string;
  role?: string;
  createdAt?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  institution?: string;
  acceptTerms: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => void;
  requestPasswordReset: (email: string) => Promise<{ success: boolean; message: string }>;
  confirmPasswordReset: (
    email: string,
    code: string,
    newPassword: string
  ) => Promise<{ success: boolean; message: string }>;
  clearError: () => void;
}
