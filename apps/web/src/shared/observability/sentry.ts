import * as Sentry from "@sentry/react";

import { env } from "@/shared/config/env";

let sentryInitialized = false;

export function initFrontendObservability(): void {
  if (!env.sentryDsn || sentryInitialized) {
    return;
  }

  Sentry.init({
    dsn: env.sentryDsn,
    environment: env.sentryEnvironment,
    release: env.sentryRelease,
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: env.sentryTracesSampleRate,
    sendDefaultPii: false,
  });

  sentryInitialized = true;
}

export function captureFrontendException(error: unknown): void {
  if (!env.sentryDsn || !sentryInitialized) {
    return;
  }

  Sentry.captureException(error);
}