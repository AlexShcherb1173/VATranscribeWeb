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
  eyebrow: "Скачать",
  title: "Веб-приложение доступно сейчас. Настольные версии подготовим следующим шагом.",
  lead:
    "VATranscribe сейчас работает как веб-кабинет с медиа-задачами через API. Страница скачивания подготовлена для будущих установщиков, заметок к релизу, контрольных сумм и сборок под разные платформы.",
  primaryCta: "Открыть веб-приложение",
  primaryHref: getSaasLink("register"),
  secondaryCta: "Документация",
  secondaryHref: "/ru/docs",
  trustBadges: [
    "Веб-кабинет доступен",
    "План настольных версий подготовлен",
    "Раздел контрольных сумм подготовлен",
    "Структура заметок к релизу"
  ],
  platformsTitle: "Каналы распространения",
  platformsLead:
    "Текущий рабочий путь — веб-кабинет. Настольные версии и инструменты командной строки подготовлены как будущие каналы распространения.",
  requirementsTitle: "Системные требования",
  requirementsLead:
    "Требования будут финализированы после подготовки и тестирования подписанных настольных сборок.",
  releaseTitle: "Заметки к релизу",
  releaseLead:
    "Позже этот блок будет использоваться для публичной истории версий, каналов релизов и данных проверки установщиков.",
  checksumTitle: "Целостность и подписи",
  checksumLead:
    "Контрольные суммы и подписи зарезервированы для первого подписанного установщика. Реальные SHA256 и данные подписи добавляются при публикации установщиков.",
  faqTitle: "FAQ по скачиванию",
  faqLead:
    "Короткие ответы про текущее веб-приложение, будущие настольные сборки и проверку установщиков.",
  finalTitle: "Начните с веб-приложения.",
  finalLead:
    "Самый быстрый путь сейчас — веб-кабинет с авторизацией. Настольные установщики можно добавить, когда настольная среда будет готова к выпуску.",
  finalPrimary: "Открыть веб-приложение",
  finalSecondary: "Смотреть тарифы",
  platforms: [
    {
      code: "web",
      title: "Веб-кабинет",
      status: "Доступно",
      description:
        "Веб-кабинет в браузере для входа, скачиваний, файлов, транскриптов, обзора оплаты и запросов по персональным данным.",
      version: "разработка",
      cta: "Открыть веб-приложение",
      href: getSaasLink("register"),
      meta: ["Без установщика", "Современные браузеры", "Связь с API"]
    },
    {
      code: "windows",
      title: "Настольная версия для Windows",
      status: "Запланировано",
      description:
        "Будущий установщик Windows для локальных рабочих процессов и встроенной среды выполнения.",
      version: "запланированный релиз",
      cta: "Позже",
      href: "#release-notes",
      disabled: true,
      meta: ["Windows 10/11", "Основа на Tauri", "Нужна контрольная сумма"]
    },
    {
      code: "macos",
      title: "Настольная версия для macOS",
      status: "Запланировано",
      description:
        "Будущая сборка macOS для пользователей, которым нужен локальный настольный запуск.",
      version: "запланированный релиз",
      cta: "Позже",
      href: "#release-notes",
      disabled: true,
      meta: ["Apple Silicon / Intel", "Пока без подписи", "Нотариальное заверение позже"]
    },
    {
      code: "linux",
      title: "Настольная версия для Linux",
      status: "Запланировано",
      description:
        "Будущий пакет Linux для локальных рабочих процессов, тестирования и разработки.",
      version: "запланированный релиз",
      cta: "Позже",
      href: "#release-notes",
      disabled: true,
      meta: ["Цель AppImage/deb/rpm", "Упаковка среды запланирована", "Нужна контрольная сумма"]
    },
    {
      code: "cli",
      title: "Инструменты командной строки и фоновых задач",
      status: "В плане развития",
      description:
        "Инструменты для разработчиков: локальная обработка под контролем и диагностика фоновых задач.",
      version: "запланированный релиз",
      cta: "Документация",
      href: "/ru/docs",
      meta: ["Рабочий процесс разработчика", "Пока не публично", "Сначала документация"]
    }
  ],
  requirements: [
    { label: "Веб-приложение", value: "Современный Chromium, Firefox, Safari или Edge." },
    { label: "Доступ к API", value: "Backend API и очередь фоновых задач должны быть запущены для медиа-задач." },
    { label: "Настольная среда", value: "Настольная оболочка на Tauri есть как основа, но это ещё не релиз." },
    { label: "Хранилище", value: "Зависит от скачанных медиафайлов, транскриптов и локального кэша среды выполнения." },
    { label: "Сеть", value: "Нужна для анализа URL, скачивания, авторизации и сценариев оплаты." }
  ],
  releaseNotes: [
    {
      version: "0.1.0-web",
      date: "2026-05-31",
      status: "Разработка",
      items: [
        "Веб-кабинет — основной способ доступа.",
        "Добавлена структура публичной страницы скачивания.",
        "Добавлен план распространения настольных версий.",
        "Контрольные суммы и подписи зарезервированы для реальных установщиков."
      ]
    }
  ],
  faq: [
    {
      question: "Настольное приложение уже можно скачать?",
      answer:
        "Пока нет. В проекте есть основа для настольной версии, но публичные установщики на этом этапе не опубликованы."
    },
    {
      question: "Что использовать сейчас?",
      answer:
        "Используйте веб-кабинет. Это текущий поддерживаемый путь для рабочих процессов с авторизацией."
    },
    {
      question: "У установщиков будут контрольные суммы?",
      answer:
        "Да. Когда настольные сборки будут опубликованы, страница скачивания должна содержать SHA256 и данные подписи."
    },
    {
      question: "Для страницы скачивания нужна серверная часть?",
      answer:
        "Нет. На этом этапе это маркетинговая и дистрибутивная страница. Хранилище релизов или API версий можно добавить позже."
    }
  ]
};

export function getDownloadContent(locale: Locale = "en"): DownloadContent {
  return locale === "ru" ? downloadContentRu : downloadContentEn;
}
