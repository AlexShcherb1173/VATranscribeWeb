import type { Locale } from "../i18n/locales";
import { getSaasLink } from "./links";

export type PlanCode = "free" | "pro" | "business";

export type PricingPlan = {
  code: PlanCode;
  name: string;
  badge: string;
  price: string;
  period: string;
  yearlyNote: string;
  description: string;
  bestFor: string;
  quota: string;
  storage: string;
  transcription: string;
  jobs: string;
  features: string[];
  cta: string;
  href: string;
  highlighted: boolean;
};

export type PricingComparisonRow = {
  label: string;
  free: string;
  pro: string;
  business: string;
};

export type PricingFaqItem = {
  question: string;
  answer: string;
};

export type PricingContent = {
  eyebrow: string;
  title: string;
  lead: string;
  sourceNote: string;
  periodToggle: {
    monthly: string;
    yearly: string;
    yearlyNote: string;
  };
  cardsTitle: string;
  quotaTitle: string;
  quotaLead: string;
  comparisonTitle: string;
  comparisonLead: string;
  faqTitle: string;
  faqLead: string;
  finalTitle: string;
  finalLead: string;
  finalPrimary: string;
  finalSecondary: string;
  plans: PricingPlan[];
  comparison: PricingComparisonRow[];
  faq: PricingFaqItem[];
};

export const pricingContentEn: PricingContent = {
  eyebrow: "Pricing",
  title: "Plans for creators, developers and teams.",
  lead:
    "Start with a free workflow, move to Pro for regular processing, and use Business when auditability, quotas and team operations matter.",
  sourceNote:
    "Plan codes and monthly prices are aligned with the backend /api/v1/plans catalog.",
  periodToggle: {
    monthly: "Monthly",
    yearly: "Yearly",
    yearlyNote:
      "Yearly billing is prepared as a UI foundation. Backend annual prices can be added in a later billing stage."
  },
  cardsTitle: "Choose the right workflow tier.",
  quotaTitle: "Quota matrix",
  quotaLead:
    "These limits come from the backend plan catalog and should remain aligned with /api/v1/plans.",
  comparisonTitle: "Feature comparison",
  comparisonLead:
    "The table below explains the commercial packaging of the same technical product foundation.",
  faqTitle: "Billing FAQ",
  faqLead:
    "Short answers for plan selection, quotas, billing readiness and future annual pricing.",
  finalTitle: "Ready to test the workflow?",
  finalLead:
    "Choose a plan code now. Payment provider integration can be added after the pricing surface is validated.",
  finalPrimary: "Start with Pro",
  finalSecondary: "Open dashboard",
  plans: [
    {
      code: "free",
      name: "Free",
      badge: "Validate",
      price: "$0",
      period: "forever",
      yearlyNote: "No billing required",
      description: "For validating the workflow and testing media processing.",
      bestFor: "Local testing, product validation and light usage.",
      quota: "Basic quotas",
      storage: "10 GB",
      transcription: "36,000 sec",
      jobs: "500 jobs",
      features: [
        "MP3/MP4 workflow preview",
        "Limited transcription",
        "Basic job history",
        "Legal consent flow",
        "Community-level support"
      ],
      cta: "Start free",
      href: getSaasLink("register", { plan: "free" }),
      highlighted: false
    },
    {
      code: "pro",
      name: "Pro",
      badge: "Recommended",
      price: "$12",
      period: "per month",
      yearlyNote: "Yearly billing foundation ready",
      description: "For creators and solo operators with regular media processing.",
      bestFor: "Regular download, transcription and media asset workflows.",
      quota: "Higher monthly limits",
      storage: "100 GB",
      transcription: "144,000 sec",
      jobs: "5,000 jobs",
      features: [
        "Higher download quota",
        "Higher transcription quota",
        "Media asset library",
        "Transcript history",
        "Priority processing foundation"
      ],
      cta: "Choose Pro",
      href: getSaasLink("register", { plan: "pro" }),
      highlighted: true
    },
    {
      code: "business",
      name: "Business",
      badge: "Scale",
      price: "$49",
      period: "per month",
      yearlyNote: "Annual contracts can be added later",
      description: "For teams that need compliance-oriented media workflows.",
      bestFor: "Audit-heavy workflows, larger quotas and team operations.",
      quota: "Team-ready limits",
      storage: "500 GB",
      transcription: "720,000 sec",
      jobs: "20,000 jobs",
      features: [
        "Audit log foundation",
        "Privacy request workflow",
        "Billing overview",
        "Admin-ready architecture",
        "Team workflow roadmap"
      ],
      cta: "Choose Business",
      href: getSaasLink("register", { plan: "business" }),
      highlighted: false
    }
  ],
  comparison: [
    { label: "Media downloads", free: "Basic", pro: "Higher quota", business: "Team scale" },
    { label: "Transcription", free: "Limited", pro: "Regular usage", business: "High volume" },
    { label: "Media asset library", free: "Basic", pro: "Included", business: "Included" },
    { label: "Audit logs", free: "Security baseline", pro: "Security baseline", business: "Audit-ready" },
    { label: "Privacy requests", free: "Included", pro: "Included", business: "Included" },
    { label: "Billing overview", free: "Basic", pro: "Included", business: "Included" },
    { label: "Admin/team layer", free: "No", pro: "Roadmap", business: "Roadmap priority" }
  ],
  faq: [
    {
      question: "Are these prices connected to backend plans?",
      answer:
        "Yes. The public pricing surface is aligned with the backend plan catalog: free, pro and business."
    },
    {
      question: "Is yearly billing active?",
      answer:
        "Not yet. Stage 3.5.1 adds the UI foundation for monthly/yearly switching, but backend annual pricing should be added in a later billing stage."
    },
    {
      question: "Do quotas come from the backend?",
      answer:
        "The quota values shown here match the current backend plans table and /api/v1/plans response."
    },
    {
      question: "Does choosing a plan charge the user?",
      answer:
        "No. Current CTAs pass plan codes into registration or billing flows. Payment provider integration is a later stage."
    }
  ]
};

export const pricingContentRu: PricingContent = {
  eyebrow: "Тарифы",
  title: "Планы для авторов, разработчиков и команд.",
  lead:
    "Начните с бесплатного workflow, перейдите на Pro для регулярной обработки и используйте Business, когда важны auditability, квоты и командные процессы.",
  sourceNote:
    "Коды тарифов и месячные цены синхронизированы с backend-каталогом /api/v1/plans.",
  periodToggle: {
    monthly: "Месяц",
    yearly: "Год",
    yearlyNote:
      "Годовая оплата заложена как UI foundation. Backend annual prices можно добавить на следующем billing-этапе."
  },
  cardsTitle: "Выберите подходящий уровень workflow.",
  quotaTitle: "Матрица лимитов",
  quotaLead:
    "Эти лимиты соответствуют backend plan catalog и должны оставаться синхронизированными с /api/v1/plans.",
  comparisonTitle: "Сравнение возможностей",
  comparisonLead:
    "Таблица объясняет коммерческую упаковку одной и той же технической продуктовой основы.",
  faqTitle: "FAQ по оплате",
  faqLead:
    "Короткие ответы по выбору тарифа, лимитам, billing readiness и будущей годовой оплате.",
  finalTitle: "Готовы проверить workflow?",
  finalLead:
    "Выберите plan code сейчас. Интеграцию платёжного провайдера можно добавить после проверки pricing surface.",
  finalPrimary: "Начать с Pro",
  finalSecondary: "Открыть dashboard",
  plans: [
    {
      code: "free",
      name: "Free",
      badge: "Проверка",
      price: "$0",
      period: "навсегда",
      yearlyNote: "Оплата не требуется",
      description: "Для проверки workflow и тестирования обработки медиа.",
      bestFor: "Локальное тестирование, проверка продукта и лёгкое использование.",
      quota: "Базовые лимиты",
      storage: "10 GB",
      transcription: "36,000 сек",
      jobs: "500 задач",
      features: [
        "Предпросмотр MP3/MP4 workflow",
        "Ограниченная транскрибация",
        "Базовая история задач",
        "Согласия с юридическими документами",
        "Поддержка уровня community"
      ],
      cta: "Начать бесплатно",
      href: getSaasLink("register", { plan: "free" }),
      highlighted: false
    },
    {
      code: "pro",
      name: "Pro",
      badge: "Рекомендуем",
      price: "$12",
      period: "в месяц",
      yearlyNote: "Основа для годовой оплаты готова",
      description: "Для авторов и одиночных операторов с регулярной обработкой медиа.",
      bestFor: "Регулярное скачивание, транскрибация и работа с media assets.",
      quota: "Повышенные месячные лимиты",
      storage: "100 GB",
      transcription: "144,000 сек",
      jobs: "5,000 задач",
      features: [
        "Повышенный лимит скачиваний",
        "Повышенный лимит транскрибации",
        "Библиотека медиафайлов",
        "История транскриптов",
        "Основа для приоритетной обработки"
      ],
      cta: "Выбрать Pro",
      href: getSaasLink("register", { plan: "pro" }),
      highlighted: true
    },
    {
      code: "business",
      name: "Business",
      badge: "Масштаб",
      price: "$49",
      period: "в месяц",
      yearlyNote: "Годовые контракты можно добавить позже",
      description: "Для команд, которым нужны контролируемые media workflows.",
      bestFor: "Audit-heavy workflows, большие лимиты и командные операции.",
      quota: "Командные лимиты",
      storage: "500 GB",
      transcription: "720,000 сек",
      jobs: "20,000 задач",
      features: [
        "Основа audit logs",
        "Privacy request workflow",
        "Billing overview",
        "Архитектура под админку",
        "Roadmap командной работы"
      ],
      cta: "Выбрать Business",
      href: getSaasLink("register", { plan: "business" }),
      highlighted: false
    }
  ],
  comparison: [
    { label: "Скачивание медиа", free: "Базово", pro: "Повышенная квота", business: "Командный масштаб" },
    { label: "Транскрибация", free: "Ограниченно", pro: "Регулярное использование", business: "Большой объём" },
    { label: "Media asset library", free: "Базово", pro: "Включено", business: "Включено" },
    { label: "Audit logs", free: "Security baseline", pro: "Security baseline", business: "Audit-ready" },
    { label: "Privacy requests", free: "Включено", pro: "Включено", business: "Включено" },
    { label: "Billing overview", free: "Базово", pro: "Включено", business: "Включено" },
    { label: "Admin/team layer", free: "Нет", pro: "Roadmap", business: "Roadmap priority" }
  ],
  faq: [
    {
      question: "Эти цены связаны с backend plans?",
      answer:
        "Да. Публичная pricing surface синхронизирована с backend-каталогом: free, pro и business."
    },
    {
      question: "Годовая оплата уже активна?",
      answer:
        "Пока нет. Stage 3.5.1 добавляет UI foundation для monthly/yearly, но backend annual pricing лучше добавить отдельным billing-этапом."
    },
    {
      question: "Лимиты берутся из backend?",
      answer:
        "Значения лимитов совпадают с текущей таблицей plans и ответом /api/v1/plans."
    },
    {
      question: "Выбор тарифа сразу списывает деньги?",
      answer:
        "Нет. Сейчас CTA передаёт plan code в регистрацию или billing flow. Платёжный провайдер подключается позже."
    }
  ]
};

export function getPricingContent(locale: Locale = "en"): PricingContent {
  return locale === "ru" ? pricingContentRu : pricingContentEn;
}

export function getPricingPlans(locale: Locale = "en"): PricingPlan[] {
  return getPricingContent(locale).plans;
}