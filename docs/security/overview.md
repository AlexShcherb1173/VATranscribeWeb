# Security Overview

Security must be part of the base architecture, not a later patch.

Core areas:
- authentication and sessions
- password hashing
- refresh token rotation
- role-based access control
- admin security
- API rate limits
- CORS allowlist
- webhook signature verification
- user file isolation
- storage access control
- SSRF protection for URL downloads
- audit logs
- security events
- backup and recovery
- secrets management

Critical principle:
Every user-owned entity must be checked by owner_id/user_id before access.
