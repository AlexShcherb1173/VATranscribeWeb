export const pricingPlans = [
  {
    code: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    description: "For testing the workflow and validating media processing.",
    features: ["Basic downloads", "Limited transcription", "Local testing", "Community support"],
    cta: "Start free",
    href: "/download"
  },
  {
    code: "pro",
    name: "Pro",
    price: "$12",
    period: "per month",
    description: "For creators and small teams that need regular transcription and exports.",
    features: ["Higher quotas", "MP3/MP4 workflows", "Transcription history", "Priority processing"],
    cta: "Choose Pro",
    href: "/pricing"
  },
  {
    code: "business",
    name: "Business",
    price: "$39",
    period: "per month",
    description: "For teams that need auditability, billing control and shared workflows.",
    features: ["Team-ready quotas", "Audit logs", "Billing overview", "Admin-ready foundation"],
    cta: "Contact sales",
    href: "/pricing"
  }
] as const;
