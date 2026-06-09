import axios, { type InternalAxiosRequestConfig } from "axios";

import { getCsrfToken, CSRF_HEADER_NAME } from "@/shared/auth/csrf";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/shared/auth/token";
import { env } from "@/shared/config/env";

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _authRetry?: boolean;
};

type TokenResponse = {
  access_token: string;
  token_type: string;
};

const AUTH_LOGIN_PATH = "/auth/login";
const AUTH_REFRESH_PATH = "/auth/refresh";
const AUTH_LOGOUT_PATH = "/auth/logout";
let refreshPromise: Promise<string | null> | null = null;

export const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

function isUnsafeMethod(method?: string): boolean {
  return ["post", "put", "patch", "delete"].includes((method || "get").toLowerCase());
}

function isAuthFlowRequest(url: string): boolean {
  return (
    url.includes(AUTH_LOGIN_PATH) ||
    url.includes(AUTH_REFRESH_PATH) ||
    url.includes(AUTH_LOGOUT_PATH)
  );
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = apiClient
      .post<TokenResponse>(AUTH_REFRESH_PATH)
      .then((response) => {
        setAccessToken(response.data.access_token);
        return response.data.access_token;
      })
      .catch(() => {
        clearAccessToken();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

function redirectToLogin(): void {
  const currentPath = window.location.pathname + window.location.search + window.location.hash;

  if (currentPath !== "/" && currentPath !== "/auth") {
    sessionStorage.setItem("vatranscribe_redirect_after_login", currentPath);
  }

  if (window.location.pathname !== "/") {
    window.location.assign("/");
  }
}

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (isUnsafeMethod(config.method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers[CSRF_HEADER_NAME] = csrfToken;
    }
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error?.response?.status !== 401) {
      return Promise.reject(error);
    }

    const originalRequest = error.config as RetryableRequestConfig | undefined;
    const requestUrl = String(originalRequest?.url ?? "");

    if (!originalRequest || originalRequest._authRetry || isAuthFlowRequest(requestUrl)) {
      clearAccessToken();
      if (!requestUrl.includes(AUTH_LOGIN_PATH)) {
        redirectToLogin();
      }
      return Promise.reject(error);
    }

    originalRequest._authRetry = true;
    const newAccessToken = await refreshAccessToken();

    if (!newAccessToken) {
      redirectToLogin();
      return Promise.reject(error);
    }

    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
    return apiClient(originalRequest);
  },
);
