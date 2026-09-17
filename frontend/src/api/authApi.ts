import apiClient from './client';
import type { LoginCredentials, RegisterData, User } from '../types/auth';

export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface RegisterResponse {
  user: {
    id: string | number;
    username: string;
    email: string;
    date_joined?: string;
  };
  tokens: {
    access: string;
    refresh: string;
  };
}

export const authApi = {
  /**
   * Login with username or email + password to obtain JWT tokens.
   */
  async login(credentials: LoginCredentials): Promise<{ user: User; tokens: TokenResponse }> {
    // Django's TokenObtainPairView expects 'username' and 'password'
    // If the user typed an email, we pass it as username
    const usernameOrEmail = credentials.email || '';
    const res = await apiClient.post<TokenResponse>('/auth/token/', {
      username: usernameOrEmail,
      password: credentials.password,
    });

    const tokens = res.data;
    localStorage.setItem('scidocs_auth_token', tokens.access);
    localStorage.setItem('scidocs_refresh_token', tokens.refresh);

    // Fetch user details with the newly acquired token
    const meRes = await apiClient.get<{ id: string | number; username: string; email: string }>('/auth/me/');
    const user: User = {
      id: String(meRes.data.id),
      name: meRes.data.username,
      email: meRes.data.email,
      institution: 'Academic Researcher',
      role: 'Researcher',
      createdAt: new Date().toISOString(),
    };

    localStorage.setItem('scidocs_auth_user', JSON.stringify(user));
    return { user, tokens };
  },

  /**
   * Register a new user account.
   */
  async register(data: RegisterData): Promise<{ user: User; tokens: TokenResponse }> {
    const username = data.name.trim().toLowerCase().replace(/\s+/g, '_') || data.email.split('@')[0];
    const res = await apiClient.post<RegisterResponse>('/auth/register/', {
      username,
      email: data.email,
      password: data.password,
    });

    const { user: registeredUser, tokens } = res.data;
    localStorage.setItem('scidocs_auth_token', tokens.access);
    localStorage.setItem('scidocs_refresh_token', tokens.refresh);

    const user: User = {
      id: String(registeredUser.id),
      name: registeredUser.username,
      email: registeredUser.email,
      institution: data.institution || 'Academic Institution',
      role: 'Researcher',
      createdAt: registeredUser.date_joined || new Date().toISOString(),
    };

    localStorage.setItem('scidocs_auth_user', JSON.stringify(user));
    return { user, tokens };
  },

  /**
   * Get current authenticated user details.
   */
  async getMe(): Promise<User> {
    const res = await apiClient.get<{ id: string | number; username: string; email: string; date_joined?: string }>('/auth/me/');
    const user: User = {
      id: String(res.data.id),
      name: res.data.username,
      email: res.data.email,
      institution: 'Academic Researcher',
      role: 'Researcher',
      createdAt: res.data.date_joined || new Date().toISOString(),
    };
    return user;
  },

  /**
   * Logout and clear tokens.
   */
  logout(): void {
    localStorage.removeItem('scidocs_auth_token');
    localStorage.removeItem('scidocs_refresh_token');
    localStorage.removeItem('scidocs_auth_user');
  },
};

export default authApi;
