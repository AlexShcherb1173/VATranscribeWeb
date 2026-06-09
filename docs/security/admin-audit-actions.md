# Admin Audit Actions

Admin backend endpoints are planned but not implemented yet.

When implemented, admin actions must follow this rule:

Every admin mutation must write one audit event before returning success.

## Required metadata

- admin actor user id
- action
- entity type
- entity id
- minimal metadata
- IP hash
- user-agent hash

## Planned actions

- admin.user.viewed
- admin.user.updated
- admin.user.blocked
- admin.subscription.updated
- admin.payment.refunded
- admin.plan.created
- admin.plan.updated
- admin.quota.updated
- admin.file.deleted
- admin.legal_document.created
- admin.legal_document.published
- admin.privacy_request.processed
- admin.security_event.resolved
