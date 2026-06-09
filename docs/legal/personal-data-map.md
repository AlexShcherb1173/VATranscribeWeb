# P2-01 Personal data map


VATranscribe release-readiness legal/compliance artifact.
## Categories

| Category | Examples | Purpose | Retention |
|---|---|---|---|
| Account | email, password hash, account status, profile/display name | registration, login, account management | until account deletion plus legal retention where applicable |
| Security | IP address, user-agent, audit logs, refresh token hashes, CSRF cookie metadata | authentication security, abuse prevention, audit evidence | 180 days by default |
| Files | uploaded audio/video, downloaded media, generated transcripts, export artifacts | media processing, transcription and export workflows | media 30 days, exports 14 days, transcripts 90 days |
| Temporary files | temp chunks, intermediate artifacts | job execution and cleanup | 24 hours |
| Failed job files | partial outputs from failed jobs | troubleshooting and recovery | 7 days |
| YouTube cookies | encrypted per-user Netscape cookies.txt | user-specific download jobs | until user deletion/replacement |
| Billing | plan, subscription status, payment status, provider transaction id, invoices/receipts | billing and accounting when enabled | disabled until billing provider is enabled or retained by law |
| Monitoring | Sentry events, traces, technical logs | reliability, debugging and incident response | per monitoring/log retention policy |

## Processing purposes

- Registration and login.
- Upload, download, transcription and export workflows.
- Storage of results in the user account.
- Account and session security.
- Audit logs and abuse prevention.
- Quota, usage and subscription accounting.
- Support and privacy request handling.
- Legal obligations.
- Analytics only after consent where analytics is enabled.

## Processors

For P2-01, hosting, CDN, analytics, APM, payment and email providers are treated as disabled in legal text unless explicitly configured in production legal settings.
