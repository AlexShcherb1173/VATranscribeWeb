# apps/admin

Internal admin panel for VATranscribeWeb.

Purpose:
- users management
- subscriptions management
- payments management
- fiscal receipts
- quotas and credits
- jobs monitoring
- files monitoring
- licenses and devices
- webhooks monitoring
- audit logs
- security events
- privacy requests
- ads, affiliate and sponsored placements

Target local port: 5174.

Production domain:
- https://admin.<brand-domain>

Security requirements:
- admin-only authentication
- RBAC
- audit logs
- optional 2FA
- optional IP allowlist

Status: Stage 1 skeleton.
