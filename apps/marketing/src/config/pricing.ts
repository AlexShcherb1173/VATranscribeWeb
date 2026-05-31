import type { Locale } from "../i18n/locales";

export type PricingPlan = {
  code: string;
  name: string;
  price: string;
  period: string;
  description: string;
  quota: string;
  features: string[];
  cta: string;
  href: string;
  highlighted: boolean;
};

export const pricingPlans: PricingPlan[] = [
  {
    code: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    description: "For validating the workflow and testing media processing.",
    quota: "Basic quotas",
    features: [
      "MP3/MP4 workflow preview",
      "Limited transcription",
      "Basic job history",
      "Legal consent flow",
      "Community-level support"
    ],
    cta: "Start free",
    href: "http://localhost:5175/auth/register?plan=pro",
    highlighted: false
  },
  {
    code: "pro",
    name: "Pro",
    price: "$12",
    period: "per month",
    description: "For creators and solo operators with regular media processing.",
    quota: "Higher monthly limits",
    features: [
      "Higher download quota",
      "Higher transcription quota",
      "Media asset library",
      "Transcript history",
      "Priority processing foundation"
    ],
    cta: "Choose Pro",
    href: "http://localhost:5175/auth/register?plan=free",
    highlighted: true
  },
  {
    code: "business",
    name: "Business",
    price: "$49",
    period: "per month",
    description: "For teams that need compliance-oriented media workflows.",
    quota: "Team-ready limits",
    features: [
      "Audit log foundation",
      "Privacy request workflow",
      "Billing overview",
      "Admin-ready architecture",
      "Team workflow roadmap"
    ],
    cta: "Contact sales",
    href: "http://localhost:5175/auth/register?plan=business",
    highlighted: false
  }
];

export const pricingPlansRu: PricingPlan[] = [
  {
    code: "free",
    name: "Free",
    price: "$0",
    period: "навсегда",
    description: "Для проверки workflow и тестирования обработки медиа.",
    quota: "Базовые лимиты",
    features: [
      "Предпросмотр MP3/MP4 workflow",
      "Ограниченная транскрибация",
      "Базовая история задач",
      "Согласия с юридическими документами",
      "Поддержка уровня community"
    ],
    cta: "Начать бесплатно",
    href: "http://localhost:5175/auth/register?plan=pro",
    highlighted: false
  },
  {
    code: "pro",
    name: "Pro",
    price: "$12",
    period: "в месяц",
    description: "Для авторов и одиночных операторов с регулярной обработкой медиа.",
    quota: "Повышенные месячные лимиты",
    features: [
      "Повышенный лимит скачиваний",
      "Повышенный лимит транскрибации",
      "Библиотека медиафайлов",
      "История транскриптов",
      "Основа для приоритетной обработки"
    ],
    cta: "Выбрать Pro",
    href: "http://localhost:5175/auth/register",
    highlighted: true
  },
  {
    code: "business",
    name: "Business",
    price: "$49",
    period: "в месяц",
    description: "Для команд, которым нужны контролируемые media workflows.",
    quota: "Командные лимиты",
    features: [
      "Основа audit logs",
      "Privacy request workflow",
      "Billing overview",
      "Архитектура под админку",
      "Roadmap командной работы"
    ],
    cta: "Связаться",
    href: "http://localhost:5175/auth/register?plan=business",
    highlighted: false
  }
];

export function getPricingPlans(locale: Locale = "en"): PricingPlan[] {
  return locale === "ru" ? pricingPlansRu : pricingPlans;
}