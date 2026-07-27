export type MarketingAnalyticsProvider = "disabled" | "yandex" | "ga4" | "both" | "posthog" | "provider-neutral";

export const COOKIE_CONSENT_STORAGE_KEY = "vatranscribe.cookieConsent";

export function analyticsRequiresConsent(): boolean {
  return true;
}

export function analyticsIsDisabledByDefault(provider: MarketingAnalyticsProvider): boolean {
  return provider === "disabled" || provider === "provider-neutral";
}
