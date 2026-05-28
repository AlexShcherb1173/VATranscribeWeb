const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function normalizeApiBaseUrl(value?: string): string {
  const raw = (value || DEFAULT_API_BASE_URL).trim().replace(/\/+$/, "");
  return raw.replace("http://localhost:", "http://127.0.0.1:");
}

export const env = {
  apiBaseUrl: normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL),
};