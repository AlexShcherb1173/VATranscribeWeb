# Stage 3.1 Marketing App Foundation

This stage introduces `apps/marketing` as a standalone Astro static site.

## Purpose

The marketing app is responsible for:

- public landing pages
- SEO pages
- pricing pages
- download pages
- legal pages
- blog/resources/docs foundation

## Separation

- `apps/marketing` — public static marketing site
- `apps/web` — authenticated SaaS dashboard
- `apps/api` — FastAPI backend
- `apps/admin` — future internal admin panel

## Local commands

```powershell
npm install
npm run dev:marketing
npm run build:marketing
npm run preview:marketing



Current routes
/
/features
/pricing
/download
/use-cases
/docs
/blog
/resources
/legal/terms
/legal/privacy
/legal/personal-data
/legal/cookies
/legal/refund
Production notes

The legal pages are placeholders and must be replaced with reviewed legal text before launch.
The Astro config uses a placeholder domain and must be changed before deployment.
