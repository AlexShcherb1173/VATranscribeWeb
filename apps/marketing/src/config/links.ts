import { localizePath } from "../i18n/locales";
import type { Locale } from "../i18n/locales";

export type PlanCode = "free" | "pro" | "business";

export type SaasTarget =
  | "login"
  | "register"
  | "dashboard"
  | "downloads"
  | "billing"
  | "pricing"
  | "settings";

export type SaasLinkOptions = {
  plan?: PlanCode;
  redirectTo?: string;
};

const DEFAULT_SAAS_BASE_URL = "http://127.0.0.1:5175";

const SAAS_PATHS: Record<SaasTarget, string> = {
  login: "/auth/login",
  register: "/auth/register",
  dashboard: "/app",
  downloads: "/app/downloads",
  billing: "/app/billing",
  pricing: "/pricing",
  settings: "/app/settings"
};

export function getSaasBaseUrl(): string {
  const raw = import.meta.env.PUBLIC_VATRANSCRIBE_APP_URL || DEFAULT_SAAS_BASE_URL;
  return String(raw).trim().replace(/\/+$/, "");
}

export function getSaasPath(target: SaasTarget, options: SaasLinkOptions = {}): string {
  const path = SAAS_PATHS[target];
  const params = new URLSearchParams();

  if (options.plan) {
    params.set("plan", options.plan);
  }

  if (options.redirectTo) {
    params.set("redirectTo", options.redirectTo);
  }

  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

export function getSaasLink(target: SaasTarget, options: SaasLinkOptions = {}): string {
  const base = getSaasBaseUrl();
  const path = getSaasPath(target, options);
  return new URL(path, `${base}/`).toString();
}

export function getMarketingPath(path: string, locale: Locale = "en"): string {
  return localizePath(path, locale);
}
