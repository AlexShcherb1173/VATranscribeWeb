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
  eyebrow: "РўР°СЂРёС„С‹",
  title: "РўР°СЂРёС„С‹ РґР»СЏ Р°РІС‚РѕСЂРѕРІ, СЂР°Р·СЂР°Р±РѕС‚С‡РёРєРѕРІ Рё РєРѕРјР°РЅРґ.",
  lead:
    "РќР°С‡РЅРёС‚Рµ Р±РµСЃРїР»Р°С‚РЅРѕ, РїРµСЂРµР№РґРёС‚Рµ РЅР° РїСЂРѕС„РµСЃСЃРёРѕРЅР°Р»СЊРЅС‹Р№ С‚Р°СЂРёС„ РґР»СЏ СЂРµРіСѓР»СЏСЂРЅРѕР№ РѕР±СЂР°Р±РѕС‚РєРё Рё РёСЃРїРѕР»СЊР·СѓР№С‚Рµ РєРѕРјР°РЅРґРЅС‹Р№ С‚Р°СЂРёС„, РєРѕРіРґР° РІР°Р¶РЅС‹ Р±РѕР»СЊС€РёРµ Р»РёРјРёС‚С‹, Р¶СѓСЂРЅР°Р» РґРµР№СЃС‚РІРёР№ Рё СЃРѕРІРјРµСЃС‚РЅР°СЏ СЂР°Р±РѕС‚Р°.",
  sourceNote:
    "РљРѕРґС‹ С‚Р°СЂРёС„РѕРІ Рё РјРµСЃСЏС‡РЅС‹Рµ С†РµРЅС‹ СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅС‹ СЃ РєР°С‚Р°Р»РѕРіРѕРј С‚Р°СЂРёС„РѕРІ API /api/v1/plans.",
  periodToggle: {
    monthly: "РњРµСЃСЏС†",
    yearly: "Р“РѕРґ",
    yearlyNote:
      "Р“РѕРґРѕРІР°СЏ РѕРїР»Р°С‚Р° РїРѕРґРіРѕС‚РѕРІР»РµРЅР° РЅР° СѓСЂРѕРІРЅРµ РёРЅС‚РµСЂС„РµР№СЃР°. Р¦РµРЅС‹ РґР»СЏ РіРѕРґРѕРІРѕР№ РѕРїР»Р°С‚С‹ РјРѕР¶РЅРѕ РґРѕР±Р°РІРёС‚СЊ РЅР° СЃР»РµРґСѓСЋС‰РµРј СЌС‚Р°РїРµ Р±РёР»Р»РёРЅРіР°."
  },
  cardsTitle: "Р’С‹Р±РµСЂРёС‚Рµ РїРѕРґС…РѕРґСЏС‰РёР№ С‚Р°СЂРёС„.",
  quotaTitle: "Р›РёРјРёС‚С‹ С‚Р°СЂРёС„РѕРІ",
  quotaLead:
    "Р­С‚Рё Р»РёРјРёС‚С‹ СЃРѕРѕС‚РІРµС‚СЃС‚РІСѓСЋС‚ С‚РµРєСѓС‰РµРјСѓ РєР°С‚Р°Р»РѕРіСѓ С‚Р°СЂРёС„РѕРІ API Рё РґРѕР»Р¶РЅС‹ РѕСЃС‚Р°РІР°С‚СЊСЃСЏ СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРЅС‹РјРё СЃ /api/v1/plans.",
  comparisonTitle: "РЎСЂР°РІРЅРµРЅРёРµ РІРѕР·РјРѕР¶РЅРѕСЃС‚РµР№",
  comparisonLead:
    "РўР°Р±Р»РёС†Р° РїРѕРєР°Р·С‹РІР°РµС‚, С‡РµРј РѕС‚Р»РёС‡Р°СЋС‚СЃСЏ С‚Р°СЂРёС„С‹ РѕРґРЅРѕР№ РїСЂРѕРґСѓРєС‚РѕРІРѕР№ РїР»Р°С‚С„РѕСЂРјС‹.",
  faqTitle: "Р’РѕРїСЂРѕСЃС‹ РїРѕ РѕРїР»Р°С‚Рµ",
  faqLead:
    "РљРѕСЂРѕС‚РєРёРµ РѕС‚РІРµС‚С‹ РїРѕ РІС‹Р±РѕСЂСѓ С‚Р°СЂРёС„Р°, Р»РёРјРёС‚Р°Рј, РїРѕРґРєР»СЋС‡РµРЅРёСЋ РѕРїР»Р°С‚С‹ Рё Р±СѓРґСѓС‰РµР№ РіРѕРґРѕРІРѕР№ РїРѕРґРїРёСЃРєРµ.",
  finalTitle: "Р“РѕС‚РѕРІС‹ РїСЂРѕРІРµСЂРёС‚СЊ РїСЂРѕРґСѓРєС‚?",
  finalLead:
    "Р’С‹Р±РµСЂРёС‚Рµ С‚Р°СЂРёС„. РџРѕРґРєР»СЋС‡РµРЅРёРµ РїР»Р°С‚С‘Р¶РЅРѕРіРѕ РїСЂРѕРІР°Р№РґРµСЂР° РјРѕР¶РЅРѕ РґРѕР±Р°РІРёС‚СЊ РїРѕСЃР»Рµ РїСЂРѕРІРµСЂРєРё С‚Р°СЂРёС„РЅРѕР№ СЃС‚СЂР°РЅРёС†С‹.",
  finalPrimary: "РќР°С‡Р°С‚СЊ СЃ РїСЂРѕС„РµСЃСЃРёРѕРЅР°Р»СЊРЅРѕРіРѕ С‚Р°СЂРёС„Р°",
  finalSecondary: "РћС‚РєСЂС‹С‚СЊ РїСЂРёР»РѕР¶РµРЅРёРµ",
  plans: [
    {
      code: "free",
      name: "Р‘РµСЃРїР»Р°С‚РЅС‹Р№",
      badge: "РџСЂРѕРІРµСЂРєР°",
      price: "$0",
      period: "РЅР°РІСЃРµРіРґР°",
      yearlyNote: "РћРїР»Р°С‚Р° РЅРµ С‚СЂРµР±СѓРµС‚СЃСЏ",
      description: "Р”Р»СЏ РїСЂРѕРІРµСЂРєРё РїСЂРѕРґСѓРєС‚Р° Рё С‚РµСЃС‚РёСЂРѕРІР°РЅРёСЏ РѕР±СЂР°Р±РѕС‚РєРё РјРµРґРёР°.",
      bestFor: "Р›РѕРєР°Р»СЊРЅРѕРµ С‚РµСЃС‚РёСЂРѕРІР°РЅРёРµ, РїСЂРѕРІРµСЂРєР° РїСЂРѕРґСѓРєС‚Р° Рё Р»С‘РіРєРѕРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ.",
      quota: "Р‘Р°Р·РѕРІС‹Рµ Р»РёРјРёС‚С‹",
      storage: "10 Р“Р‘",
      transcription: "36 000 СЃРµРє",
      jobs: "500 Р·Р°РґР°С‡",
      features: [
        "РџСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ СЂР°Р±РѕС‚С‹ СЃ MP3/MP4",
        "РћРіСЂР°РЅРёС‡РµРЅРЅР°СЏ С‚СЂР°РЅСЃРєСЂРёР±Р°С†РёСЏ",
        "Р‘Р°Р·РѕРІР°СЏ РёСЃС‚РѕСЂРёСЏ Р·Р°РґР°С‡",
        "РЎРѕРіР»Р°СЃРёСЏ СЃ СЋСЂРёРґРёС‡РµСЃРєРёРјРё РґРѕРєСѓРјРµРЅС‚Р°РјРё",
        "Р‘Р°Р·РѕРІР°СЏ РїРѕРґРґРµСЂР¶РєР°"
      ],
      cta: "РќР°С‡Р°С‚СЊ Р±РµСЃРїР»Р°С‚РЅРѕ",
      href: getSaasLink("register", { plan: "free" }),
      highlighted: false
    },
    {
      code: "pro",
      name: "РџСЂРѕС„РµСЃСЃРёРѕРЅР°Р»СЊРЅС‹Р№",
      badge: "Р РµРєРѕРјРµРЅРґСѓРµРј",
      price: "$12",
      period: "РІ РјРµСЃСЏС†",
      yearlyNote: "РћСЃРЅРѕРІР° РґР»СЏ РіРѕРґРѕРІРѕР№ РѕРїР»Р°С‚С‹ РіРѕС‚РѕРІР°",
      description: "Р”Р»СЏ Р°РІС‚РѕСЂРѕРІ Рё СЃР°РјРѕСЃС‚РѕСЏС‚РµР»СЊРЅС‹С… СЃРїРµС†РёР°Р»РёСЃС‚РѕРІ СЃ СЂРµРіСѓР»СЏСЂРЅРѕР№ РѕР±СЂР°Р±РѕС‚РєРѕР№ РјРµРґРёР°.",
      bestFor: "Р РµРіСѓР»СЏСЂРЅРѕРµ СЃРєР°С‡РёРІР°РЅРёРµ, С‚СЂР°РЅСЃРєСЂРёР±Р°С†РёСЏ Рё СЂР°Р±РѕС‚Р° СЃ РјРµРґРёР°С‚РµРєРѕР№.",
      quota: "РџРѕРІС‹С€РµРЅРЅС‹Рµ РјРµСЃСЏС‡РЅС‹Рµ Р»РёРјРёС‚С‹",
      storage: "100 Р“Р‘",
      transcription: "144 000 СЃРµРє",
      jobs: "5 000 Р·Р°РґР°С‡",
      features: [
        "РџРѕРІС‹С€РµРЅРЅС‹Р№ Р»РёРјРёС‚ СЃРєР°С‡РёРІР°РЅРёР№",
        "РџРѕРІС‹С€РµРЅРЅС‹Р№ Р»РёРјРёС‚ С‚СЂР°РЅСЃРєСЂРёР±Р°С†РёРё",
        "Р‘РёР±Р»РёРѕС‚РµРєР° РјРµРґРёР°С„Р°Р№Р»РѕРІ",
        "РСЃС‚РѕСЂРёСЏ С‚СЂР°РЅСЃРєСЂРёРїС‚РѕРІ",
        "РћСЃРЅРѕРІР° РґР»СЏ РїСЂРёРѕСЂРёС‚РµС‚РЅРѕР№ РѕР±СЂР°Р±РѕС‚РєРё"
      ],
      cta: "Р’С‹Р±СЂР°С‚СЊ РїСЂРѕС„РµСЃСЃРёРѕРЅР°Р»СЊРЅС‹Р№ С‚Р°СЂРёС„",
      href: getSaasLink("register", { plan: "pro" }),
      highlighted: true
    },
    {
      code: "business",
      name: "РљРѕРјР°РЅРґРЅС‹Р№",
      badge: "РњР°СЃС€С‚Р°Р±",
      price: "$49",
      period: "РІ РјРµСЃСЏС†",
      yearlyNote: "Р“РѕРґРѕРІС‹Рµ РґРѕРіРѕРІРѕСЂС‹ РјРѕР¶РЅРѕ РґРѕР±Р°РІРёС‚СЊ РїРѕР·Р¶Рµ",
      description: "Р”Р»СЏ РєРѕРјР°РЅРґ, РєРѕС‚РѕСЂС‹Рј РЅСѓР¶РЅС‹ РєРѕРЅС‚СЂРѕР»РёСЂСѓРµРјС‹Рµ РїСЂРѕС†РµСЃСЃС‹ РѕР±СЂР°Р±РѕС‚РєРё РјРµРґРёР°.",
      bestFor: "Р‘РѕР»СЊС€РёРµ Р»РёРјРёС‚С‹, Р¶СѓСЂРЅР°Р» РґРµР№СЃС‚РІРёР№ Рё РєРѕРјР°РЅРґРЅС‹Рµ РѕРїРµСЂР°С†РёРё.",
      quota: "РљРѕРјР°РЅРґРЅС‹Рµ Р»РёРјРёС‚С‹",
      storage: "500 Р“Р‘",
      transcription: "720 000 СЃРµРє",
      jobs: "20 000 Р·Р°РґР°С‡",
      features: [
        "РћСЃРЅРѕРІР° РґР»СЏ Р¶СѓСЂРЅР°Р»Р° РґРµР№СЃС‚РІРёР№",
        "Р—Р°РїСЂРѕСЃС‹ РїРѕ РїРµСЂСЃРѕРЅР°Р»СЊРЅС‹Рј РґР°РЅРЅС‹Рј",
        "РћР±Р·РѕСЂ РѕРїР»Р°С‚С‹ Рё С‚Р°СЂРёС„РѕРІ",
        "РђСЂС…РёС‚РµРєС‚СѓСЂР° РїРѕРґ Р°РґРјРёРЅ-РїР°РЅРµР»СЊ",
        "РџСЂРёРѕСЂРёС‚РµС‚ РІ СЂР°Р·РІРёС‚РёРё РєРѕРјР°РЅРґРЅРѕР№ СЂР°Р±РѕС‚С‹"
      ],
      cta: "Р’С‹Р±СЂР°С‚СЊ РєРѕРјР°РЅРґРЅС‹Р№ С‚Р°СЂРёС„",
      href: getSaasLink("register", { plan: "business" }),
      highlighted: false
    }
  ],
  comparison: [
    { label: "РЎРєР°С‡РёРІР°РЅРёРµ РјРµРґРёР°", free: "Р‘Р°Р·РѕРІРѕ", pro: "РџРѕРІС‹С€РµРЅРЅР°СЏ РєРІРѕС‚Р°", business: "РљРѕРјР°РЅРґРЅС‹Р№ РјР°СЃС€С‚Р°Р±" },
    { label: "РўСЂР°РЅСЃРєСЂРёР±Р°С†РёСЏ", free: "РћРіСЂР°РЅРёС‡РµРЅРЅРѕ", pro: "Р РµРіСѓР»СЏСЂРЅРѕРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ", business: "Р‘РѕР»СЊС€РѕР№ РѕР±СЉС‘Рј" },
    { label: "Р‘РёР±Р»РёРѕС‚РµРєР° РјРµРґРёР°С„Р°Р№Р»РѕРІ", free: "Р‘Р°Р·РѕРІРѕ", pro: "Р’РєР»СЋС‡РµРЅРѕ", business: "Р’РєР»СЋС‡РµРЅРѕ" },
    { label: "Р–СѓСЂРЅР°Р» РґРµР№СЃС‚РІРёР№", free: "Р‘Р°Р·РѕРІС‹Р№ СѓСЂРѕРІРµРЅСЊ", pro: "Р‘Р°Р·РѕРІС‹Р№ СѓСЂРѕРІРµРЅСЊ", business: "Р Р°СЃС€РёСЂРµРЅРЅС‹Р№ СѓСЂРѕРІРµРЅСЊ" },
    { label: "Р—Р°РїСЂРѕСЃС‹ РїРѕ РїРµСЂСЃРѕРЅР°Р»СЊРЅС‹Рј РґР°РЅРЅС‹Рј", free: "Р’РєР»СЋС‡РµРЅРѕ", pro: "Р’РєР»СЋС‡РµРЅРѕ", business: "Р’РєР»СЋС‡РµРЅРѕ" },
    { label: "РћР±Р·РѕСЂ РѕРїР»Р°С‚С‹", free: "Р‘Р°Р·РѕРІРѕ", pro: "Р’РєР»СЋС‡РµРЅРѕ", business: "Р’РєР»СЋС‡РµРЅРѕ" },
    { label: "РђРґРјРёРЅ-РїР°РЅРµР»СЊ Рё РєРѕРјР°РЅРґРЅС‹Р№ СЃР»РѕР№", free: "РќРµС‚", pro: "Р’ РїР»Р°РЅРµ СЂР°Р·РІРёС‚РёСЏ", business: "РџСЂРёРѕСЂРёС‚РµС‚ РІ СЂР°Р·РІРёС‚РёРё" }
  ],
  faq: [
    {
      question: "Р­С‚Рё С†РµРЅС‹ СЃРІСЏР·Р°РЅС‹ СЃ С‚Р°СЂРёС„Р°РјРё РІ API?",
      answer:
        "Р”Р°. РџСѓР±Р»РёС‡РЅР°СЏ С‚Р°СЂРёС„РЅР°СЏ СЃС‚СЂР°РЅРёС†Р° СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅР° СЃ РєР°С‚Р°Р»РѕРіРѕРј С‚Р°СЂРёС„РѕРІ API: Р±РµСЃРїР»Р°С‚РЅС‹Р№, РїСЂРѕС„РµСЃСЃРёРѕРЅР°Р»СЊРЅС‹Р№ Рё РєРѕРјР°РЅРґРЅС‹Р№."
    },
    {
      question: "Р“РѕРґРѕРІР°СЏ РѕРїР»Р°С‚Р° СѓР¶Рµ Р°РєС‚РёРІРЅР°?",
      answer:
        "РџРѕРєР° РЅРµС‚. РРЅС‚РµСЂС„РµР№СЃ РїРѕРґРіРѕС‚РѕРІР»РµРЅ РґР»СЏ РїРµСЂРµРєР»СЋС‡РµРЅРёСЏ РјРµР¶РґСѓ РјРµСЃСЏС‡РЅРѕР№ Рё РіРѕРґРѕРІРѕР№ РѕРїР»Р°С‚РѕР№, РЅРѕ РіРѕРґРѕРІС‹Рµ С†РµРЅС‹ Р»СѓС‡С€Рµ РґРѕР±Р°РІРёС‚СЊ РѕС‚РґРµР»СЊРЅС‹Рј СЌС‚Р°РїРѕРј Р±РёР»Р»РёРЅРіР°."
    },
    {
      question: "Р›РёРјРёС‚С‹ Р±РµСЂСѓС‚СЃСЏ РёР· API?",
      answer:
        "Р—РЅР°С‡РµРЅРёСЏ Р»РёРјРёС‚РѕРІ СЃРѕРІРїР°РґР°СЋС‚ СЃ С‚РµРєСѓС‰РµР№ С‚Р°Р±Р»РёС†РµР№ С‚Р°СЂРёС„РѕРІ Рё РѕС‚РІРµС‚РѕРј /api/v1/plans."
    },
    {
      question: "Р’С‹Р±РѕСЂ С‚Р°СЂРёС„Р° СЃСЂР°Р·Сѓ СЃРїРёСЃС‹РІР°РµС‚ РґРµРЅСЊРіРё?",
      answer:
        "РќРµС‚. РЎРµР№С‡Р°СЃ РєРЅРѕРїРєРё РїРµСЂРµРґР°СЋС‚ РєРѕРґ С‚Р°СЂРёС„Р° РІ СЂРµРіРёСЃС‚СЂР°С†РёСЋ РёР»Рё СЂР°Р·РґРµР» РѕРїР»Р°С‚С‹. РџР»Р°С‚С‘Р¶РЅС‹Р№ РїСЂРѕРІР°Р№РґРµСЂ РїРѕРґРєР»СЋС‡Р°РµС‚СЃСЏ РїРѕР·Р¶Рµ."
    }
  ]
};

export function getPricingContent(locale: Locale = "en"): PricingContent {
  return locale === "ru" ? pricingContentRu : pricingContentEn;
}

export function getPricingPlans(locale: Locale = "en"): PricingPlan[] {
  return getPricingContent(locale).plans;
}