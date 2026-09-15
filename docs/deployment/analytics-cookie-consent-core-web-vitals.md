# P2-08 Analytics, Cookie Consent and Core Web Vitals

## Objective

P2-08 activates the production-ready analytics foundation without enabling tracking by default.
Analytics scripts must never load before the user has granted analytics consent.

## Providers

Supported provider modes:

- `disabled` — default and safest mode.
- `yandex` — Yandex Metrika loaded from `YANDEX_METRIKA_ID` / `VITE_YANDEX_METRIKA_ID` / `PUBLIC_YANDEX_METRIKA_ID`.
- `ga4` — GA4 loaded from `GA4_MEASUREMENT_ID` / `VITE_GA4_MEASUREMENT_ID` / `PUBLIC_GA4_MEASUREMENT_ID`.
- `both` — Yandex Metrika and GA4.
- `posthog` — reserved for a consent-aware PostHog bootstrap.
- `provider-neutral` — documentation/integration placeholder.

No tracking IDs are hardcoded in source code. All IDs must come from runtime/build environment variables.

## Cookie consent model

Consent is versioned with `COOKIE_CONSENT_VERSION` / `VITE_COOKIE_CONSENT_VERSION` / `PUBLIC_COOKIE_CONSENT_VERSION`.

Categories:

| Category | Default | Purpose |
| --- | --- | --- |
| necessary | enabled | authentication, CSRF, session security, language/interface storage |
| analytics | disabled | product analytics and Core Web Vitals reporting |
| marketing | disabled | marketing pixels and advertising attribution |

The browser stores consent in `localStorage` under `vatranscribe.cookieConsent`.

## Core Web Vitals

Targets:

- LCP < 2.5s
- INP < 200ms
- CLS < 0.1

Core Web Vitals reporting is allowed only after analytics consent. Until a real analytics provider is enabled, use Lighthouse/PageSpeed reports and the checklist in `docs/performance/core-web-vitals-checklist.md`.

## Release checklist

1. Set `ANALYTICS_PROVIDER=disabled` until legal and tracking IDs are final.
2. If enabling Yandex Metrika, set all Yandex env IDs and update legal processor records.
3. If enabling GA4, set all GA4 env IDs and update legal processor records.
4. Confirm cookie banner appears on marketing and app surfaces.
5. Confirm no analytics network request is made before analytics consent.
6. Confirm analytics network requests start only after analytics consent.
7. Run Lighthouse on marketing home, pricing, app login, and app dashboard.
8. Archive the Lighthouse report in release artifacts.
