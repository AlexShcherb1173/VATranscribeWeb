export const CORE_WEB_VITALS_TARGETS = {
  LCP: 2500,
  INP: 200,
  CLS: 0.1,
} as const;

export function shouldReportCoreWebVitalsAfterConsent(hasAnalyticsConsent: boolean): boolean {
  return hasAnalyticsConsent === true;
}
