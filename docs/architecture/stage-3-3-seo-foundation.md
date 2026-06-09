# Stage 3.3 SEO Foundation

Stage 3.3 adds the SEO infrastructure for the Astro marketing application.

## Implemented

- page-level SEO config
- canonical URLs
- OpenGraph metadata
- Twitter card metadata
- dynamic `robots.txt`
- dynamic `sitemap.xml`
- dynamic `og-image.svg`
- JSON-LD structured data
- page canonical mapping

## Files

- `apps/marketing/src/config/seo.ts`
- `apps/marketing/src/layouts/BaseLayout.astro`
- `apps/marketing/src/layouts/MarketingLayout.astro`
- `apps/marketing/src/pages/robots.txt.ts`
- `apps/marketing/src/pages/sitemap.xml.ts`
- `apps/marketing/src/pages/og-image.svg.ts`

## Structured data

The base layout emits JSON-LD for:

- `Organization`
- `WebSite`
- `SoftwareApplication`
- `WebPage`

## Notes before production

Current `siteConfig.baseUrl` uses a placeholder domain. Replace it with the production domain before public deployment.

Legal pages are still placeholders and must be replaced with reviewed legal text before launch.