import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request Interceptor: Attach JWT Access Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('scidocs_auth_token') || sessionStorage.getItem('scidocs_auth_token');
    // Only attach real cryptographic JWT tokens, never fake client-side mock strings
    if (token && !token.startsWith('jwt-') && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // If sending FormData, delete Content-Type to allow browser to generate multipart boundary
    if (config.data instanceof FormData && config.headers) {
      if (typeof (config.headers as Record<string, unknown>).delete === 'function') {
        (config.headers as { delete: (h: string) => void }).delete('Content-Type');
        (config.headers as { delete: (h: string) => void }).delete('content-type');
      }
      delete config.headers['Content-Type'];
      delete config.headers['content-type'];
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response Interceptor: Handle 401 & Refresh Token
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('scidocs_refresh_token') || sessionStorage.getItem('scidocs_refresh_token');

      if (!refreshToken || refreshToken.startsWith('jwt-') || originalRequest.url?.endsWith('/auth/token/refresh/')) {
        // Clear dead or mock token so subsequent requests aren't permanently poisoned with 401
        localStorage.removeItem('scidocs_auth_token');
        sessionStorage.removeItem('scidocs_auth_token');
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const newAccessToken = response.data.access;
        if (localStorage.getItem('scidocs_auth_token')) {
          localStorage.setItem('scidocs_auth_token', newAccessToken);
          if (response.data.refresh) {
            localStorage.setItem('scidocs_refresh_token', response.data.refresh);
          }
        } else {
          sessionStorage.setItem('scidocs_auth_token', newAccessToken);
          if (response.data.refresh) {
            sessionStorage.setItem('scidocs_refresh_token', response.data.refresh);
          }
        }

        apiClient.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;
        processQueue(null, newAccessToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        localStorage.removeItem('scidocs_auth_token');
        localStorage.removeItem('scidocs_refresh_token');
        localStorage.removeItem('scidocs_auth_user');
        sessionStorage.removeItem('scidocs_auth_token');
        sessionStorage.removeItem('scidocs_refresh_token');
        sessionStorage.removeItem('scidocs_auth_user');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
