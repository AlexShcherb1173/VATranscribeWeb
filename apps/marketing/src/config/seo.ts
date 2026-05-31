import { siteConfig } from "./site";

export type SeoPage = {
  path: string;
  title: string;
  description: string;
  priority: string;
  changefreq: "daily" | "weekly" | "monthly" | "yearly";
  noindex?: boolean;
};

export const seoPages: SeoPage[] = [
  {
    path: "/",
    title: "VATranscribe — Download, transcribe and organize media workflows",
    description:
      "VATranscribe is a SaaS-ready media workflow platform for downloads, MP3/MP4 conversion, transcription, quotas, audit logs and privacy workflows.",
    priority: "1.0",
    changefreq: "weekly"
  },
  {
    path: "/features",
    title: "VATranscribe Features — Downloads, transcription and SaaS security",
    description:
      "Explore VATranscribe features for media downloading, transcription workflows, user-owned files, refresh token rotation, audit logs and billing-ready architecture.",
    priority: "0.9",
    changefreq: "weekly"
  },
  {
    path: "/use-cases",
    title: "VATranscribe Use Cases — Creators, developers and teams",
    description:
      "VATranscribe use cases for creators, developers, testers and teams building controlled media processing workflows.",
    priority: "0.85",
    changefreq: "weekly"
  },
  {
    path: "/pricing",
    title: "VATranscribe Pricing — Plans for media workflow automation",
    description:
      "Compare VATranscribe plans for download workflows, transcription, quotas, media history, audit-ready flows and team-ready architecture.",
    priority: "0.9",
    changefreq: "weekly"
  },
  {
    path: "/download",
    title: "Download VATranscribe — Web dashboard and future desktop builds",
    description:
      "Open the VATranscribe web dashboard and follow the future desktop download layer for installers, checksums and release notes.",
    priority: "0.8",
    changefreq: "weekly"
  },
  {
    path: "/docs",
    title: "VATranscribe Documentation",
    description:
      "VATranscribe documentation hub for product setup, downloader workflows, transcription workflows, billing, quotas, security and privacy.",
    priority: "0.75",
    changefreq: "weekly"
  },
  {
    path: "/blog",
    title: "VATranscribe Blog",
    description:
      "Product updates, media workflow notes, downloader guides, transcription automation and SaaS build notes.",
    priority: "0.7",
    changefreq: "weekly"
  },
  {
    path: "/resources",
    title: "VATranscribe Resources",
    description:
      "Guides, checklists, comparisons and resources for building media download and transcription workflows.",
    priority: "0.65",
    changefreq: "weekly"
  },
  {
    path: "/legal/terms",
    title: "VATranscribe Terms of Service",
    description:
      "Terms of Service placeholder for VATranscribe. Replace with reviewed legal text before production launch.",
    priority: "0.35",
    changefreq: "monthly"
  },
  {
    path: "/legal/privacy",
    title: "VATranscribe Privacy Policy",
    description:
      "Privacy Policy placeholder for VATranscribe. Replace with reviewed legal text before production launch.",
    priority: "0.35",
    changefreq: "monthly"
  },
  {
    path: "/legal/personal-data",
    title: "VATranscribe Personal Data Processing Consent",
    description:
      "Personal data processing consent placeholder for VATranscribe. Replace with reviewed legal text before production launch.",
    priority: "0.3",
    changefreq: "monthly"
  },
  {
    path: "/legal/cookies",
    title: "VATranscribe Cookie Policy",
    description:
      "Cookie Policy placeholder for VATranscribe. Replace with reviewed legal text before production launch.",
    priority: "0.3",
    changefreq: "monthly"
  },
  {
    path: "/legal/refund",
    title: "VATranscribe Refund Policy",
    description:
      "Refund Policy placeholder for VATranscribe. Replace with reviewed legal text before production launch.",
    priority: "0.3",
    changefreq: "monthly"
  }
] as const;

function normalizePath(path: string): string {
  if (!path || path === "/") {
    return "/";
  }

  const clean = path.split("?")[0].split("#")[0];
  const withoutTrailingSlash = clean.length > 1 ? clean.replace(/\/$/, "") : clean;

  return withoutTrailingSlash || "/";
}

export function getSeoForPath(path: string): SeoPage | undefined {
  const normalizedPath = normalizePath(path);

  return seoPages.find((page) => normalizePath(page.path) === normalizedPath);
}

export function absoluteUrl(path: string): string {
  return new URL(path, siteConfig.baseUrl).toString();
}

export function getDefaultJsonLd(params: {
  canonical: string;
  pageTitle: string;
  description: string;
}) {
  const { canonical, pageTitle, description } = params;

  return [
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      name: siteConfig.productName,
      url: siteConfig.baseUrl,
      logo: absoluteUrl("/favicon.svg")
    },
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      name: siteConfig.productName,
      url: siteConfig.baseUrl,
      description: siteConfig.description,
      potentialAction: {
        "@type": "SearchAction",
        target: `${siteConfig.baseUrl}/resources?query={search_term_string}`,
        "query-input": "required name=search_term_string"
      }
    },
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      name: siteConfig.productName,
      applicationCategory: "MultimediaApplication",
      operatingSystem: "Web",
      url: canonical,
      description,
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD"
      }
    },
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      name: pageTitle,
      url: canonical,
      description
    }
  ];
}