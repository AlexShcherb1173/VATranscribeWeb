import { env } from "@/shared/config/env";

export type CookieConsentCategory = "necessary" | "analytics" | "marketing";

export type CookieConsentState = {
  version: string;
  necessary: true;
  analytics: boolean;
  marketing: boolean;
  updatedAt: string;
};

export const COOKIE_CONSENT_STORAGE_KEY = "vatranscribe.cookieConsent";

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function normalizeConsent(raw: unknown): CookieConsentState | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }

  const value = raw as Partial<CookieConsentState>;
  if (value.version !== env.cookieConsentVersion) {
    return null;
  }

  return {
    version: env.cookieConsentVersion,
    necessary: true,
    analytics: value.analytics === true,
    marketing: value.marketing === true,
    updatedAt: typeof value.updatedAt === "string" ? value.updatedAt : new Date().toISOString(),
  };
}

export function getCookieConsent(): CookieConsentState | null {
  if (!isBrowser()) {
    return null;
  }

  try {
    return normalizeConsent(JSON.parse(window.localStorage.getItem(COOKIE_CONSENT_STORAGE_KEY) || "null"));
  } catch {
    return null;
  }
}

export function saveCookieConsent(input: { analytics: boolean; marketing: boolean }): CookieConsentState {
  const consent: CookieConsentState = {
    version: env.cookieConsentVersion,
    necessary: true,
    analytics: input.analytics,
    marketing: input.marketing,
    updatedAt: new Date().toISOString(),
  };

  if (isBrowser()) {
    window.localStorage.setItem(COOKIE_CONSENT_STORAGE_KEY, JSON.stringify(consent));
    window.dispatchEvent(new CustomEvent("vatranscribe:cookie-consent-updated", { detail: consent }));
  }

  return consent;
}

export function hasConsentFor(category: CookieConsentCategory, consent: CookieConsentState | null = getCookieConsent()): boolean {
  if (category === "necessary") {
    return true;
  }

  if (!env.cookieConsentRequired) {
    return true;
  }

  if (!consent) {
    return false;
  }

  return category === "analytics" ? consent.analytics : consent.marketing;
}

export function resetCookieConsent(): void {
  if (!isBrowser()) {
    return;
  }
  window.localStorage.removeItem(COOKIE_CONSENT_STORAGE_KEY);
  window.dispatchEvent(new CustomEvent("vatranscribe:cookie-consent-updated"));
}
