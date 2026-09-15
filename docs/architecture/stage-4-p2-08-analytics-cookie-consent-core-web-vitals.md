# Stage 4 / P2-08 — Analytics, Cookie Consent and Core Web Vitals

## Status

`P2-08_analytics_cookie_consent_core_web_vitals` adds the consent-aware analytics layer.

## Decisions

- Analytics provider is disabled by default.
- Yandex Metrika and GA4 are supported through environment variables.
- Cookie consent categories are `necessary`, `analytics`, and `marketing`.
- Analytics and marketing are off by default.
- Consent is stored in browser `localStorage` with version `2026-06-10`.
- Core Web Vitals may be reported only after analytics consent.
- Admin analytics is intentionally disabled.

## Production gate

Before analytics can be enabled in production:

1. tracking IDs must be configured through env/vault only;
2. cookie consent must be present on marketing and app surfaces;
3. legal cookie policy and personal data map must describe analytics processors;
4. no analytics network requests may occur before analytics consent;
5. Lighthouse/Core Web Vitals evidence must be attached to the release.

## Files

- `apps/web/src/shared/analytics/analytics.ts`
- `apps/web/src/shared/cookies/consent.ts`
- `apps/web/src/shared/core-web-vitals/coreWebVitals.ts`
- `apps/web/src/widgets/cookie-consent/CookieConsentBanner.tsx`
- `apps/marketing/src/components/CookieConsent.astro`
- `apps/marketing/src/scripts/analytics.ts`
- `apps/marketing/src/scripts/coreWebVitals.ts`
- `docs/deployment/analytics-cookie-consent-core-web-vitals.md`
- `docs/legal/cookie-policy.md`
- `docs/performance/core-web-vitals-checklist.md`
