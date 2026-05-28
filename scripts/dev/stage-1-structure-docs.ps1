$ErrorActionPreference = "Stop"

$Root = "D:\DevProject\PythonProject\VATranscribeWeb"

if (-not (Test-Path $Root)) {
    throw "Project root not found: $Root"
}

Set-Location $Root

Write-Host "Stage 1: structure and documentation..."

$Dirs = @(
    "apps/marketing/src/pages",
    "apps/marketing/src/pages/tools",
    "apps/marketing/src/pages/blog",
    "apps/marketing/src/pages/docs",
    "apps/marketing/src/pages/legal",
    "apps/marketing/src/pages/resources",
    "apps/marketing/src/components/landing",
    "apps/marketing/src/components/pricing",
    "apps/marketing/src/components/monetization",
    "apps/marketing/src/components/seo",
    "apps/marketing/src/components/common",
    "apps/marketing/src/layouts",
    "apps/marketing/src/content/blog",
    "apps/marketing/src/content/docs",
    "apps/marketing/src/content/legal",
    "apps/marketing/src/content/resources",
    "apps/marketing/src/config",
    "apps/marketing/src/styles",
    "apps/marketing/public/og",
    "apps/marketing/public/screenshots",
    "apps/marketing/public/downloads",

    "apps/admin/src/app/router",
    "apps/admin/src/app/providers",
    "apps/admin/src/app/store",
    "apps/admin/src/app/styles",
    "apps/admin/src/pages/login",
    "apps/admin/src/pages/dashboard",
    "apps/admin/src/pages/users",
    "apps/admin/src/pages/subscriptions",
    "apps/admin/src/pages/payments",
    "apps/admin/src/pages/fiscal-receipts",
    "apps/admin/src/pages/plans",
    "apps/admin/src/pages/quotas",
    "apps/admin/src/pages/jobs",
    "apps/admin/src/pages/files",
    "apps/admin/src/pages/transcriptions",
    "apps/admin/src/pages/licenses",
    "apps/admin/src/pages/devices",
    "apps/admin/src/pages/desktop-releases",
    "apps/admin/src/pages/affiliate",
    "apps/admin/src/pages/ads",
    "apps/admin/src/pages/sponsored",
    "apps/admin/src/pages/legal-documents",
    "apps/admin/src/pages/consents",
    "apps/admin/src/pages/privacy-requests",
    "apps/admin/src/pages/webhooks",
    "apps/admin/src/pages/audit-logs",
    "apps/admin/src/pages/security-events",
    "apps/admin/src/pages/reports",
    "apps/admin/src/pages/settings",

    "apps/admin/src/features/admin-auth",
    "apps/admin/src/features/users-management",
    "apps/admin/src/features/billing-management",
    "apps/admin/src/features/payment-management",
    "apps/admin/src/features/quota-management",
    "apps/admin/src/features/job-management",
    "apps/admin/src/features/file-management",
    "apps/admin/src/features/license-management",
    "apps/admin/src/features/webhook-monitoring",
    "apps/admin/src/features/audit-monitoring",
    "apps/admin/src/features/privacy-management",
    "apps/admin/src/features/security-monitoring",

    "apps/admin/src/entities/admin-user",
    "apps/admin/src/entities/user",
    "apps/admin/src/entities/subscription",
    "apps/admin/src/entities/payment",
    "apps/admin/src/entities/fiscal-receipt",
    "apps/admin/src/entities/job",
    "apps/admin/src/entities/file",
    "apps/admin/src/entities/license",
    "apps/admin/src/entities/webhook-event",
    "apps/admin/src/entities/audit-log",
    "apps/admin/src/entities/security-event",

    "apps/admin/src/widgets/admin-shell",
    "apps/admin/src/widgets/admin-sidebar",
    "apps/admin/src/widgets/admin-topbar",
    "apps/admin/src/widgets/stats-cards",
    "apps/admin/src/widgets/revenue-chart",
    "apps/admin/src/widgets/recent-payments",
    "apps/admin/src/widgets/failed-jobs",
    "apps/admin/src/widgets/webhook-errors",
    "apps/admin/src/widgets/security-alerts",

    "apps/admin/src/shared/api",
    "apps/admin/src/shared/auth",
    "apps/admin/src/shared/config",
    "apps/admin/src/shared/hooks",
    "apps/admin/src/shared/lib",
    "apps/admin/src/shared/ui",

    "docs/architecture",
    "docs/api",
    "docs/billing",
    "docs/monetization",
    "docs/security",
    "docs/privacy",
    "docs/legal",
    "docs/desktop",
    "docs/deployment",
    "docs/roadmap",

    "scripts/dev",
    "scripts/migrations",
    "scripts/maintenance",
    "scripts/packaging",
    "scripts/reports",
    "scripts/security",
    "scripts/backup",

    "tests/api",
    "tests/worker",
    "tests/billing",
    "tests/monetization",
    "tests/security",
    "tests/privacy",
    "tests/compliance",
    "tests/integration",
    "tests/fixtures",

    "infra/nginx/sites",
    "infra/deploy",
    "infra/security",
    "infra/backup"
)

foreach ($Dir in $Dirs) {
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null

    $Gitkeep = Join-Path $Dir ".gitkeep"
    if (-not (Test-Path $Gitkeep)) {
        New-Item -ItemType File -Force -Path $Gitkeep | Out-Null
    }
}

function Write-TextFile {
    param(
        [string]$Path,
        [string[]]$Lines
    )

    $Parent = Split-Path $Path -Parent

    if ($Parent -and -not (Test-Path $Parent)) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }

    Set-Content -Encoding UTF8 -Path $Path -Value $Lines
}

Write-TextFile "apps/marketing/README.md" @(
    "# apps/marketing",
    "",
    "Public marketing application for VATranscribeWeb.",
    "",
    "Purpose:",
    "- landing page",
    "- SEO pages",
    "- pricing page",
    "- download page",
    "- blog",
    "- documentation pages",
    "- legal pages",
    "- affiliate and resources pages",
    "- advertising and sponsored content slots",
    "",
    "Target local port: 4321.",
    "",
    "Production domain:",
    "- https://<brand-domain>",
    "- https://www.<brand-domain>",
    "",
    "Status: Stage 1 skeleton."
)

Write-TextFile "apps/admin/README.md" @(
    "# apps/admin",
    "",
    "Internal admin panel for VATranscribeWeb.",
    "",
    "Purpose:",
    "- users management",
    "- subscriptions management",
    "- payments management",
    "- fiscal receipts",
    "- quotas and credits",
    "- jobs monitoring",
    "- files monitoring",
    "- licenses and devices",
    "- webhooks monitoring",
    "- audit logs",
    "- security events",
    "- privacy requests",
    "- ads, affiliate and sponsored placements",
    "",
    "Target local port: 5174.",
    "",
    "Production domain:",
    "- https://admin.<brand-domain>",
    "",
    "Security requirements:",
    "- admin-only authentication",
    "- RBAC",
    "- audit logs",
    "- optional 2FA",
    "- optional IP allowlist",
    "",
    "Status: Stage 1 skeleton."
)

Write-TextFile "docs/architecture/project-structure.md" @(
    "# Project Structure",
    "",
    "VATranscribeWeb is a commercial SaaS/Web monorepo based on the existing VATranscribe_clean core.",
    "",
    "Root structure:",
    "",
    "VATranscribeWeb/",
    "- apps/",
    "  - marketing/   public landing, SEO, blog, docs, legal",
    "  - web/         user SaaS app and dashboard",
    "  - admin/       internal admin panel",
    "  - api/         FastAPI backend",
    "  - worker/      Celery background worker",
    "  - desktop/     desktop app shell",
    "- packages/",
    "  - core/        shared media, download and transcription logic",
    "  - shared-types/ shared TypeScript contracts",
    "  - sdk/         future API SDK",
    "- infra/         Docker, Nginx, compose, deploy and backup",
    "- alembic/       database migrations",
    "- docs/          architecture, billing, security and privacy",
    "- scripts/       dev, migrations, maintenance and reports",
    "- tests/         api, worker, billing, security and privacy",
    "- .github/       CI/CD workflows",
    "",
    "Stage 1 goal:",
    "- fix the final target project structure",
    "- add base documentation",
    "- prepare skeletons for future implementation"
)

Write-TextFile "docs/architecture/domain-map.md" @(
    "# Domain Map",
    "",
    "Local development:",
    "",
    "| Area | URL | Purpose |",
    "|---|---|---|",
    "| Marketing | http://localhost:4321 | public landing and SEO site |",
    "| Web App | http://localhost:5173 | user dashboard and SaaS app |",
    "| Admin | http://localhost:5174 | internal admin panel |",
    "| API | http://localhost:8000 | FastAPI backend |",
    "| API Docs | http://localhost:8000/docs | Swagger/OpenAPI |",
    "",
    "Production target:",
    "",
    "| Area | Domain | Purpose |",
    "|---|---|---|",
    "| Marketing | https://<brand-domain> | public website |",
    "| Web App | https://app.<brand-domain> | user app |",
    "| Admin | https://admin.<brand-domain> | internal admin |",
    "| API | https://api.<brand-domain> | backend API |",
    "| Storage/CDN | https://cdn.<brand-domain> | public or signed assets |"
)

Write-TextFile "docs/security/overview.md" @(
    "# Security Overview",
    "",
    "Security must be part of the base architecture, not a later patch.",
    "",
    "Core areas:",
    "- authentication and sessions",
    "- password hashing",
    "- refresh token rotation",
    "- role-based access control",
    "- admin security",
    "- API rate limits",
    "- CORS allowlist",
    "- webhook signature verification",
    "- user file isolation",
    "- storage access control",
    "- SSRF protection for URL downloads",
    "- audit logs",
    "- security events",
    "- backup and recovery",
    "- secrets management",
    "",
    "Critical principle:",
    "Every user-owned entity must be checked by owner_id/user_id before access."
)

Write-TextFile "docs/security/threat-model.md" @(
    "# Threat Model",
    "",
    "Main protected assets:",
    "- user accounts",
    "- uploaded media files",
    "- transcripts and exports",
    "- payment records",
    "- fiscal receipts",
    "- subscriptions and quotas",
    "- admin operations",
    "- API keys and secrets",
    "",
    "High-risk zones:",
    "1. File upload and processing.",
    "2. URL downloading and external media probing.",
    "3. Payment webhooks.",
    "4. Admin panel.",
    "5. Public storage and download URLs.",
    "",
    "Initial mitigations:",
    "- validate file size and MIME types",
    "- use subprocess without shell=True",
    "- block localhost and private IP downloads",
    "- verify webhook signatures",
    "- log admin actions",
    "- keep secrets outside Git"
)

Write-TextFile "docs/privacy/overview.md" @(
    "# Privacy Overview",
    "",
    "VATranscribeWeb processes personal data and user-generated content.",
    "",
    "Personal data categories:",
    "- email",
    "- username and profile data",
    "- IP address",
    "- user-agent",
    "- cookies",
    "- payment identifiers",
    "- device identifiers",
    "- uploaded files",
    "- transcripts",
    "- job logs",
    "",
    "Required flows:",
    "- consent records",
    "- privacy policy acceptance",
    "- user data export",
    "- account deletion request",
    "- file deletion",
    "- email unsubscribe",
    "- data retention rules"
)

Write-TextFile "docs/privacy/data-retention-policy.md" @(
    "# Data Retention Policy",
    "",
    "Initial retention model:",
    "",
    "| Data type | Free users | Paid users | Notes |",
    "|---|---:|---:|---|",
    "| Uploaded files | 7 days | 30-90 days | depends on plan |",
    "| Generated transcripts | 30 days | 365 days | configurable |",
    "| Job logs | 30 days | 90 days | technical diagnostics |",
    "| Payment records | accounting period | accounting period | legal and finance |",
    "| Audit logs | 365 days | 365 days | admin and security |",
    "",
    "Exact periods must be finalized with legal/accounting review."
)

Write-TextFile "docs/monetization/overview.md" @(
    "# Monetization Overview",
    "",
    "VATranscribeWeb monetization layers:",
    "1. Subscriptions.",
    "2. Credit packs and transcription minutes.",
    "3. Desktop licenses.",
    "4. B2B/API access.",
    "5. Affiliate links.",
    "6. Advertising blocks.",
    "7. Sponsored placements.",
    "",
    "Main revenue flow:",
    "Landing/SEO -> registration -> trial -> subscription/credits/license.",
    "",
    "Additional revenue flow:",
    "Blog/tools/resources -> affiliate links/ads/sponsored placements."
)

Write-TextFile "docs/monetization/pricing-model.md" @(
    "# Pricing Model",
    "",
    "Initial target model:",
    "",
    "| Plan | Purpose | Billing |",
    "|---|---|---|",
    "| Free | trial and product discovery | free |",
    "| Starter | light users | monthly/yearly |",
    "| Pro | active creators and professionals | monthly/yearly |",
    "| Business | teams, API and high usage | monthly/yearly/custom |",
    "",
    "Additional paid units:",
    "- credit packs",
    "- extra transcription minutes",
    "- desktop license",
    "- API access"
)

Write-TextFile "docs/billing/billing-flow.md" @(
    "# Billing Flow",
    "",
    "Subscription flow:",
    "pricing page -> checkout request -> payment provider -> provider webhook -> payment succeeded -> subscription active -> quotas synced -> user gets paid access",
    "",
    "Rule:",
    "Frontend redirect is not a source of truth. Payment provider webhook is the source of truth."
)

Write-TextFile "docs/api/endpoints.md" @(
    "# API Endpoints",
    "",
    "Existing transferred endpoint groups:",
    "- auth",
    "- profile",
    "- settings",
    "- plans",
    "- billing",
    "- quota",
    "- downloads",
    "- uploads",
    "- files",
    "- media_assets",
    "- jobs",
    "- transcriptions",
    "- transcripts",
    "- exports",
    "",
    "Planned endpoint groups:",
    "- subscriptions",
    "- payments",
    "- invoices",
    "- fiscal_receipts",
    "- credits",
    "- licenses",
    "- devices",
    "- desktop",
    "- affiliate",
    "- ads",
    "- sponsored",
    "- legal",
    "- consents",
    "- privacy",
    "- admin_*"
)

Write-TextFile "docs/roadmap/implementation-stages.md" @(
    "# Implementation Stages",
    "",
    "Stage 0 - Migration",
    "- create VATranscribeWeb repository",
    "- migrate working modules from VATranscribe_clean",
    "- keep old implementations safe",
    "",
    "Stage 1 - Structure and Documentation",
    "- create apps/marketing skeleton",
    "- create apps/admin skeleton",
    "- create docs/security",
    "- create docs/privacy",
    "- create docs/monetization",
    "- create scripts/reports",
    "- create tests/security and tests/privacy",
    "",
    "Stage 2 - Security and Privacy Foundation",
    "- harden auth",
    "- add consent records",
    "- add audit logs",
    "- add privacy request models",
    "- add file ownership checks",
    "",
    "Stage 3 - Billing Core",
    "- plans",
    "- subscriptions",
    "- payments",
    "- webhooks",
    "- fiscal receipts",
    "",
    "Stage 4 - Usage, Quota and Credits",
    "- usage events",
    "- quota reservations",
    "- credit packs",
    "- monthly reset",
    "",
    "Stage 5 - Desktop Licensing",
    "- licenses",
    "- devices",
    "- activation",
    "- app versions",
    "",
    "Stage 6 - Marketing Monetization",
    "- affiliate",
    "- ads",
    "- sponsored placements",
    "- reports"
)

Write-TextFile "scripts/reports/README.md" @(
    "# scripts/reports",
    "",
    "Report scripts for finance, billing and monetization.",
    "",
    "Planned scripts:",
    "- export_payments_csv.py",
    "- export_receipts_csv.py",
    "- export_refunds_csv.py",
    "- export_affiliate_income_csv.py",
    "- export_ad_income_csv.py",
    "- export_kudir_income_csv.py",
    "- monthly_revenue_report.py"
)

Write-TextFile "tests/security/README.md" @(
    "# tests/security",
    "",
    "Security tests.",
    "",
    "Planned coverage:",
    "- auth tokens",
    "- password hashing",
    "- permissions",
    "- rate limits",
    "- webhook signatures",
    "- file access",
    "- user isolation",
    "- admin permissions"
)

Write-TextFile "tests/privacy/README.md" @(
    "# tests/privacy",
    "",
    "Privacy and personal data tests.",
    "",
    "Planned coverage:",
    "- user consents",
    "- data export",
    "- account deletion",
    "- retention policy",
    "- email unsubscribe"
)

Write-Host "Stage 1 structure and documentation created."
Write-Host ""
Write-Host "Next commands:"
Write-Host "git status"
Write-Host "git add ."
Write-Host 'git commit -m "docs: fix stage 1 structure and documentation"'