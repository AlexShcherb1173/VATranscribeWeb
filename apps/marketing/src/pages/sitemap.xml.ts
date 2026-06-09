import { allSeoPages } from "../config/seo";
import { siteConfig } from "../config/site";
import { getAlternateLinks } from "../i18n/locales";

function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export function GET() {
  const lastmod = new Date().toISOString().split("T")[0];

  const urls = allSeoPages
    .filter((page) => !page.noindex)
    .map((page) => {
      const loc = new URL(page.path, siteConfig.baseUrl).toString();
      const alternates = getAlternateLinks(page.path)
        .map((link) => {
          const href = new URL(link.href, siteConfig.baseUrl).toString();

          return `    <xhtml:link rel="alternate" hreflang="${escapeXml(link.locale)}" href="${escapeXml(href)}" />`;
        })
        .join("\n");

      return [
        "  <url>",
        `    <loc>${escapeXml(loc)}</loc>`,
        alternates,
        `    <lastmod>${lastmod}</lastmod>`,
        `    <changefreq>${page.changefreq}</changefreq>`,
        `    <priority>${page.priority}</priority>`,
        "  </url>"
      ].join("\n");
    })
    .join("\n");

  const body = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    urls,
    "</urlset>"
  ].join("\n");

  return new Response(body, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8"
    }
  });
}