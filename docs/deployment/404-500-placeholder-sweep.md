# P2-09 404/500 and placeholder sweep

This release-readiness step validates the public and authenticated error experience before launch.

## Scope

- Marketing has explicit English and Russian 404 pages.
- Marketing has static 500 fallback pages.
- Web app has a catch-all not-found route.
- Web app has a production-safe error boundary.
- API has production-safe exception handlers and does not expose stack traces in production responses.
- User-facing placeholder copy is removed from marketing and authenticated UI text.

## Placeholder policy

User-facing surfaces must not contain unfinished copy such as `Lorem ipsum`, `TODO`, `FIXME`, public test emails, demo payment copy or launch-blocking placeholder warnings.

Technical examples are allowed only in files that are clearly templates, runbooks or developer documentation. Examples must not be rendered on public marketing pages or in the authenticated user workspace.

## Verification

Run:

```bash
pytest tests/security/test_404_500_placeholder_sweep_static.py -v
pytest tests/privacy/test_no_user_facing_placeholders_static.py -v
npm --prefix apps/web run build
npm --prefix apps/marketing run build
```
