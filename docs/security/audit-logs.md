# Audit Logs

Stage 2.3 implements audit logging for real auth and billing flows.

## Database table

Audit events are stored in `audit_logs`.

Tracked fields:

- actor_user_id
- action
- entity_type
- entity_id
- meta_json
- ip_hash
- user_agent_hash
- created_at

## Auth events

Implemented actions:

- auth.register_success
- auth.register_failed
- auth.login_success
- auth.login_failed
- auth.refresh_success
- auth.refresh_failed
- auth.logout
- auth.logout_all

## Billing events

Implemented actions:

- billing.overview_viewed
- billing.upgrade_requested
- billing.upgrade_succeeded
- billing.upgrade_failed

## Admin actions

Backend admin routers are not implemented yet.

When admin backend endpoints are added, every admin mutation must create an audit event:

- admin.user.updated
- admin.user.blocked
- admin.subscription.updated
- admin.payment.refunded
- admin.plan.updated
- admin.quota.updated
- admin.file.deleted
- admin.legal_document.published
- admin.security_event.resolved

## Privacy note

IP address and user-agent are stored only as SHA-256 hashes.
Email values in metadata must be masked.
