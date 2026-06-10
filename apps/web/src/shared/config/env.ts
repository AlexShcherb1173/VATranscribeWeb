const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function normalizeApiBaseUrl(value?: string): string {
  const raw = (value || DEFAULT_API_BASE_URL).trim().replace(/\/+$/, "");
  return raw.replace("http://localhost:", "http://127.0.0.1:");
}

function normalizeOptional(value?: string): string | undefined {
  const raw = (value || "").trim();
  return raw.length > 0 ? raw : undefined;
}

function normalizeNumber(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export const env = {
  apiBaseUrl: normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL),
  sentryDsn: normalizeOptional(import.meta.env.VITE_SENTRY_DSN),
  sentryEnvironment: normalizeOptional(import.meta.env.VITE_SENTRY_ENVIRONMENT) || import.meta.env.MODE,
  sentryRelease: normalizeOptional(import.meta.env.VITE_SENTRY_RELEASE),
  sentryTracesSampleRate: normalizeNumber(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE, 0),
};
