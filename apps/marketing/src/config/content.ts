import { localizePath } from "../i18n/locales";
import type { Locale } from "../i18n/locales";

export type ContentKind = "blog" | "resource";

export type ContentSection = {
  title: string;
  paragraphs?: string[];
  bullets?: string[];
};

export type ContentItem = {
  kind: ContentKind;
  locale: Locale;
  slug: string;
  title: string;
  description: string;
  category: string;
  date: string;
  readTime: string;
  path: string;
  sections: ContentSection[];
};

export type DocItem = {
  locale: Locale;
  title: string;
  description: string;
  href: string;
  tags: string[];
};

export type ChangelogEntry = {
  locale: Locale;
  version: string;
  date: string;
  title: string;
  description: string;
  items: string[];
};

export type ContentLanding = {
  eyebrow: string;
  title: string;
  lead: string;
  empty?: string;
};

const blogEn: ContentItem[] = [
  {
    kind: "blog",
    locale: "en",
    slug: "media-download-transcription-workflow",
    title: "How VATranscribe structures media download and transcription workflows",
    description:
      "A practical overview of the product workflow: URL analysis, download jobs, media assets, transcription and export readiness.",
    category: "Product architecture",
    date: "2026-06-04",
    readTime: "5 min",
    path: "/blog/media-download-transcription-workflow",
    sections: [
      {
        title: "Why the workflow needs structure",
        paragraphs: [
          "Media products become hard to maintain when downloading, conversion, transcription, storage and exports are implemented as unrelated utilities.",
          "VATranscribe separates the public marketing layer, authenticated web dashboard, API, worker layer and future desktop shell so that each part has a clear responsibility."
        ]
      },
      {
        title: "Core flow",
        bullets: [
          "The user submits a source URL or uploaded media asset.",
          "The backend creates a job owned by the authenticated user.",
          "The worker processes download or transcription tasks.",
          "Generated files, transcripts and logs remain connected to the user account.",
          "Pricing, quotas and audit logs can be attached without rewriting the workflow."
        ]
      },
      {
        title: "Product result",
        paragraphs: [
          "This structure makes the product easier to monetize, secure and extend. It also keeps the future desktop app aligned with the same backend contract."
        ]
      }
    ]
  },
  {
    kind: "blog",
    locale: "en",
    slug: "security-privacy-foundation",
    title: "Security and privacy foundation in VATranscribe",
    description:
      "What Stage 2 added: refresh token rotation, legal consents, audit logs, file ownership checks, rate limits and privacy requests.",
    category: "Security",
    date: "2026-06-04",
    readTime: "6 min",
    path: "/blog/security-privacy-foundation",
    sections: [
      {
        title: "Security before growth",
        paragraphs: [
          "A media SaaS product stores sensitive workflow metadata and may process user-submitted files. Security and privacy controls should be added before public growth begins."
        ]
      },
      {
        title: "Implemented foundation",
        bullets: [
          "Refresh token rotation for stronger session handling.",
          "Backend password policy during registration.",
          "Required legal document acceptance during signup.",
          "Audit logs for security-relevant events.",
          "Ownership checks for user media assets.",
          "Rate limits on sensitive authentication endpoints.",
          "Privacy request model, router and audit trail."
        ]
      },
      {
        title: "Why it matters",
        paragraphs: [
          "These controls reduce direct object access risk, make user consent traceable and prepare the project for production readiness work in a later stage."
        ]
      }
    ]
  },
  {
    kind: "blog",
    locale: "en",
    slug: "bilingual-astro-saas-marketing-layer",
    title: "Building a bilingual Astro marketing layer for a SaaS product",
    description:
      "How VATranscribe uses Astro, locale-aware routes, hreflang, sitemap entries and shared content config for EN/RU marketing pages.",
    category: "Marketing engineering",
    date: "2026-06-04",
    readTime: "4 min",
    path: "/blog/bilingual-astro-saas-marketing-layer",
    sections: [
      {
        title: "Route strategy",
        paragraphs: [
          "VATranscribe keeps English routes as default and adds Russian variants under /ru. This keeps URLs short while preserving clear locale separation."
        ]
      },
      {
        title: "SEO requirements",
        bullets: [
          "Canonical URLs for each language version.",
          "hreflang links for EN, RU and x-default.",
          "Sitemap entries for localized pages.",
          "Separate title and description copy per locale."
        ]
      },
      {
        title: "Content model",
        paragraphs: [
          "Stage 3.7 uses a TypeScript config-driven content layer. This keeps early-stage content explicit, versionable and easy to review without adding MDX complexity yet."
        ]
      }
    ]
  }
];

const blogRu: ContentItem[] = [
  {
    kind: "blog",
    locale: "ru",
    slug: "media-download-transcription-workflow",
    title: "Как VATranscribe организует скачивание и транскрибацию медиа",
    description:
      "Практический обзор workflow: анализ URL, download jobs, media assets, transcription и подготовка к export layer.",
    category: "Архитектура продукта",
    date: "2026-06-04",
    readTime: "5 мин",
    path: "/ru/blog/media-download-transcription-workflow",
    sections: [
      {
        title: "Почему workflow нужно структурировать",
        paragraphs: [
          "Media-продукт быстро становится сложным, если скачивание, конвертация, транскрибация, хранение и экспорт сделаны как набор несвязанных утилит.",
          "VATranscribe разделяет marketing layer, authenticated dashboard, API, worker layer и будущий desktop shell, чтобы каждый слой имел свою ответственность."
        ]
      },
      {
        title: "Основной поток",
        bullets: [
          "Пользователь отправляет source URL или media asset.",
          "Backend создаёт задачу, принадлежащую authenticated user.",
          "Worker выполняет download или transcription task.",
          "Файлы, транскрипты и логи остаются связаны с аккаунтом.",
          "Тарифы, квоты и audit logs можно подключать без переписывания workflow."
        ]
      },
      {
        title: "Результат",
        paragraphs: [
          "Такая структура упрощает монетизацию, безопасность и расширение продукта. Будущий desktop app сможет использовать тот же backend contract."
        ]
      }
    ]
  },
  {
    kind: "blog",
    locale: "ru",
    slug: "security-privacy-foundation",
    title: "Security & Privacy foundation в VATranscribe",
    description:
      "Что добавил Stage 2: refresh token rotation, legal consents, audit logs, ownership checks, rate limits и privacy requests.",
    category: "Безопасность",
    date: "2026-06-04",
    readTime: "6 мин",
    path: "/ru/blog/security-privacy-foundation",
    sections: [
      {
        title: "Security до роста",
        paragraphs: [
          "Media SaaS хранит чувствительные workflow metadata и может обрабатывать пользовательские файлы. Поэтому security и privacy controls нужны до публичного роста."
        ]
      },
      {
        title: "Что реализовано",
        bullets: [
          "Refresh token rotation для усиления сессий.",
          "Backend password policy при регистрации.",
          "Обязательное принятие legal documents при signup.",
          "Audit logs для security-relevant events.",
          "Ownership checks для user media assets.",
          "Rate limits на sensitive auth endpoints.",
          "Privacy request model, router и audit trail."
        ]
      },
      {
        title: "Почему это важно",
        paragraphs: [
          "Эти меры снижают риск прямого доступа к чужим объектам, делают согласия трассируемыми и готовят проект к production readiness."
        ]
      }
    ]
  },
  {
    kind: "blog",
    locale: "ru",
    slug: "bilingual-astro-saas-marketing-layer",
    title: "Двуязычный Astro marketing layer для SaaS-продукта",
    description:
      "Как VATranscribe использует Astro, locale-aware routes, hreflang, sitemap и shared content config для EN/RU страниц.",
    category: "Marketing engineering",
    date: "2026-06-04",
    readTime: "4 мин",
    path: "/ru/blog/bilingual-astro-saas-marketing-layer",
    sections: [
      {
        title: "Стратегия маршрутов",
        paragraphs: [
          "VATranscribe оставляет английские маршруты по умолчанию и добавляет русские версии под /ru. Это сохраняет короткие URL и чёткое разделение языков."
        ]
      },
      {
        title: "SEO-требования",
        bullets: [
          "Canonical URL для каждой языковой версии.",
          "hreflang links для EN, RU и x-default.",
          "Sitemap entries для локализованных страниц.",
          "Отдельные title и description для каждого языка."
        ]
      },
      {
        title: "Content model",
        paragraphs: [
          "Stage 3.7 использует TypeScript config-driven content layer. Это проще контролировать на раннем этапе и не добавляет MDX-сложности."
        ]
      }
    ]
  }
];

const resourcesEn: ContentItem[] = [
  {
    kind: "resource",
    locale: "en",
    slug: "media-workflow-checklist",
    title: "Media workflow checklist",
    description:
      "Checklist for designing a controlled media download and transcription workflow.",
    category: "Checklist",
    date: "2026-06-04",
    readTime: "3 min",
    path: "/resources/media-workflow-checklist",
    sections: [
      {
        title: "Workflow checkpoints",
        bullets: [
          "Define supported source types.",
          "Separate URL analysis from job creation.",
          "Track job status and progress.",
          "Persist logs for user-facing diagnostics.",
          "Connect output files to media assets.",
          "Attach transcription and export history."
        ]
      }
    ]
  },
  {
    kind: "resource",
    locale: "en",
    slug: "security-privacy-checklist",
    title: "Security and privacy checklist",
    description:
      "Practical security and privacy checks for a SaaS media product.",
    category: "Security checklist",
    date: "2026-06-04",
    readTime: "4 min",
    path: "/resources/security-privacy-checklist",
    sections: [
      {
        title: "Baseline",
        bullets: [
          "Use token rotation for long-lived sessions.",
          "Validate object ownership before job creation.",
          "Require legal consents during registration.",
          "Record security-relevant audit logs.",
          "Add rate limits to public auth endpoints.",
          "Provide privacy request workflows."
        ]
      }
    ]
  },
  {
    kind: "resource",
    locale: "en",
    slug: "pricing-quotas-checklist",
    title: "Pricing and quotas checklist",
    description:
      "Checklist for aligning public pricing pages with backend plan catalogs.",
    category: "Billing checklist",
    date: "2026-06-04",
    readTime: "3 min",
    path: "/resources/pricing-quotas-checklist",
    sections: [
      {
        title: "Pricing alignment",
        bullets: [
          "Use stable plan codes.",
          "Expose public plan catalog endpoint.",
          "Keep marketing prices aligned with backend plans.",
          "Display quotas consistently.",
          "Pass selected plan code into registration or billing flows.",
          "Do not enable payments before refund and legal policies are ready."
        ]
      }
    ]
  }
];

const resourcesRu: ContentItem[] = [
  {
    kind: "resource",
    locale: "ru",
    slug: "media-workflow-checklist",
    title: "Чеклист media workflow",
    description:
      "Чеклист проектирования контролируемого workflow для скачивания и транскрибации медиа.",
    category: "Чеклист",
    date: "2026-06-04",
    readTime: "3 мин",
    path: "/ru/resources/media-workflow-checklist",
    sections: [
      {
        title: "Контрольные точки",
        bullets: [
          "Определить поддерживаемые source types.",
          "Разделить URL analysis и job creation.",
          "Отслеживать job status и progress.",
          "Хранить logs для диагностики.",
          "Связать output files с media assets.",
          "Добавить transcription и export history."
        ]
      }
    ]
  },
  {
    kind: "resource",
    locale: "ru",
    slug: "security-privacy-checklist",
    title: "Чеклист security и privacy",
    description:
      "Практические проверки security и privacy для SaaS media-продукта.",
    category: "Security checklist",
    date: "2026-06-04",
    readTime: "4 мин",
    path: "/ru/resources/security-privacy-checklist",
    sections: [
      {
        title: "Базовый уровень",
        bullets: [
          "Использовать token rotation для long-lived sessions.",
          "Проверять ownership перед созданием job.",
          "Требовать legal consents при регистрации.",
          "Записывать security-relevant audit logs.",
          "Добавить rate limits для public auth endpoints.",
          "Реализовать privacy request workflows."
        ]
      }
    ]
  },
  {
    kind: "resource",
    locale: "ru",
    slug: "pricing-quotas-checklist",
    title: "Чеклист pricing и quotas",
    description:
      "Чеклист синхронизации публичных тарифов с backend plan catalog.",
    category: "Billing checklist",
    date: "2026-06-04",
    readTime: "3 мин",
    path: "/ru/resources/pricing-quotas-checklist",
    sections: [
      {
        title: "Pricing alignment",
        bullets: [
          "Использовать стабильные plan codes.",
          "Открыть public plan catalog endpoint.",
          "Синхронизировать marketing prices с backend plans.",
          "Показывать quotas единообразно.",
          "Передавать selected plan code в registration или billing flow.",
          "Не включать платежи до готовности refund и legal policies."
        ]
      }
    ]
  }
];

export const docsEn: DocItem[] = [
  {
    locale: "en",
    title: "Getting started",
    description: "Start with the web dashboard, registration flow and core product navigation.",
    href: "/docs#getting-started",
    tags: ["setup", "dashboard"]
  },
  {
    locale: "en",
    title: "Download workflow",
    description: "Understand URL analysis, job creation, logs and output files.",
    href: "/docs#download-workflow",
    tags: ["downloads", "jobs"]
  },
  {
    locale: "en",
    title: "Transcription workflow",
    description: "Connect media assets with transcription jobs and transcript history.",
    href: "/docs#transcription-workflow",
    tags: ["transcription", "media"]
  },
  {
    locale: "en",
    title: "Billing and quotas",
    description: "Plan codes, public pricing, quota matrix and future payment integration.",
    href: "/docs#billing-quotas",
    tags: ["billing", "quotas"]
  },
  {
    locale: "en",
    title: "Security and privacy",
    description: "Refresh token rotation, consents, audit logs, rate limits and privacy requests.",
    href: "/docs#security-privacy",
    tags: ["security", "privacy"]
  }
];

export const docsRu: DocItem[] = [
  {
    locale: "ru",
    title: "Быстрый старт",
    description: "Начало работы с веб-кабинетом, регистрацией и навигацией по продукту.",
    href: "/ru/docs#getting-started",
    tags: ["настройка", "кабинет"]
  },
  {
    locale: "ru",
    title: "Процесс скачивания",
    description: "Анализ ссылки, создание задачи, журналы выполнения и итоговые файлы.",
    href: "/ru/docs#download-workflow",
    tags: ["скачивание", "задачи"]
  },
  {
    locale: "ru",
    title: "Процесс транскрибации",
    description: "Связь медиафайлов с задачами транскрибации и историей распознавания.",
    href: "/ru/docs#transcription-workflow",
    tags: ["транскрибация", "медиа"]
  },
  {
    locale: "ru",
    title: "Тарифы и лимиты",
    description: "Коды тарифов, публичные цены, матрица лимитов и будущая интеграция оплаты.",
    href: "/ru/docs#billing-quotas",
    tags: ["тарифы", "лимиты"]
  },
  {
    locale: "ru",
    title: "Безопасность и персональные данные",
    description: "Ротация токенов обновления, согласия, журнал аудита, лимиты запросов и обращения по персональным данным.",
    href: "/ru/docs#security-privacy",
    tags: ["безопасность", "персональные данные"]
  }
];

export const changelogEn: ChangelogEntry[] = [
  {
    locale: "en",
    version: "Stage 3.7",
    date: "2026-06-04",
    title: "Blog, resources, docs and changelog layer",
    description: "Adds the public content layer for the marketing app.",
    items: [
      "Blog list and detail routes.",
      "Resources list and detail routes.",
      "Docs hub.",
      "Public changelog page.",
      "EN/RU content and SEO entries."
    ]
  },
  {
    locale: "en",
    version: "Stage 3.6",
    date: "2026-06-04",
    title: "Download and distribution page",
    description: "Adds web app access, desktop roadmap and release-note structure.",
    items: [
      "Distribution channel cards.",
      "System requirements section.",
      "Release notes preview.",
      "Checksum and signature sections."
    ]
  },
  {
    locale: "en",
    version: "Stage 3.5",
    date: "2026-06-04",
    title: "Pricing and backend plan alignment",
    description: "Connects public pricing with backend plans.",
    items: [
      "Public /api/v1/plans endpoint.",
      "Pricing cards aligned with backend plan codes.",
      "Quota matrix and comparison table.",
      "Billing FAQ."
    ]
  }
];

export const changelogRu: ChangelogEntry[] = [
  {
    locale: "ru",
    version: "Stage 3.7",
    date: "2026-06-04",
    title: "Blog, resources, docs и changelog layer",
    description: "Добавляет публичный content layer для marketing app.",
    items: [
      "Blog list и detail routes.",
      "Resources list и detail routes.",
      "Docs hub.",
      "Публичный changelog.",
      "EN/RU контент и SEO entries."
    ]
  },
  {
    locale: "ru",
    version: "Stage 3.6",
    date: "2026-06-04",
    title: "Download и distribution page",
    description: "Добавляет web app access, desktop roadmap и release-note structure.",
    items: [
      "Distribution channel cards.",
      "System requirements section.",
      "Release notes preview.",
      "Checksum и signature sections."
    ]
  },
  {
    locale: "ru",
    version: "Stage 3.5",
    date: "2026-06-04",
    title: "Pricing и backend plan alignment",
    description: "Связывает публичные тарифы с backend plans.",
    items: [
      "Public /api/v1/plans endpoint.",
      "Pricing cards синхронизированы с backend plan codes.",
      "Quota matrix и comparison table.",
      "Billing FAQ."
    ]
  }
];

export function getBlogItems(locale: Locale): ContentItem[] {
  return locale === "ru" ? blogRu : blogEn;
}

export function getResourceItems(locale: Locale): ContentItem[] {
  return locale === "ru" ? resourcesRu : resourcesEn;
}

export function getDocsItems(locale: Locale): DocItem[] {
  return locale === "ru" ? docsRu : docsEn;
}

export function getChangelogItems(locale: Locale): ChangelogEntry[] {
  return locale === "ru" ? changelogRu : changelogEn;
}

export function getContentItem(kind: ContentKind, locale: Locale, slug: string): ContentItem | undefined {
  const items = kind === "blog" ? getBlogItems(locale) : getResourceItems(locale);
  return items.find((item) => item.slug === slug);
}

export function getContentLanding(kind: "blog" | "resources" | "docs" | "changelog", locale: Locale): ContentLanding {
  const ru = locale === "ru";

  const map: Record<string, ContentLanding> = {
    "blog-en": {
      eyebrow: "Blog",
      title: "Product updates and media workflow notes.",
      lead: "Articles about VATranscribe architecture, security, marketing engineering and media automation."
    },
    "blog-ru": {
      eyebrow: "Блог",
      title: "Обновления продукта и заметки по media workflows.",
      lead: "Статьи об архитектуре VATranscribe, security, marketing engineering и media automation."
    },
    "resources-en": {
      eyebrow: "Resources",
      title: "Checklists and practical resources.",
      lead: "Reusable materials for media workflows, security, privacy, pricing and quotas."
    },
    "resources-ru": {
      eyebrow: "Ресурсы",
      title: "Чеклисты и практические материалы.",
      lead: "Материалы по media workflows, security, privacy, pricing и quotas."
    },
    "docs-en": {
      eyebrow: "Docs",
      title: "Documentation hub.",
      lead: "Product documentation for workflows, billing, quotas, security and privacy."
    },
    "docs-ru": {
      eyebrow: "Документация",
      title: "Центр документации.",
      lead: "Документация продукта: рабочие процессы, тарифы, лимиты, безопасность и персональные данные."
    },
    "changelog-en": {
      eyebrow: "Changelog",
      title: "Public product changelog.",
      lead: "Track implemented marketing, security, pricing and distribution stages."
    },
    "changelog-ru": {
      eyebrow: "Changelog",
      title: "Публичный changelog продукта.",
      lead: "История реализованных этапов marketing, security, pricing и distribution."
    }
  };

  return map[`${kind}-${ru ? "ru" : "en"}`];
}

export function getContentSeoPages() {
  const items = [
    ...blogEn,
    ...blogRu,
    ...resourcesEn,
    ...resourcesRu
  ];

  const detailPages = items.map((item) => ({
    path: item.path,
    title: item.title,
    description: item.description,
    priority: item.kind === "blog" ? "0.55" : "0.5",
    changefreq: "monthly" as const,
    locale: item.locale
  }));

  return [
    {
      path: "/changelog",
      title: "VATranscribe Changelog",
      description: "Public VATranscribe product changelog with implemented stages and release notes.",
      priority: "0.6",
      changefreq: "weekly" as const,
      locale: "en" as const
    },
    {
      path: "/ru/changelog",
      title: "Changelog VATranscribe",
      description: "Публичный changelog VATranscribe с реализованными этапами и release notes.",
      priority: "0.6",
      changefreq: "weekly" as const,
      locale: "ru" as const
    },
    ...detailPages
  ];
}

export function localizedContentPath(kind: ContentKind, slug: string, locale: Locale): string {
  const base = kind === "blog" ? `/blog/${slug}` : `/resources/${slug}`;
  return localizePath(base, locale);
}
