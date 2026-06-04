export type LegalDocumentType =
  | "terms"
  | "privacy"
  | "personal_data"
  | "cookies"
  | "refund";

export type LegalSection = {
  title: string;
  paragraphs?: string[];
  bullets?: string[];
};

export type LegalDocumentConfig = {
  documentType: LegalDocumentType;
  slug: string;
  path: string;
  title: string;
  shortTitle: string;
  version: string;
  effectiveDate: string;
  requiredForRegistration: boolean;
  summary: string;
  notice: string;
  sections: LegalSection[];
};

export const LEGAL_VERSION = "1.0";
export const LEGAL_EFFECTIVE_DATE = "2026-05-31";

export const legalDocuments: LegalDocumentConfig[] = [
  {
    documentType: "terms",
    slug: "terms",
    path: "/legal/terms",
    title: "Terms of Service",
    shortTitle: "Terms",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: true,
    summary:
      "Terms governing access to VATranscribe, including account use, media processing, subscriptions, acceptable use and service limitations.",
    notice:
      "This document is a product-ready legal draft. Replace company details, governing law and commercial terms before production launch.",
    sections: [
      {
        title: "1. Scope",
        paragraphs: [
          "These Terms of Service govern access to and use of VATranscribe, including the public marketing website, authenticated web dashboard, API-backed media workflows, download features, transcription features and related services.",
          "By creating an account or using the service, the user agrees to these Terms and to the legal documents referenced during registration."
        ]
      },
      {
        title: "2. Account registration",
        paragraphs: [
          "Users may need to create an account to access authenticated functionality, including job history, media assets, transcripts, quota usage and billing-related features.",
          "Users are responsible for keeping account credentials secure and for all activity performed through their account."
        ],
        bullets: [
          "The backend may reject weak passwords.",
          "The service may use access tokens and refresh token rotation.",
          "Users may be logged out if security controls detect invalid or revoked tokens."
        ]
      },
      {
        title: "3. Media processing",
        paragraphs: [
          "VATranscribe can process URLs, uploads, media assets, transcripts and export artifacts depending on the enabled product features.",
          "The user is responsible for ensuring that they have the rights and permissions required to download, process, transcribe, store or export any submitted media."
        ],
        bullets: [
          "Do not process content that violates third-party rights.",
          "Do not use the service for unlawful, harmful or abusive activity.",
          "Do not attempt to bypass platform restrictions, quotas, rate limits or security controls."
        ]
      },
      {
        title: "4. Subscriptions, quotas and billing",
        paragraphs: [
          "VATranscribe may provide free and paid plans with different quotas, limits and feature access. Current pricing and plan descriptions may be displayed on the pricing page or inside the product dashboard.",
          "Quotas may apply to storage, transcription seconds, job count, download activity, export activity and other resource-consuming operations."
        ]
      },
      {
        title: "5. Service availability",
        paragraphs: [
          "The service may change over time. Features may be modified, suspended or discontinued as part of active product development.",
          "The service is provided on an as-available basis during development stages. Production availability commitments require a separate written agreement."
        ]
      },
      {
        title: "6. Termination",
        paragraphs: [
          "The service may suspend or terminate accounts that violate these Terms, abuse infrastructure, attempt unauthorized access or create legal or security risk.",
          "Users may request deletion or export of account-related data through the privacy request workflow where available."
        ]
      },
      {
        title: "7. Contact",
        paragraphs: [
          "Production launch requires official legal contact email, business name, registered address and jurisdiction. Until then, legal contact details are managed through the deployment configuration and project owner records."
        ]
      }
    ]
  },
  {
    documentType: "privacy",
    slug: "privacy",
    path: "/legal/privacy",
    title: "Privacy Policy",
    shortTitle: "Privacy",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: true,
    summary:
      "Privacy Policy describing what data VATranscribe may collect, how it is used, how long it is kept and how users can request access or deletion.",
    notice:
      "This privacy text is a structured draft. Confirm jurisdiction, controller details, processors, analytics tools and retention periods before launch.",
    sections: [
      {
        title: "1. Data controller",
        paragraphs: [
          "The data controller or service operator must be specified before production launch. Add the legal entity name, registered address and contact email here.",
          "This policy applies to the VATranscribe marketing website, web dashboard, API and related processing workflows."
        ]
      },
      {
        title: "2. Data we may process",
        bullets: [
          "Account data: email address, password hash, account status and timestamps.",
          "Security data: authentication events, refresh token records, IP-derived metadata and audit logs.",
          "Usage data: jobs, quota usage, media asset metadata, transcript metadata and export metadata.",
          "User-submitted data: media links, uploaded files, generated transcripts and comments in privacy requests.",
          "Billing data: plan, subscription status, usage history and provider references when payments are enabled."
        ]
      },
      {
        title: "3. Purposes of processing",
        bullets: [
          "Create and manage user accounts.",
          "Authenticate users and protect sessions.",
          "Process download and transcription jobs.",
          "Enforce quotas, subscriptions and service limits.",
          "Record consent versions and audit-relevant events.",
          "Respond to privacy requests and support requests.",
          "Improve service reliability and security."
        ]
      },
      {
        title: "4. Legal basis",
        paragraphs: [
          "Depending on jurisdiction, processing may be based on contract performance, user consent, legitimate interest, legal obligation or another applicable legal basis.",
          "For production use, replace this section with jurisdiction-specific legal bases reviewed by counsel."
        ]
      },
      {
        title: "5. Retention",
        paragraphs: [
          "Account, media, transcript, audit and billing records may be retained while the account is active or as required for security, compliance, billing, dispute resolution and legal obligations.",
          "Specific retention periods must be finalized before production. The product architecture supports user privacy requests for export, deletion and consent revocation workflows."
        ]
      },
      {
        title: "6. User rights",
        bullets: [
          "Request access to personal data.",
          "Request export of data where supported.",
          "Request deletion of account-related data where legally possible.",
          "Request correction of inaccurate data.",
          "Revoke consent where processing is based on consent.",
          "Submit a privacy request through the product workflow."
        ]
      },
      {
        title: "7. Processors and third parties",
        paragraphs: [
          "The service may rely on hosting, database, email, analytics, payment, fiscalization, logging or media-processing providers. List real providers before production launch.",
          "Do not publish this policy without adding actual processor names, countries and data transfer details where required."
        ]
      },
      {
        title: "8. Contact",
        paragraphs: [
          "Add the official privacy contact email and business contact details before launch."
        ]
      }
    ]
  },
  {
    documentType: "personal_data",
    slug: "personal-data",
    path: "/legal/personal-data",
    title: "Personal Data Processing Consent",
    shortTitle: "Personal Data",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: true,
    summary:
      "Consent text for processing personal data needed for account creation, authentication, media workflow operation, audit logs and privacy requests.",
    notice:
      "This consent is a structured draft. Adjust wording for the actual jurisdiction, business entity and statutory requirements.",
    sections: [
      {
        title: "1. Consent scope",
        paragraphs: [
          "By accepting this document during registration, the user consents to the processing of personal data required to provide VATranscribe functionality.",
          "This may include account data, authentication data, consent records, privacy request data, media workflow metadata, transcript metadata and billing-related data where enabled."
        ]
      },
      {
        title: "2. Processing purposes",
        bullets: [
          "Account creation and authentication.",
          "Session security and refresh token rotation.",
          "Operation of download, upload, transcription and export workflows.",
          "Quota management and subscription-related functionality.",
          "Legal consent version tracking.",
          "Security audit logging.",
          "Privacy request handling."
        ]
      },
      {
        title: "3. Data categories",
        bullets: [
          "Email address and account identifiers.",
          "Password hash and authentication metadata.",
          "User consent records and legal document versions.",
          "Job metadata, media asset metadata and transcript metadata.",
          "IP-derived request metadata where logged for security.",
          "Privacy request comments and status."
        ]
      },
      {
        title: "4. Withdrawal",
        paragraphs: [
          "The user may request consent revocation where applicable. Revocation may limit or prevent further access to parts of the service that require processing.",
          "Some records may continue to be retained where required for security, legal obligations, billing, dispute resolution or audit integrity."
        ]
      },
      {
        title: "5. Duration",
        paragraphs: [
          "Consent remains effective until revoked or until the account and associated data are deleted, subject to mandatory retention obligations.",
          "Production retention periods must be finalized in the Privacy Policy."
        ]
      }
    ]
  },
  {
    documentType: "cookies",
    slug: "cookies",
    path: "/legal/cookies",
    title: "Cookie Policy",
    shortTitle: "Cookies",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: false,
    summary:
      "Cookie Policy explaining essential cookies, local storage, analytics cookies and future tracking technology controls.",
    notice:
      "This page is ready structurally. Add real analytics and cookie inventory before production launch.",
    sections: [
      {
        title: "1. What cookies are",
        paragraphs: [
          "Cookies and similar technologies help websites remember state, protect sessions, measure usage and improve user experience.",
          "VATranscribe may also use browser storage for authentication state, theme preferences and product settings where applicable."
        ]
      },
      {
        title: "2. Essential technologies",
        bullets: [
          "Authentication/session storage required to keep users logged in.",
          "Security-related storage required to protect account access.",
          "Preference storage such as theme, language or product UI settings."
        ]
      },
      {
        title: "3. Analytics and marketing",
        paragraphs: [
          "Analytics or marketing tools are not finalized in this draft. If Google Analytics, Yandex Metrica, PostHog or other tools are added, list them here before launch.",
          "Where required by law, non-essential cookies should be blocked until the user gives consent."
        ]
      },
      {
        title: "4. User control",
        paragraphs: [
          "Users can control cookies through browser settings. Blocking essential cookies may break authenticated functionality.",
          "A production cookie banner or preference center should be added when non-essential tracking is enabled."
        ]
      }
    ]
  },
  {
    documentType: "refund",
    slug: "refund",
    path: "/legal/refund",
    title: "Refund Policy",
    shortTitle: "Refund",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: false,
    summary:
      "Refund Policy draft for future subscriptions, plan changes, failed payments, trials and exceptional refunds.",
    notice:
      "Commercial refund rules must be finalized before paid subscriptions are enabled.",
    sections: [
      {
        title: "1. Current status",
        paragraphs: [
          "VATranscribe is currently structured for future SaaS billing and subscription functionality. Paid subscription terms must be finalized before production payments are enabled.",
          "This Refund Policy is a draft for the future commercial layer."
        ]
      },
      {
        title: "2. Subscriptions",
        paragraphs: [
          "Paid plans may be billed monthly or yearly when enabled. Subscription periods, renewal behavior, cancellation behavior and plan limits should be displayed before payment.",
          "The user is responsible for reviewing the selected plan, billing period and quota limits before subscribing."
        ]
      },
      {
        title: "3. Refunds",
        paragraphs: [
          "A default production policy may allow discretionary refunds for duplicate charges, technical payment errors or legally required consumer cancellation rights.",
          "If a no-refund policy is chosen for consumed digital services, it must be clearly disclosed before payment and reviewed for the target jurisdiction."
        ]
      },
      {
        title: "4. Cancellations",
        paragraphs: [
          "Cancellation should stop future renewals but may not automatically refund the current billing period unless required by law or stated in the plan terms.",
          "If the product supports cancel-at-period-end, the dashboard should display the cancellation status."
        ]
      },
      {
        title: "5. Contact",
        paragraphs: [
          "Add a billing support email and expected response time before enabling paid subscriptions."
        ]
      }
    ]
  }
];

export const requiredRegistrationDocumentTypes: LegalDocumentType[] = [
  "terms",
  "privacy",
  "personal_data"
];

export function getLegalDocumentBySlug(slug: string): LegalDocumentConfig | undefined {
  return legalDocuments.find((document) => document.slug === slug);
}

export function getLegalDocumentByType(
  documentType: LegalDocumentType
): LegalDocumentConfig | undefined {
  return legalDocuments.find((document) => document.documentType === documentType);
}