export const pricingPlans = [
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
    href: "http://localhost:5175/auth/register",
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
    href: "http://localhost:5175/auth/register",
    highlighted: true
  },
  {
    code: "business",
    name: "Business",
    price: "$39",
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
    href: "/pricing#contact",
    highlighted: false
  }
] as const;