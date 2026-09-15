import axios from "axios";

import { clearAccessToken, getAccessToken } from "@/shared/auth/token";
import { env } from "@/shared/config/env";

export const apiClient = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    "сервер API/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      const requestUrl = String(error?.config?.url ?? "");
      const isLoginRequest = requestUrl.includes("/auth/login");

      clearAccessToken();

      if (!isLoginRequest) {
        const currentPath =
          window.location.pathname + window.location.search + window.location.hash;

        if (currentPath !== "/" && currentPath !== "/auth") {
          sessionStorage.setItem("vatranscribe_redirect_after_login", currentPath);
        }

        if (window.location.pathname !== "/") {
          window.location.assign("/");
        }
      }
    }

    return Promise.reject(error);
  },
);

