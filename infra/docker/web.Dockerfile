FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/marketing/package.json apps/marketing/package.json
COPY apps/web/package.json apps/web/package.json
COPY apps/api/package.json apps/api/package.json

RUN npm install --include=optional --no-audit --no-fund
RUN ROLLUP_VERSION=$(node -p 'require("./node_modules/rollup/package.json").version') \
  && npm install --no-save --include=optional --no-audit --no-fund @rollup/rollup-linux-x64-musl@${ROLLUP_VERSION} \
  && node -e 'require("@rollup/rollup-linux-x64-musl"); console.log("ROLLUP_NATIVE_MUSL_OK")'

COPY . .

ARG PUBLIC_VATRANSCRIBE_MARKETING_URL=http://localhost:8080
ARG PUBLIC_VATRANSCRIBE_APP_URL=http://localhost:8080
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_BASE_PATH=/app/
ARG VITE_SENTRY_DSN=
ARG VITE_SENTRY_ENVIRONMENT=production
ARG VITE_SENTRY_RELEASE=
ARG VITE_SENTRY_TRACES_SAMPLE_RATE=0

ENV PUBLIC_VATRANSCRIBE_MARKETING_URL=${PUBLIC_VATRANSCRIBE_MARKETING_URL}
ENV PUBLIC_VATRANSCRIBE_APP_URL=${PUBLIC_VATRANSCRIBE_APP_URL}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_BASE_PATH=${VITE_BASE_PATH}
ENV VITE_SENTRY_DSN=${VITE_SENTRY_DSN}
ENV VITE_SENTRY_ENVIRONMENT=${VITE_SENTRY_ENVIRONMENT}
ENV VITE_SENTRY_RELEASE=${VITE_SENTRY_RELEASE}
ENV VITE_SENTRY_TRACES_SAMPLE_RATE=${VITE_SENTRY_TRACES_SAMPLE_RATE}

RUN npm run build:marketing
RUN npm run build:web

FROM nginx:1.27-alpine AS runtime

RUN sed -i '/^user  nginx;/d' /etc/nginx/nginx.conf \
    && mkdir -p /etc/nginx/conf.d /var/cache/nginx /run \
    && chown -R nginx:nginx /etc/nginx/conf.d /var/cache/nginx /run

COPY --chown=nginx:nginx infra/docker/nginx.conf /etc/nginx/conf.d/default.conf

# Immutable deployment configuration shipped with the exact web image.
RUN mkdir -p \
    /opt/vatranscribe/web-release/infra/compose \
    /opt/vatranscribe/web-release/infra/docker \
    /opt/vatranscribe/web-release/infra/deploy

COPY infra/compose/docker-compose.prod.yml \
    /opt/vatranscribe/web-release/infra/compose/docker-compose.prod.yml

COPY infra/compose/docker-compose.registry.yml \
    /opt/vatranscribe/web-release/infra/compose/docker-compose.registry.yml

COPY infra/docker/nginx.prod.conf.template \
    /opt/vatranscribe/web-release/infra/docker/nginx.prod.conf.template

COPY infra/deploy/sync-nginx-certificates.sh \
    /opt/vatranscribe/web-release/infra/deploy/sync-nginx-certificates.sh

RUN chmod 0444 \
      /opt/vatranscribe/web-release/infra/compose/docker-compose.prod.yml \
      /opt/vatranscribe/web-release/infra/compose/docker-compose.registry.yml \
      /opt/vatranscribe/web-release/infra/docker/nginx.prod.conf.template \
    && chmod 0555 \
      /opt/vatranscribe/web-release/infra/deploy/sync-nginx-certificates.sh

COPY --from=build --chown=nginx:nginx /app/apps/marketing/dist /usr/share/nginx/html/marketing
COPY --from=build --chown=nginx:nginx /app/apps/web/dist /usr/share/nginx/html/web

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1

USER 101:101

CMD ["nginx", "-g", "daemon off;"]