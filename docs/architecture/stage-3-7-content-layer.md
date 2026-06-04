# Stage 3.7 Blog / Resources / Docs / Changelog

Stage 3.7 adds a config-driven public content layer to the Astro marketing app.

## Implemented routes

English:

- `/blog`
- `/blog/[slug]`
- `/resources`
- `/resources/[slug]`
- `/docs`
- `/changelog`

Russian:

- `/ru/blog`
- `/ru/blog/[slug]`
- `/ru/resources`
- `/ru/resources/[slug]`
- `/ru/docs`
- `/ru/changelog`

## Content model

Content is stored in:

- `apps/marketing/src/config/content.ts`

This keeps Stage 3.7 simple and reviewable without adding MDX/content collections yet.

## Content included

Blog:

- media download and transcription workflow
- security and privacy foundation
- bilingual Astro marketing layer

Resources:

- media workflow checklist
- security and privacy checklist
- pricing and quotas checklist

Docs:

- getting started
- download workflow
- transcription workflow
- billing and quotas
- security and privacy

Changelog:

- Stage 3.7 content layer
- Stage 3.6 download layer
- Stage 3.5 pricing/backend alignment

## SEO

The content detail pages and changelog pages are added to `allSeoPages`, so they are included in sitemap generation and BaseLayout SEO lookup.
