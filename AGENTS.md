# VATranscribeWeb Agent Instructions

## Scope

These instructions apply throughout this repository unless a more specific
AGENTS.md exists deeper in the tree.

Honor the user's task boundaries.

For inspection, audit, review, or analysis tasks, remain read-only unless the
user explicitly authorizes implementation.

Do not request network access, elevated permissions, or access outside the
workspace unless it is necessary for the task. Explain why additional
permission is required before requesting it.

Derive decisions from the current repository state: source code, imports,
manifests, scripts, workflows, Dockerfiles, configuration templates, and tests.

Distinguish VERIFIED facts from assumptions and unknowns.

Do not invent commands, services, architecture, behavior, test results, or
policies.

A command being declared in the repository does not prove that it passes.

## Git and change discipline

- Never commit directly to main.
- Use a scoped branch or worktree for implementation work.
- Before editing, verify:
  - repository root;
  - current branch;
  - HEAD;
  - git status.
- Preserve pre-existing user changes.
- Make minimal, reviewable changes.
- Do not modify unrelated files.
- Avoid incidental formatting or cleanup.
- Do not perform unrelated dependency upgrades.
- Do not stage, commit, push, merge, rebase, deploy, or create releases unless
  explicitly authorized.
- Review the final git diff and git status before declaring completion.
- Never bypass branch protection, required CI checks, or security gates.

## Repository architecture

Current major areas include:

- `apps/api` — FastAPI/Uvicorn backend.
- `apps/worker` — Celery background processing.
- `apps/web` — React/TypeScript/Vite user application.
- `apps/marketing` — Astro marketing/documentation/legal site.
- `packages/core/vatranscribe_core` — shared Python media, download,
  transcription, storage, export, URL-safety, and domain code.
- `alembic/` with root `alembic.ini` — database migrations.
- `infra/` — Docker, Compose, proxy/TLS, deployment, rollback, backup/restore,
  logging, monitoring, and production infrastructure.
- `tests/` — repository test suite.

Some directories may be scaffolds, duplicated-looking trees may exist, and
directory presence alone does not establish runtime use.

Follow actual imports, manifests, module resolution, runtime entry points, and
workflows before changing or removing code.

Respect runtime and package-manager versions declared by the current manifests
and Dockerfiles.

## API and compatibility

Preserve existing API routes, schemas, response/status behavior, task names,
and frontend/backend contracts unless a change is explicitly requested.

Never weaken:

- authentication;
- authorization;
- resource ownership checks;
- quota enforcement;
- audit logging;
- rate limiting;
- security headers;
- privacy/consent controls;
- billing/payment validation.

Add regression tests for bug fixes, including relevant negative cases and
authorization boundaries.

## Security

Treat all user-controlled data as untrusted, including:

- URLs;
- redirects;
- uploads;
- filenames;
- media metadata;
- transcripts;
- form/API input.

Consider where relevant:

- SSRF;
- IDOR;
- path traversal;
- injection;
- XSS;
- CSRF;
- authorization bypass;
- unsafe redirects;
- unsafe subprocess invocation;
- unsafe file handling.

Preserve validation across API, worker, and shared-engine boundaries.

Do not bypass URL validation for redirects or resolved media URLs.

Do not expose private storage through public static routing.

## Secrets and sensitive data

Never expose, print, commit, copy, or place secrets in:

- code;
- logs;
- reports;
- prompts;
- examples;
- artifacts.

Do not inspect `.env` unless the user explicitly authorizes it for a specific
task.

Apply the same restriction to:

- runtime environment files;
- credentials;
- tokens;
- private keys;
- cookie files;
- local secret files/directories;
- database dumps;
- backups.

Configuration templates such as `.env.example` may be inspected when relevant,
but do not reproduce secret-like values.

## Database and Alembic

Use Alembic for database schema changes.

Before creating a migration:

- inspect the current revision chain;
- inspect model metadata registration;
- verify the current migration conventions.

Review migrations for:

- destructive operations;
- locks;
- backfills;
- defaults;
- constraints;
- indexes;
- compatibility between old/new application versions;
- rollback limitations.

Do not casually rewrite historical migrations or substitute ad hoc SQL for an
Alembic migration.

Do not assume migration commands are isolated from configured databases.

## Jobs, transactions, and consistency

For API/worker changes, consider:

- transaction boundaries;
- partial failures;
- concurrency;
- retries;
- cancellation;
- idempotency;
- duplicate Celery delivery;
- database/filesystem consistency;
- task dispatch ordering.

Repeated execution must not duplicate billing/quota effects or corrupt job,
media, transcript, or artifact state.

## Infrastructure and production

Treat changes under Docker, Compose, Nginx, CI/CD, deployment, rollback,
backup/restore, security scanning, and production configuration as
security-sensitive.

Do not weaken:

- container hardening;
- private service exposure;
- TLS/security headers;
- storage isolation;
- egress controls;
- immutable release identity;
- archive/integrity validation;
- SSH host verification;
- backup integrity;
- monitoring;
- rollback behavior.

Do not run operational or deployment scripts merely to inspect their behavior.

Do not access production systems unless the user explicitly authorizes a
specific production operation.

## Dependencies and lockfiles

Do not modify dependency manifests, lockfiles, overrides, or scanner
configuration unless required by the task.

Do not run dependency installation merely as incidental validation.

When dependencies change, keep manifests and lockfiles consistent and review
the security/supply-chain impact.

## Validation

Use the smallest relevant validation first.

Verified canonical commands include:

### Backend

```bash
python -m pytest
```

### Web

```bash
npm run lint --workspace apps/web
npm run typecheck --workspace apps/web
npm run build:web
```

### Marketing

```bash
npm run check --workspace apps/marketing
npm run build:marketing
```

### Frontend aggregate

```bash
npm run build:frontend
```

### Lockfile/security policy

```bash
bash scripts/security/check-lockfiles.sh
```

Other repository commands may exist in package manifests, workflows,
documentation, or scripts. Inspect their implementation and side effects
before running them.

Important limitations:

- API workspace `lint` and `typecheck` currently use Python `compileall`; do
  not describe that as full linting or static type analysis.
- Frontend test scripts may be placeholders; inspect them before claiming test
  coverage.
- Ruff and mypy configuration does not by itself establish a canonical command.
- Docker Compose configuration can load environment files and may output
  interpolated values. Do not run it during restricted secret-safe inspections
  without appropriate authorization.
- Security scanners may require network access or inspect sensitive local data.

Never claim validation passed if it was skipped, failed, blocked, or only ran a
placeholder command.

## Generated and local data

Exclude generated/local data from routine searches and changes, including
typical:

- virtual environments;
- `node_modules`;
- Python bytecode/cache;
- pytest/mypy/Ruff caches;
- coverage output;
- build output;
- `.turbo`;
- `.vite`;
- Astro generated state;
- IDE metadata;
- runtime storage;
- logs;
- backups;
- database dumps;
- generated security/release evidence.

Consult `.gitignore` for exact repository patterns.

Ignored does not mean safe to delete.

## Definition of Done

Before declaring a task complete:

1. Confirm the requested behavior was implemented with minimal relevant changes.
2. Confirm existing API/security contracts were preserved unless explicitly
   changed.
3. Add regression coverage for bug fixes.
4. Review relevant transaction, retry, idempotency, migration, security, and
   infrastructure risks.
5. Run the smallest relevant checks first and broader validation where justified
   and authorized.
6. Review `git diff` and `git status`.
7. Check for unrelated changes, generated artifacts, secrets, and accidental
   contract changes.
8. Report:
   - changed files;
   - commands/tests executed;
   - outcomes;
   - skipped or failed validation and reasons;
   - unresolved risks.

Do not claim full validation when checks were skipped or failed.
