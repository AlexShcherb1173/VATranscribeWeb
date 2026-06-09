# Stage 3.8 Marketing ↔ SaaS Links

Stage 3.8 centralizes links between the Astro marketing app and the React SaaS app.

## Implemented

- Central marketing link helper:
  - `apps/marketing/src/config/links.ts`
- Marketing CTA links now use:
  - `getSaasLink("login")`
  - `getSaasLink("register")`
  - `getSaasLink("register", { plan: "pro" })`
  - `getSaasLink("dashboard")`
  - `getSaasLink("billing", { plan: "pro" })`
- Public app base URL can be configured through:
  - `PUBLIC_VATRANSCRIBE_APP_URL`
- Web app has explicit routes:
  - `/auth/login`
  - `/auth/register`
  - `/dashboard`
  - `/billing`
- Register route reads `?plan=` and redirects to billing with selected plan after registration.
- Web pricing page now links to explicit auth routes instead of `/?plan=...`.

## Route contract

Marketing layer:

- `/pricing`
- `/download`
- `/blog`
- `/resources`
- `/docs`
- `/changelog`

SaaS web layer:

- `/auth/login`
- `/auth/register`
- `/auth/register?plan=pro`
- `/app`
- `/app/downloads`
- `/app/billing?plan=pro`

## Notes

Backend is not changed in this stage.
