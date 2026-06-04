import { siteConfig } from "./site";
import { getLocaleFromPath, localizePath, stripLocaleFromPath } from "../i18n/locales";
import type { Locale } from "../i18n/locales";

export type SeoPage = {
  path: string;
  title: string;
  description: string;
  priority: string;
  changefreq: "daily" | "weekly" | "monthly" | "yearly";
  locale?: Locale;
  noindex?: boolean;
};

const enSeoPages: SeoPage[] = [
  {
    path: "/",
    title: "VATranscribe — Download, transcribe and organize media workflows",
    description:
      "VATranscribe is a SaaS-ready media workflow platform for downloads, MP3/MP4 conversion, transcription, quotas, audit logs and privacy workflows.",
    priority: "1.0",
    changefreq: "weekly",
    locale: "en"
  },
  {
    path: "/features",
    title: "VATranscribe Features — Downloads, transcription and SaaS security",
    description:
      "Explore VATranscribe features for media downloading, transcription workflows, user-owned files, refresh token rotation, audit logs and billing-ready architecture.",
    priority: "0.9",
    changefreq: "weekly",
    locale: "en"
  },
  {
    path: "/use-cases",
    title: "VATranscribe Use Cases — Creators, developers and teams",
    description:
      "VATranscribe use cases for creators, developers, testers and teams building controlled media processing workflows.",
    priority: "0.85",
    changefreq: "weekly",
    locale: "en"
  },
  {
    path: "/pricing",
    title: "VATranscribe Pricing — Plans for media workflow automation",
    description:
      "Compare VATranscribe plans for download workflows, transcription, quotas, media history, audit-ready flows and team-ready architecture.",
    priority: "0.9",
    changefreq: "weekly",
    locale: "en"
  },
  {
    path: "/download",
    title: "Download VATranscribe — Web app, desktop roadmap and release notes",
    description:
      "Open the VATranscribe web app and follow the desktop distribution roadmap with installers, release notes, checksums and platform requirements.",
    priority: "0.8",
    changefreq: "weekly",
    locale: "en"
  },
  {
    path: "/docs",
    title: "VATranscribe Documentation",
    description:
      "VATranscribe documentation hub for product setup, downloader workflows, transcription workflows, billing, quotas, security and privacy.",
    priority: "0.75",
    changefreq: "weekly",
    locale: "en"
  },
  {
    path: "/blog",
    title: "VATranscribe Blog",
    description:
      "Product updates, media workflow notes, downloader guides, transcription automation and SaaS build notes.",
    priority: "0.7",
    changefreq: "weekly",
    locale: "en"
  },
  {
    path: "/resources",
    title: "VATranscribe Resources",
    description:
      "Guides, checklists, comparisons and resources for building media download and transcription workflows.",
    priority: "0.65",
    changefreq: "weekly",
    locale: "en"
  },
  {
    path: "/legal",
    title: "VATranscribe Legal Center",
    description:
      "VATranscribe legal center with Terms, Privacy Policy, Personal Data Processing Consent, Cookie Policy and Refund Policy.",
    priority: "0.4",
    changefreq: "monthly",
    locale: "en"
  },
  {
    path: "/legal/terms",
    title: "VATranscribe Terms of Service",
    description:
      "Terms governing access to VATranscribe, including account use, media processing, subscriptions, acceptable use and service limitations.",
    priority: "0.35",
    changefreq: "monthly",
    locale: "en"
  },
  {
    path: "/legal/privacy",
    title: "VATranscribe Privacy Policy",
    description:
      "Privacy Policy describing what data VATranscribe may collect, how it is used, how long it is kept and how users can request access or deletion.",
    priority: "0.35",
    changefreq: "monthly",
    locale: "en"
  },
  {
    path: "/legal/personal-data",
    title: "VATranscribe Personal Data Processing Consent",
    description:
      "Consent text for processing personal data needed for account creation, authentication, media workflow operation, audit logs and privacy requests.",
    priority: "0.3",
    changefreq: "monthly",
    locale: "en"
  },
  {
    path: "/legal/cookies",
    title: "VATranscribe Cookie Policy",
    description:
      "Cookie Policy explaining essential cookies, local storage, analytics cookies and future tracking technology controls.",
    priority: "0.3",
    changefreq: "monthly",
    locale: "en"
  },
  {
    path: "/legal/refund",
    title: "VATranscribe Refund Policy",
    description:
      "Refund Policy draft for future subscriptions, plan changes, failed payments, trials and exceptional refunds.",
    priority: "0.3",
    changefreq: "monthly",
    locale: "en"
  }
];

const ruSeoMap: Record<string, Pick<SeoPage, "title" | "description">> = {
  "/": {
    title: "VATranscribe — скачивание, транскрибация и организация медиа",
    description:
      "VATranscribe — SaaS-ready платформа для скачивания, MP3/MP4, транскрибации, квот, audit logs и privacy workflows."
  },
  "/features": {
    title: "Возможности VATranscribe — скачивание, транскрибация и security",
    description:
      "Возможности VATranscribe для media downloads, транскрибации, user-owned files, refresh token rotation, audit logs и billing-ready архитектуры."
  },
  "/use-cases": {
    title: "Сценарии VATranscribe — авторы, разработчики и команды",
    description:
      "Сценарии использования VATranscribe для авторов, разработчиков, тестирования и командной обработки медиа."
  },
  "/pricing": {
    title: "Тарифы VATranscribe — планы для media workflow automation",
    description:
      "Сравнение тарифов VATranscribe для скачивания, транскрибации, квот, истории медиа и team-ready архитектуры."
  },
  "/download": {
    title: "Скачать VATranscribe — web app, desktop roadmap и release notes",
    description:
      "Откройте web app VATranscribe и следите за desktop distribution roadmap: installers, release notes, checksums и platform requirements."
  },
  "/docs": {
    title: "Документация VATranscribe",
    description:
      "Документация VATranscribe по setup, downloader workflows, transcription workflows, billing, quotas, security и privacy."
  },
  "/blog": {
    title: "Блог VATranscribe",
    description:
      "Новости продукта, заметки по media workflows, downloader guides, transcription automation и SaaS build notes."
  },
  "/resources": {
    title: "Ресурсы VATranscribe",
    description:
      "Гайды, чеклисты, сравнения и материалы по media download и transcription workflows."
  },
  "/legal": {
    title: "Юридический центр VATranscribe",
    description:
      "Юридический центр VATranscribe: условия, политика конфиденциальности, персональные данные, cookies и возвраты."
  },
  "/legal/terms": {
    title: "Условия использования VATranscribe",
    description:
      "Условия доступа к VATranscribe: аккаунт, обработка медиа, подписки, допустимое использование и ограничения сервиса."
  },
  "/legal/privacy": {
    title: "Политика конфиденциальности VATranscribe",
    description:
      "Политика описывает, какие данные может обрабатывать VATranscribe, зачем они используются, как хранятся и как пользователь может запросить доступ или удаление."
  },
  "/legal/personal-data": {
    title: "Согласие на обработку персональных данных VATranscribe",
    description:
      "Согласие на обработку персональных данных для аккаунта, аутентификации, media workflows, audit logs и privacy requests."
  },
  "/legal/cookies": {
    title: "Политика cookies VATranscribe",
    description:
      "Политика cookies описывает essential cookies, local storage, analytics cookies и будущие настройки tracking technologies."
  },
  "/legal/refund": {
    title: "Политика возвратов VATranscribe",
    description:
      "Черновик политики возвратов для будущих подписок, смены тарифов, ошибок платежей, trial-периодов и исключительных возвратов."
  }
};

const ruSeoPages: SeoPage[] = enSeoPages.map((page) => {
  const basePath = stripLocaleFromPath(page.path);
  const ruSeo = ruSeoMap[basePath] ?? {
    title: page.title,
    description: page.description
  };

  return {
    ...page,
    path: localizePath(basePath, "ru"),
    title: ruSeo.title,
    description: ruSeo.description,
    locale: "ru"
  };
});

export const seoPages: SeoPage[] = enSeoPages;
export const allSeoPages: SeoPage[] = [...enSeoPages, ...ruSeoPages];

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

  return allSeoPages.find((page) => normalizePath(page.path) === normalizedPath);
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
  const locale = getLocaleFromPath(canonical);

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
      inLanguage: locale
    },
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      name: siteConfig.productName,
      applicationCategory: "MultimediaApplication",
      operatingSystem: "Web",
      url: canonical,
      description,
      inLanguage: locale,
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
      description,
      inLanguage: locale
    }
  ];
}