import { env } from "@/shared/config/env";

type SentryBrowserSdk = {
  init?: (options: Record<string, unknown>) => void;
  captureException?: (error: unknown) => void;
  captureMessage?: (message: string, level?: string) => void;
};

declare global {
  interface Window {
    Sentry?: SentryBrowserSdk;
  }
}

export function initFrontendObservability(): void {
  if (!env.sentryDsn) {
    return;
  }

  const sentry = window.Sentry;
  if (!sentry?.init) {
    console.warn("VITE_SENTRY_DSN is set, but Sentry browser SDK is not loaded.");
    return;
  }

  sentry.init({
    dsn: env.sentryDsn,
    environment: env.sentryEnvironment,
    release: env.sentryRelease,
    tracesSampleRate: env.sentryTracesSampleRate,
    sendDefaultPii: false,
  });

  window.addEventListener("error", (event) => {
    sentry.captureException?.(event.error || event.message);
  });

  window.addEventListener("unhandledrejection", (event) => {
    sentry.captureException?.(event.reason);
  });
}
