import { env } from "@/shared/config/env";
import { getCookieConsent, hasConsentFor } from "@/shared/cookies/consent";

declare global {
  interface Window {
    ym?: (...args: unknown[]) => void;
    gtag?: (...args: unknown[]) => void;
    dataLayer?: unknown[];
    posthog?: { init?: (...args: unknown[]) => void; capture?: (...args: unknown[]) => void };
  }
}

type AnalyticsProvider = "disabled" | "yandex" | "ga4" | "both" | "posthog" | "provider-neutral";

let analyticsBootstrapped = false;

function shouldUseProvider(provider: AnalyticsProvider, candidate: AnalyticsProvider): boolean {
  return provider === candidate || provider === "both";
}

function appendScript(id: string, src: string, inline?: string): void {
  if (document.getElementById(id)) {
    return;
  }

  const script = document.createElement("script");
  script.id = id;
  script.async = true;
  if (src) {
    script.src = src;
  }
  if (inline) {
    script.text = inline;
  }
  document.head.appendChild(script);
}

function initYandexMetrika(): void {
  const id = env.yandexMetrikaId;
  if (!id) {
    return;
  }

  window.ym = window.ym || function ymShim(...args: unknown[]) {
    (window.ym as unknown as { a?: unknown[][] }).a = (window.ym as unknown as { a?: unknown[][] }).a || [];
    (window.ym as unknown as { a?: unknown[][] }).a?.push(args);
  };

  appendScript("vatranscribe-yandex-metrika", `https://mc.yandex.ru/metrika/tag.js`);
  window.ym(Number(id), "init", {
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
    webvisor: false,
  });
}

function initGa4(): void {
  const id = env.ga4MeasurementId;
  if (!id) {
    return;
  }

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function gtagShim(...args: unknown[]) {
    window.dataLayer?.push(args);
  };

  appendScript("vatranscribe-ga4", `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(id)}`);
  window.gtag("js", new Date());
  window.gtag("config", id, { anonymize_ip: true, send_page_view: true });
}

function initPostHog(): void {
  if (!env.posthogApiKey) {
    return;
  }

  // P2-08 keeps PostHog provider-neutral: load through a separately approved snippet later.
  window.posthog?.init?.(env.posthogApiKey, {
    api_host: env.posthogHost,
    capture_pageview: true,
    autocapture: false,
  });
}

export function initConsentAwareAnalytics(): void {
  if (analyticsBootstrapped || !env.analyticsEnabled) {
    return;
  }

  const consent = getCookieConsent();
  if (!consent || !hasConsentFor("analytics", consent)) {
    return;
  }

  analyticsBootstrapped = true;
  const provider = env.analyticsProvider;

  if (shouldUseProvider(provider, "yandex")) {
    initYandexMetrika();
  }

  if (shouldUseProvider(provider, "ga4")) {
    initGa4();
  }

  if (provider === "posthog") {
    initPostHog();
  }
}

export function trackAnalyticsEvent(name: string, params: Record<string, unknown> = {}): void {
  if (!analyticsBootstrapped || !hasConsentFor("analytics")) {
    return;
  }

  if (env.ga4MeasurementId && window.gtag) {
    window.gtag("event", name, params);
  }

  if (env.yandexMetrikaId && window.ym) {
    window.ym(Number(env.yandexMetrikaId), "reachGoal", name, params);
  }

  window.posthog?.capture?.(name, params);
}

if (typeof window !== "undefined") {
  window.addEventListener("vatranscribe:cookie-consent-updated", () => {
    initConsentAwareAnalytics();
  });
}
