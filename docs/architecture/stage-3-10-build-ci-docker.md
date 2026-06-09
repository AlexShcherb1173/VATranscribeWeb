Stage 3.10 Architecture Note

Stage 3.10 introduces a production-like frontend delivery model.

Components
infra/docker/web.Dockerfile
infra/docker/nginx.conf
infra/compose/docker-compose.prod.yml
Build model

The web image builds both frontend applications:

Astro marketing app
React/Vite SaaS web app

The final runtime image is Nginx.

Why React uses /app/ base

The React app is mounted under /app/ in Nginx. Vite receives:

VITE_BASE_PATH=/app/

This avoids conflicts between Astro assets and React assets.

API model

The React app uses:

VITE_API_BASE_URL=/api/v1

Nginx proxies /api/* to the FastAPI container.

Status

This is deploy-ready structure, not full production readiness.
