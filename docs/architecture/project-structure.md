# Project Structure

VATranscribeWeb is a commercial SaaS/Web monorepo based on the existing VATranscribe_clean core.

Root structure:

VATranscribeWeb/
- apps/
  - marketing/   public landing, SEO, blog, docs, legal
  - web/         user SaaS app and dashboard
  - admin/       internal admin panel
  - api/         FastAPI backend
  - worker/      Celery background worker
  - desktop/     desktop app shell
- packages/
  - core/        shared media, download and transcription logic
  - shared-types/ shared TypeScript contracts
  - sdk/         future API SDK
- infra/         Docker, Nginx, compose, deploy and backup
- alembic/       database migrations
- docs/          architecture, billing, security and privacy
- scripts/       dev, migrations, maintenance and reports
- tests/         api, worker, billing, security and privacy
- .github/       CI/CD workflows

Stage 1 goal:
- fix the final target project structure
- add base documentation
- prepare skeletons for future implementation
