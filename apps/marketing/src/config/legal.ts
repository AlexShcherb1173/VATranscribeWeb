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

export const LEGAL_VERSION = "2.0";
export const LEGAL_EFFECTIVE_DATE = "2026-06-10";

export const legalDocuments: LegalDocumentConfig[] = [
  {
    "documentType": "terms",
    "slug": "terms",
    "path": "/legal/terms",
    "title": "Terms of Service",
    "shortTitle": "Terms",
    "requiredForRegistration": true,
    "summary": "Terms governing access to VATranscribe, including account use, media processing, quotas, acceptable use and service limitations.",
    "notice": "VATranscribe is operated in pre-release mode by a self-employed individual operator. Paid billing is disabled until a verified payment workflow is enabled.",
    "sections": [
      {
        "title": "1. Scope",
        "paragraphs": [
          "These Terms govern access to VATranscribe, including the public website, authenticated dashboard, API-backed upload, download, transcription, export, quota and account functionality.",
          "By creating an account or using protected functionality, the user accepts these Terms and the required legal documents presented during registration."
        ]
      },
      {
        "title": "2. Operator and contacts",
        "paragraphs": [
          "Operator type: individual / self-employed operator.",
          "Operator name, legal address and registration data are configured through deployment legal settings and must be finalized before public production launch.",
          "Legal contact: legal@example.com. Support contact: legal@example.com."
        ]
      },
      {
        "title": "3. Account and security",
        "paragraphs": [
          "Users are responsible for keeping credentials secure and for all activity performed through their account."
        ],
        "bullets": [
          "The service may enforce password policy, refresh token rotation, CSRF protection and rate limits.",
          "The service may suspend sessions or accounts that create security or abuse risk."
        ]
      },
      {
        "title": "4. Media processing",
        "paragraphs": [
          "The user is responsible for having rights and permissions to upload, download, process, transcribe, store and export submitted media.",
          "The service must not be used for unlawful content, rights infringement, abusive automation, unauthorized access attempts or circumvention of third-party restrictions."
        ]
      },
      {
        "title": "5. YouTube cookies",
        "paragraphs": [
          "If enabled, a user may upload a Netscape cookies.txt file for that user's own jobs. The file is stored encrypted per user, used only for the user's processing tasks and can be deleted or replaced by the user.",
          "The user is responsible for complying with third-party platform terms."
        ]
      },
      {
        "title": "6. Quotas and limits",
        "paragraphs": [
          "VATranscribe may enforce storage, upload, download, export, transcription, job and rate limits. Operations can be rejected, stopped or deleted when limits or retention policies apply."
        ]
      },
      {
        "title": "7. Billing status",
        "paragraphs": [
          "Paid billing and paid subscription activation are disabled until a production payment provider and verified payment workflow are enabled."
        ]
      },
      {
        "title": "8. Privacy requests and deletion",
        "paragraphs": [
          "Users may request export, deletion or correction of account-related data where legally and technically applicable. Some records may be retained for security, legal, billing or audit reasons."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  },
  {
    "documentType": "privacy",
    "slug": "privacy",
    "path": "/legal/privacy",
    "title": "Privacy Policy",
    "shortTitle": "Privacy",
    "requiredForRegistration": true,
    "summary": "Privacy Policy describing data categories, processing purposes, retention, user rights and third-party processor status for VATranscribe.",
    "notice": "Third-party processors are disabled for P2-01 unless explicitly configured in production legal settings.",
    "sections": [
      {
        "title": "1. Controller / operator",
        "paragraphs": [
          "VATranscribe is operated by an individual / self-employed operator in pre-release mode. Operator details are configured through LEGAL_* deployment settings and must be finalized before public production launch.",
          "Privacy contact: privacy@example.com. Legal contact: legal@example.com."
        ]
      },
      {
        "title": "2. Data categories",
        "bullets": [
          "Account: email, password hash, account status, profile/display name where provided.",
          "Security: IP address, user-agent, audit logs, refresh token hashes, CSRF cookie metadata and security events.",
          "Files: uploaded audio/video, downloaded media, generated transcripts, export artifacts in txt/srt/vtt/json formats and job metadata.",
          "YouTube cookies: encrypted per-user Netscape cookies.txt file if uploaded by the user.",
          "Billing: plan, subscription status, payment status, provider transaction id, invoices or receipts where enabled.",
          "Monitoring: Sentry events, error traces and technical logs where monitoring is enabled."
        ]
      },
      {
        "title": "3. Purposes",
        "bullets": [
          "Registration and login.",
          "Providing upload, download, transcription and export workflows.",
          "Storing results in the user account.",
          "Securing accounts and sessions.",
          "Audit logging and abuse prevention.",
          "Quota, usage and subscription accounting.",
          "Support and privacy request handling.",
          "Legal obligations and service reliability.",
          "Analytics and improvement only after consent where analytics is enabled."
        ]
      },
      {
        "title": "4. Retention",
        "bullets": [
          "Uploaded/downloaded media: 30 days by default or until user deletion.",
          "Export artifacts: 14 days by default or until user deletion.",
          "Transcripts: 90 days by default or until user deletion.",
          "Temporary files: 24 hours.",
          "Failed job files: 7 days.",
          "Audit/security logs: 180 days.",
          "Account deletion processing window: 30 days.",
          "Backups: 7 daily, 4 weekly and 6 monthly backups.",
          "Billing records: disabled until billing is enabled or retained as required by law."
        ]
      },
      {
        "title": "5. Third parties",
        "paragraphs": [
          "For P2-01, hosting, CDN, analytics, APM, payment and email processors are treated as disabled unless configured in production legal settings. When enabled, this policy must list real providers, countries and data transfer details."
        ]
      },
      {
        "title": "6. User rights",
        "bullets": [
          "Request access to personal data.",
          "Request data export where supported.",
          "Request deletion where legally and technically possible.",
          "Request correction of inaccurate data.",
          "Withdraw consent where processing is based on consent."
        ]
      },
      {
        "title": "7. Russian personal data status",
        "paragraphs": [
          "If personal data of Russian citizens is processed, 152-FZ readiness must be completed before public production launch, including operator status, localization decision and RKN notification status where applicable."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  },
  {
    "documentType": "personal_data",
    "slug": "personal-data",
    "path": "/legal/personal-data",
    "title": "Consent to Personal Data Processing",
    "shortTitle": "Personal Data",
    "requiredForRegistration": true,
    "summary": "Consent for processing personal data needed for account creation, authentication, media workflows, audit logs, quota accounting and privacy requests.",
    "notice": "This consent is separated from the Terms and Privacy Policy and is required for account registration.",
    "sections": [
      {
        "title": "1. Consent scope",
        "paragraphs": [
          "By accepting this document, the user gives consent to processing personal data required to provide VATranscribe functionality."
        ]
      },
      {
        "title": "2. Data covered",
        "bullets": [
          "Account and authentication data.",
          "Security logs and audit events.",
          "Uploaded and downloaded media, transcripts and export artifacts.",
          "YouTube cookies.txt if the user uploads it.",
          "Quota, usage, subscription and billing-related data where enabled.",
          "Support and privacy request data."
        ]
      },
      {
        "title": "3. Processing operations",
        "paragraphs": [
          "Processing may include collection, recording, organization, storage, adaptation, retrieval, use, transfer to configured processors where applicable, blocking, deletion and destruction."
        ]
      },
      {
        "title": "4. Withdrawal",
        "paragraphs": [
          "The user may withdraw consent where processing is based on consent. Withdrawal may limit access to the service. Some records may continue to be processed where required for security, legal obligations, billing, dispute resolution or audit evidence."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  },
  {
    "documentType": "cookies",
    "slug": "cookies",
    "path": "/legal/cookies",
    "title": "Cookie Policy",
    "shortTitle": "Cookies",
    "requiredForRegistration": false,
    "summary": "Cookie Policy describing essential cookies, browser storage and the disabled-by-default analytics/marketing tracking model.",
    "notice": "Analytics and marketing cookies are disabled for P2-01 unless enabled through a separate consent-aware integration.",
    "sections": [
      {
        "title": "1. Essential cookies",
        "paragraphs": [
          "VATranscribe may use cookies and browser storage required for authentication, CSRF protection, session security, language and interface preferences."
        ]
      },
      {
        "title": "2. Non-essential tracking",
        "paragraphs": [
          "Analytics cookies, marketing pixels and CRM/ad pixels are disabled unless explicitly configured and gated by consent where required."
        ]
      },
      {
        "title": "3. User choice",
        "paragraphs": [
          "When non-essential tracking is enabled, users must be given a clear choice before activation where required by law."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  },
  {
    "documentType": "refund",
    "slug": "refund",
    "path": "/legal/refund",
    "title": "Refund Policy",
    "shortTitle": "Refunds",
    "requiredForRegistration": false,
    "summary": "Refund Policy for the current state where paid billing is disabled until a verified payment provider is configured.",
    "notice": "Paid subscriptions must not be enabled until payment provider, refund rules, invoices and fiscal receipt requirements are finalized.",
    "sections": [
      {
        "title": "1. Current billing status",
        "paragraphs": [
          "Paid billing is disabled for P2-01. The service may show plan and quota information, but paid-plan activation requires a production payment provider and verified webhook flow."
        ]
      },
      {
        "title": "2. Future payments",
        "paragraphs": [
          "Before payments are enabled, the service must publish exact pricing, billing period, renewal, cancellation, refund, invoice and fiscal receipt rules."
        ]
      },
      {
        "title": "3. Contact",
        "paragraphs": [
          "Billing and refund questions should be sent to the configured support contact."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
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
