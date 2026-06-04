import { getMarketingBaseUrl, getSaasBaseUrl } from "./links";

export const siteConfig = {
  name: "VATranscribe",
  productName: "VATranscribe",
  tagline: "Download, transcribe and manage media files in one workspace.",
  description:
    "VATranscribe is a SaaS-ready media workflow platform for downloading, converting, transcribing and organizing video and audio files.",
  baseUrl: getMarketingBaseUrl(),
  appUrl: getSaasBaseUrl(),
  apiUrl: "http://localhost:8000",
  locale: "en",
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
  ]
} as const;

export const productStats = [
  { value: "MP3/MP4", label: "download workflows" },
  { value: "JWT + rotation", label: "auth foundation" },
  { value: "Audit-ready", label: "security events" },
  { value: "SaaS-ready", label: "billing and quotas" }
] as const;

export const primaryUseCases = [
  {
    title: "Creators and editors",
    description:
      "Collect source media, prepare audio/video files and turn speech into reusable text assets.",
    href: "/use-cases#creators"
  },
  {
    title: "Developers and testers",
    description:
      "Validate downloader and transcription flows with logs, queues, API endpoints and ownership checks.",
    href: "/use-cases#developers"
  },
  {
    title: "Teams and operators",
    description:
      "Prepare a controlled SaaS workflow with accounts, quotas, audit logs and privacy requests.",
    href: "/use-cases#teams"
  }
] as const;