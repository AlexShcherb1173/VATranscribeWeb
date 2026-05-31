export const siteConfig = {
  name: "VATranscribe",
  productName: "VATranscribe",
  tagline: "Download, transcribe and manage media files in one workspace.",
  description:
    "VATranscribe is a SaaS-ready media workflow platform for downloading, converting, transcribing and organizing video and audio files.",
  baseUrl: "https://vatranscribe.example.com",
  appUrl: "http://localhost:5175",
  apiUrl: "http://localhost:8000",
  locale: "en",
  nav: [
    { label: "Features", href: "/features" },
    { label: "Pricing", href: "/pricing" },
    { label: "Download", href: "/download" },
    { label: "Docs", href: "/docs" },
    { label: "Blog", href: "/blog" }
  ],
  legal: [
    { label: "Terms", href: "/legal/terms" },
    { label: "Privacy", href: "/legal/privacy" },
    { label: "Personal Data", href: "/legal/personal-data" },
    { label: "Cookies", href: "/legal/cookies" },
    { label: "Refund Policy", href: "/legal/refund" }
  ]
} as const;
