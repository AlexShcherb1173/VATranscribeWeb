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
  analyticsProvider: (normalizeOptional(import.meta.env.VITE_ANALYTICS_PROVIDER) || "disabled") as "disabled" | "yandex" | "ga4" | "both" | "posthog" | "provider-neutral",
  analyticsEnabled: (normalizeOptional(import.meta.env.VITE_ANALYTICS_PROVIDER) || "disabled") !== "disabled",
  yandexMetrikaId: normalizeOptional(import.meta.env.VITE_YANDEX_METRIKA_ID),
  ga4MeasurementId: normalizeOptional(import.meta.env.VITE_GA4_MEASUREMENT_ID),
  posthogApiKey: normalizeOptional(import.meta.env.VITE_POSTHOG_API_KEY),
  posthogHost: normalizeOptional(import.meta.env.VITE_POSTHOG_HOST) || "https://app.posthog.com",
  cookieConsentRequired: (normalizeOptional(import.meta.env.VITE_COOKIE_CONSENT_REQUIRED) || "true") !== "false",
  cookieConsentVersion: normalizeOptional(import.meta.env.VITE_COOKIE_CONSENT_VERSION) || "2026-06-10",
  coreWebVitalsEnabled: (normalizeOptional(import.meta.env.VITE_CORE_WEB_VITALS_ENABLED) || "true") !== "false",
  coreWebVitalsReportMode: normalizeOptional(import.meta.env.VITE_CORE_WEB_VITALS_REPORT_MODE) || "analytics",
  coreWebVitalsTargets: {
    lcp: normalizeNumber(import.meta.env.VITE_CORE_WEB_VITALS_LCP_TARGET_MS, 2500),
    inp: normalizeNumber(import.meta.env.VITE_CORE_WEB_VITALS_INP_TARGET_MS, 200),
    cls: normalizeNumber(import.meta.env.VITE_CORE_WEB_VITALS_CLS_TARGET, 0.1),
  },
};
