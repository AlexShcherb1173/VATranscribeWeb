# Stage 3.9 Marketing QA / SEO Polish / No-placeholders Sweep

Stage 3.9 performs a QA sweep of the Astro marketing layer after the marketing-to-SaaS links stage.

## Verified

- `npm run build:marketing`
- `npm run build:web`
- `docker compose exec api python -m pytest tests/security tests/privacy`
- EN/RU route coverage
- sitemap.xml generation
- robots.txt generation
- marketing-to-SaaS CTA generation
- canonical/hreflang foundation
- public content pages for blog, resources, docs and changelog

## Fixed

- Removed `vatranscribe.example.com` from the default SEO base URL.
- Added `PUBLIC_VATRANSCRIBE_MARKETING_URL` for canonical URLs, sitemap, robots.txt and JSON-LD.
- Reworded public placeholder/pending/TBD text in download, changelog, FAQ and legal content.
- Kept desktop distribution language as planned roadmap content rather than unfinished placeholder text.

## Local development URLs

Marketing:

```text
PUBLIC_VATRANSCRIBE_MARKETING_URL=http://localhost:4321
SaaS web app:

PUBLIC_VATRANSCRIBE_APP_URL=http://127.0.0.1:5175
Production note

Before deployment, set:

PUBLIC_VATRANSCRIBE_MARKETING_URL=https://your-marketing-domain
PUBLIC_VATRANSCRIBE_APP_URL=https://your-saas-app-domain

Use the real public marketing domain for canonical URLs, sitemap, robots.txt and JSON-LD.
Use the real SaaS app URL for login, registration, dashboard and billing CTA links.
