# Core Web Vitals Checklist

Targets for production pages:

| Metric | Target |
| --- | --- |
| LCP | < 2.5s |
| INP | < 200ms |
| CLS | < 0.1 |

## Pages to test

- Marketing home: `https://vatranscribe.ru/`
- Pricing: `https://vatranscribe.ru/pricing`
- App login/register: `https://app.vatranscribe.ru/`
- Dashboard after login: `https://app.vatranscribe.ru/app`

## Required release evidence

- Lighthouse report for every key page.
- No analytics scripts before consent.
- No marketing pixels before marketing consent.
- Hashed static assets served with long cache TTL.
- HTML served with no-cache or short TTL.
