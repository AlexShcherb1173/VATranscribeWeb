# Stage 4 P3-08: Production rehearsal

## Purpose

P3-08 is the final integrated release rehearsal before public production launch. It verifies that independent P3 evidence gates work together as one release process. Runtime secrets are loaded from `/opt/vatranscribe/secrets/.env.runtime`.

DO NOT treat foundation tests as production launch approval. Production launch requires live evidence.

## Covered gates

- Staging deploy.
- Runtime secrets validation.
- Migrations via Alembic.
- Smoke checks.
- Rollback timing, target <= 5 minutes.
- Backup/restore proof.
- Auth checks.
- Private files/storage checks.
- Background jobs/worker checks.
- Billing checks.
- Cookie consent checks.
- Analytics checks.
- Monitoring/APM/logging checks.
- Legal/152-ФЗ and supply-chain evidence linkage.

## Architecture decision

P3-08 is implemented as an evidence-first operational workflow:

- `infra/deploy/run-production-rehearsal.sh` orchestrates the rehearsal.
- `infra/deploy/redact-production-rehearsal-evidence.sh` sanitizes outputs.
- `infra/deploy/validate-production-rehearsal.sh` validates redacted evidence markers.
- `docs/release/final-production-go-nogo-checklist.md` defines final release gates.

## Production status

P3-08 foundation is closed when scripts, docs, and static tests pass. Production evidence is closed only when the rehearsal is executed on staging/production-like infrastructure and redacted evidence passes validation.
