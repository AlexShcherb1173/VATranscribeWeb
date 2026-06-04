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

ENV PUBLIC_VATRANSCRIBE_MARKETING_URL=${PUBLIC_VATRANSCRIBE_MARKETING_URL}
ENV PUBLIC_VATRANSCRIBE_APP_URL=${PUBLIC_VATRANSCRIBE_APP_URL}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_BASE_PATH=${VITE_BASE_PATH}

RUN npm run build:marketing
RUN npm run build:web

FROM nginx:1.27-alpine AS runtime

COPY infra/docker/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/apps/marketing/dist /usr/share/nginx/html/marketing
COPY --from=build /app/apps/web/dist /usr/share/nginx/html/web

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]