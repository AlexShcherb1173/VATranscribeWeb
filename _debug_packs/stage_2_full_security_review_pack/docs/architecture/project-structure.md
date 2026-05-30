# Project Structure

Target VATranscribeWeb monorepo structure.

apps/marketing - public landing, SEO, blog, docs and legal pages
apps/web - user SaaS application
apps/admin - internal admin panel
apps/api - FastAPI backend
apps/worker - Celery workers
apps/desktop - desktop app shell

packages/core - shared media processing core
packages/shared-types - shared TypeScript contracts
packages/sdk - future API SDK

infra - Docker, Nginx, compose, deploy and backup configuration
docs - architecture, security, privacy, billing and roadmap documentation
scripts - developer, migration, report and maintenance scripts
tests - API, worker, billing, security, privacy and integration tests
