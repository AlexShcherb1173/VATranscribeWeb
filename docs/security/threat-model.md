# Threat Model

Main protected assets:
- user accounts
- uploaded media files
- transcripts and exports
- payment records
- fiscal receipts
- subscriptions and quotas
- admin operations
- API keys and secrets

High-risk zones:
1. File upload and processing.
2. URL downloading and external media probing.
3. Payment webhooks.
4. Admin panel.
5. Public storage and download URLs.

Initial mitigations:
- validate file size and MIME types
- use subprocess without shell=True
- block localhost and private IP downloads
- verify webhook signatures
- log admin actions
- keep secrets outside Git
