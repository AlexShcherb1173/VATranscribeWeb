import type { Locale } from "../i18n/locales";
import { getSaasLink } from "./links";

export type DownloadPlatform = {
  code: "web" | "windows" | "macos" | "linux" | "cli";
  title: string;
  status: string;
  description: string;
  version: string;
  cta: string;
  href: string;
  disabled?: boolean;
  meta: string[];
};

export type SystemRequirement = {
  label: string;
  value: string;
};

export type ReleaseNote = {
  version: string;
  date: string;
  status: string;
  items: string[];
};

export type DownloadFaqItem = {
  question: string;
  answer: string;
};

export type DownloadContent = {
  eyebrow: string;
  title: string;
  lead: string;
  primaryCta: string;
  primaryHref: string;
  secondaryCta: string;
  secondaryHref: string;
  trustBadges: string[];
  platformsTitle: string;
  platformsLead: string;
  requirementsTitle: string;
  requirementsLead: string;
  releaseTitle: string;
  releaseLead: string;
  checksumTitle: string;
  checksumLead: string;
  faqTitle: string;
  faqLead: string;
  finalTitle: string;
  finalLead: string;
  finalPrimary: string;
  finalSecondary: string;
  platforms: DownloadPlatform[];
  requirements: SystemRequirement[];
  releaseNotes: ReleaseNote[];
  faq: DownloadFaqItem[];
};

export const downloadContentEn: DownloadContent = {
  eyebrow: "Download layer",
  title: "Access the web app now. Prepare desktop distribution next.",
  lead:
    "VATranscribe currently runs as a web dashboard with API-backed media workflows. The download page is prepared for future desktop installers, release notes, checksums and platform-specific builds.",
  primaryCta: "Open web app",
  primaryHref: getSaasLink("register"),
  secondaryCta: "Read docs",
  secondaryHref: "/docs",
  trustBadges: [
    "Web dashboard available",
    "Desktop roadmap prepared",
    "Checksum section prepared",
    "Release notes structure"
  ],
  platformsTitle: "Distribution channels",
  platformsLead:
    "The current production path is the web dashboard. Desktop and CLI distribution are prepared as a public product surface.",
  requirementsTitle: "System requirements",
  requirementsLead:
    "Desktop requirements will be finalized when signed platform builds are produced and tested.",
  releaseTitle: "Release notes preview",
  releaseLead:
    "Use this section later for public version history, release channels and installer integrity data.",
  checksumTitle: "Integrity and signatures",
  checksumLead:
    "Checksums and signatures are reserved for the first signed installer release. Add SHA256 values and signing details when installers are published.",
  faqTitle: "Download FAQ",
  faqLead:
    "Short answers about the current web app, future desktop builds and installer verification.",
  finalTitle: "Start with the web app.",
  finalLead:
    "The fastest path today is the authenticated web dashboard. Desktop installers can be added when the desktop runtime is production-ready.",
  finalPrimary: "Open web app",
  finalSecondary: "View pricing",
  platforms: [
    {
      code: "web",
      title: "Web dashboard",
      status: "Available",
      description:
        "Use the browser-based SaaS dashboard for auth, downloads, files, transcripts, billing overview and privacy flows.",
      version: "dev",
      cta: "Open web app",
      href: getSaasLink("register"),
      meta: ["No installer", "Works in modern browsers", "Connected to API"]
    },
    {
      code: "windows",
      title: "Windows desktop",
      status: "Planned",
      description:
        "Future Windows installer for local desktop workflows and bundled runtime integration.",
      version: "planned release",
      cta: "Coming later",
      href: "#release-notes",
      disabled: true,
      meta: ["Windows 10/11", "Tauri foundation", "Checksum required"]
    },
    {
      code: "macos",
      title: "macOS desktop",
      status: "Planned",
      description:
        "Future macOS build for users who prefer a local desktop entry point.",
      version: "planned release",
      cta: "Coming later",
      href: "#release-notes",
      disabled: true,
      meta: ["Apple Silicon / Intel target", "Not signed yet", "Not notarized yet"]
    },
    {
      code: "linux",
      title: "Linux desktop",
      status: "Planned",
      description:
        "Future Linux package for local workflows, testing and developer usage.",
      version: "planned release",
      cta: "Coming later",
      href: "#release-notes",
      disabled: true,
      meta: ["AppImage/deb/rpm target", "Runtime packaging planned", "Checksum required"]
    },
    {
      code: "cli",
      title: "CLI / worker tools",
      status: "Internal roadmap",
      description:
        "Developer-oriented tools for controlled local processing and worker diagnostics.",
      version: "planned release",
      cta: "Read docs",
      href: "/docs",
      meta: ["Developer workflow", "Not public yet", "Docs first"]
    }
  ],
  requirements: [
    { label: "Web app", value: "Modern Chromium, Firefox, Safari or Edge browser." },
    { label: "API access", value: "Backend API and worker stack must be running for media jobs." },
    { label: "Desktop runtime", value: "Tauri-based desktop shell is present as a project foundation, not a release." },
    { label: "Storage", value: "Depends on downloaded media, transcripts and local runtime cache." },
    { label: "Network", value: "Required for URL analysis, downloads, auth and billing flows." }
  ],
  releaseNotes: [
    {
      version: "0.1.0-web",
      date: "2026-05-31",
      status: "Development",
      items: [
        "Web dashboard is the primary access path.",
        "Public download page structure added.",
        "Desktop distribution roadmap added.",
        "Checksums and signatures reserved for real installers."
      ]
    }
  ],
  faq: [
    {
      question: "Can I download the desktop app now?",
      answer:
        "Not yet. The project has a desktop foundation, but public installers are scheduled for a later release stage."
    },
    {
      question: "Which option should I use today?",
      answer:
        "Use the web dashboard. It is the current supported access path for authenticated workflows."
    },
    {
      question: "Will installers have checksums?",
      answer:
        "Yes. When desktop builds are published, the download page should include SHA256 checksums and signing details."
    },
    {
      question: "Does the download page require backend changes?",
      answer:
        "No. Stage 3.6 is a marketing/distribution surface. Release storage or version APIs can be added later."
    }
  ]
};

export const downloadContentRu: DownloadContent = {
  eyebrow: "Download layer",
  title: "Web app доступен сейчас. Desktop distribution готовим следующим шагом.",
  lead:
    "VATranscribe сейчас работает как web dashboard с API-backed media workflows. Страница скачивания подготовлена для будущих desktop installers, release notes, checksums и platform-specific builds.",
  primaryCta: "Открыть web app",
  primaryHref: getSaasLink("register"),
  secondaryCta: "Документация",
  secondaryHref: "/ru/docs",
  trustBadges: [
    "Web dashboard доступен",
    "Desktop roadmap подготовлен",
    "Checksum section prepared",
    "Структура release notes"
  ],
  platformsTitle: "Каналы распространения",
  platformsLead:
    "Текущий production path — web dashboard. Desktop и CLI distribution подготовлены как публичная продуктовая поверхность.",
  requirementsTitle: "Системные требования",
  requirementsLead:
    "Требования будут финализированы после подготовки и тестирования подписанных desktop builds.",
  releaseTitle: "Release notes preview",
  releaseLead:
    "Позже этот блок будет использоваться для публичной истории версий, release channels и installer integrity data.",
  checksumTitle: "Integrity и подписи",
  checksumLead:
    "Checksums и signatures зарезервированы для первого подписанного installer release. Реальные SHA256 и signing details добавляются при публикации installers.",
  faqTitle: "FAQ по скачиванию",
  faqLead:
    "Короткие ответы про текущий web app, будущие desktop builds и проверку installers.",
  finalTitle: "Начните с web app.",
  finalLead:
    "Самый быстрый путь сейчас — authenticated web dashboard. Desktop installers можно добавить, когда desktop runtime будет production-ready.",
  finalPrimary: "Открыть web app",
  finalSecondary: "Смотреть тарифы",
  platforms: [
    {
      code: "web",
      title: "Web dashboard",
      status: "Доступно",
      description:
        "Browser-based SaaS dashboard для auth, downloads, files, transcripts, billing overview и privacy flows.",
      version: "dev",
      cta: "Открыть web app",
      href: getSaasLink("register"),
      meta: ["Без installer", "Современные браузеры", "Связь с API"]
    },
    {
      code: "windows",
      title: "Windows desktop",
      status: "Запланировано",
      description:
        "Будущий Windows installer для локальных desktop workflows и bundled runtime integration.",
      version: "запланированный release",
      cta: "Позже",
      href: "#release-notes",
      disabled: true,
      meta: ["Windows 10/11", "Tauri foundation", "Нужен checksum"]
    },
    {
      code: "macos",
      title: "macOS desktop",
      status: "Запланировано",
      description:
        "Будущий macOS build для пользователей, которым нужен локальный desktop entry point.",
      version: "запланированный release",
      cta: "Позже",
      href: "#release-notes",
      disabled: true,
      meta: ["Apple Silicon / Intel target", "Пока без подписи", "Notarization позже"]
    },
    {
      code: "linux",
      title: "Linux desktop",
      status: "Запланировано",
      description:
        "Будущий Linux package для локальных workflows, тестирования и developer usage.",
      version: "запланированный release",
      cta: "Позже",
      href: "#release-notes",
      disabled: true,
      meta: ["AppImage/deb/rpm target", "Runtime packaging planned", "Нужен checksum"]
    },
    {
      code: "cli",
      title: "CLI / worker tools",
      status: "В roadmap",
      description:
        "Developer-oriented tools для local processing и worker diagnostics.",
      version: "запланированный release",
      cta: "Документация",
      href: "/ru/docs",
      meta: ["Developer workflow", "Пока не public", "Сначала docs"]
    }
  ],
  requirements: [
    { label: "Web app", value: "Современный Chromium, Firefox, Safari или Edge." },
    { label: "API access", value: "Backend API и worker stack должны быть запущены для media jobs." },
    { label: "Desktop runtime", value: "Tauri desktop shell есть как foundation, но это ещё не release." },
    { label: "Storage", value: "Зависит от downloaded media, transcripts и local runtime cache." },
    { label: "Network", value: "Нужна для URL analysis, downloads, auth и billing flows." }
  ],
  releaseNotes: [
    {
      version: "0.1.0-web",
      date: "2026-05-31",
      status: "Development",
      items: [
        "Web dashboard — основной способ доступа.",
        "Добавлена структура публичной download page.",
        "Добавлен desktop distribution roadmap.",
        "Checksums и signatures зарезервированы для реальных installers."
      ]
    }
  ],
  faq: [
    {
      question: "Desktop app уже можно скачать?",
      answer:
        "Пока нет. В проекте есть desktop foundation, но публичные installers на этом этапе не опубликованы."
    },
    {
      question: "Что использовать сейчас?",
      answer:
        "Используйте web dashboard. Это текущий поддерживаемый путь для authenticated workflows."
    },
    {
      question: "У installers будут checksums?",
      answer:
        "Да. Когда desktop builds будут опубликованы, download page должна содержать SHA256 checksums и signing details."
    },
    {
      question: "Для download page нужен backend?",
      answer:
        "Нет. Stage 3.6 — это marketing/distribution surface. Release storage или version API можно добавить позже."
    }
  ]
};

export function getDownloadContent(locale: Locale = "en"): DownloadContent {
  return locale === "ru" ? downloadContentRu : downloadContentEn;
}
