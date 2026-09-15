# No-placeholder release checklist

Use this checklist before every public release.

## User-facing surfaces

- [ ] Marketing pages have no `Lorem ipsum`, `TODO`, `FIXME`, public test emails or unfinished placeholder text.
- [ ] Authenticated web app copy does not mention fake payments, demo payments or temporary payment placeholders.
- [ ] Legal pages use production-owned contact aliases.
- [ ] 404 pages are localized and not indexed.
- [ ] 500 fallback pages are available.
- [ ] Web app has a not-found route.
- [ ] Web app error boundary does not expose runtime stack traces to users.
- [ ] API production errors do not expose stack traces, SQL errors or filesystem paths.

## Allowed examples

Template placeholders may remain only in developer-only templates such as `.env.example`, `.env.production.example`, deployment runbooks and architecture input worksheets. These examples must be clearly marked as examples and must be rejected by production validation scripts where relevant.
