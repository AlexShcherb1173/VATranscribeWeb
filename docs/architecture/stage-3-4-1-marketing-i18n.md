# Stage 3.4.1 Marketing i18n RU/EN

Stage 3.4.1 adds bilingual public marketing routes.

## Locale model

Default locale:

- `en`

Secondary locale:

- `ru`

## Routes

English routes stay unchanged:

- `/`
- `/features`
- `/pricing`
- `/download`
- `/use-cases`
- `/docs`
- `/blog`
- `/resources`
- `/legal/*`

Russian routes are added under `/ru`:

- `/ru`
- `/ru/features`
- `/ru/pricing`
- `/ru/download`
- `/ru/use-cases`
- `/ru/docs`
- `/ru/blog`
- `/ru/resources`
- `/ru/legal/*`

## SEO

Implemented:

- `hreflang` links in `BaseLayout`
- EN/RU alternates in `sitemap.xml`
- locale-aware Header/Footer
- locale-aware pricing grid
- Russian legal document drafts

## Important

Backend consent records currently store:

- `document_type`
- `document_version`
- `accepted`

They do not store locale yet. RU and EN pages are treated as language variants of the same legal document version `1.0`.

If strict production legal evidence is required, add `document_locale` to consent records in a later backend migration.