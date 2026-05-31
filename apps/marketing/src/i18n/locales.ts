export const defaultLocale = "en";

export const locales = ["en", "ru"] as const;

export type Locale = (typeof locales)[number];

export const localeLabels: Record<Locale, string> = {
  en: "EN",
  ru: "RU"
};

export const localeNames: Record<Locale, string> = {
  en: "English",
  ru: "Русский"
};

export function isLocale(value: string | undefined): value is Locale {
  return value === "en" || value === "ru";
}

export function getLocaleFromPath(path: string): Locale {
  const clean = normalizePath(path);

  if (clean === "/ru" || clean.startsWith("/ru/")) {
    return "ru";
  }

  return "en";
}

export function stripLocaleFromPath(path: string): string {
  const clean = normalizePath(path);

  if (clean === "/ru") {
    return "/";
  }

  if (clean.startsWith("/ru/")) {
    return clean.slice(3) || "/";
  }

  return clean;
}

export function localizePath(path: string, locale: Locale): string {
  const clean = stripLocaleFromPath(path);

  if (locale === "en") {
    return clean;
  }

  if (clean === "/") {
    return "/ru";
  }

  return `/ru${clean}`;
}

export function normalizePath(path: string): string {
  const withoutQuery = (path || "/").split("?")[0].split("#")[0];
  const withSlash = withoutQuery.startsWith("/") ? withoutQuery : `/${withoutQuery}`;
  const withoutTrailingSlash = withSlash.length > 1 ? withSlash.replace(/\/$/, "") : withSlash;

  return withoutTrailingSlash || "/";
}

export function getAlternateLinks(path: string) {
  const basePath = stripLocaleFromPath(path);

  return [
    { locale: "en" as const, href: localizePath(basePath, "en") },
    { locale: "ru" as const, href: localizePath(basePath, "ru") },
    { locale: "x-default", href: localizePath(basePath, "en") }
  ];
}

export type LocalizedNavItem = {
  label: string;
  href: string;
};

export type LocaleContent = {
  product: {
    name: string;
    tagline: string;
    description: string;
  };
  nav: LocalizedNavItem[];
  legal: LocalizedNavItem[];
  actions: {
    login: string;
    startFree: string;
    openDashboard: string;
  };
  footer: {
    product: string;
    legal: string;
    legalCenter: string;
    rights: string;
  };
};

const enContent: LocaleContent = {
  product: {
    name: "VATranscribe",
    tagline: "Download, transcribe and manage media files in one workspace.",
    description:
      "VATranscribe is a SaaS-ready media workflow platform for downloading, converting, transcribing and organizing video and audio files."
  },
  nav: [
    { label: "Features", href: "/features" },
    { label: "Use cases", href: "/use-cases" },
    { label: "Pricing", href: "/pricing" },
    { label: "Download", href: "/download" },
    { label: "Docs", href: "/docs" }
  ],
  legal: [
    { label: "Terms", href: "/legal/terms" },
    { label: "Privacy", href: "/legal/privacy" },
    { label: "Personal Data", href: "/legal/personal-data" },
    { label: "Cookies", href: "/legal/cookies" },
    { label: "Refund Policy", href: "/legal/refund" }
  ],
  actions: {
    login: "Log in",
    startFree: "Start free",
    openDashboard: "Open dashboard"
  },
  footer: {
    product: "Product",
    legal: "Legal",
    legalCenter: "Legal center",
    rights: "All rights reserved."
  }
};

const ruContent: LocaleContent = {
  product: {
    name: "VATranscribe",
    tagline: "Скачивание, транскрибация и управление медиафайлами в одном рабочем пространстве.",
    description:
      "VATranscribe — SaaS-ready платформа для скачивания, конвертации, транскрибации и организации видео и аудиофайлов."
  },
  nav: [
    { label: "Возможности", href: "/features" },
    { label: "Сценарии", href: "/use-cases" },
    { label: "Тарифы", href: "/pricing" },
    { label: "Скачать", href: "/download" },
    { label: "Документация", href: "/docs" }
  ],
  legal: [
    { label: "Условия", href: "/legal/terms" },
    { label: "Конфиденциальность", href: "/legal/privacy" },
    { label: "Персональные данные", href: "/legal/personal-data" },
    { label: "Cookies", href: "/legal/cookies" },
    { label: "Возвраты", href: "/legal/refund" }
  ],
  actions: {
    login: "Войти",
    startFree: "Начать бесплатно",
    openDashboard: "Открыть приложение"
  },
  footer: {
    product: "Продукт",
    legal: "Документы",
    legalCenter: "Юридический центр",
    rights: "Все права защищены."
  }
};

export function getLocaleContent(locale: Locale): LocaleContent {
  return locale === "ru" ? ruContent : enContent;
}