FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    XDG_CACHE_HOME=/app/storage/cache

WORKDIR /app

ARG DENO_VERSION=2.9.4
ARG DENO_SHA256=c24f955d9fbfe0ea5ae2b501c8e71ae76e31e4c9782390a54a284b3364fda725

RUN printf '%s\n' \
    'Types: deb' \
    'URIs: https://deb.debian.org/debian' \
    'Suites: bookworm bookworm-updates' \
    'Components: main' \
    'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
    '' \
    'Types: deb' \
    'URIs: https://security.debian.org/debian-security' \
    'Suites: bookworm-security' \
    'Components: main' \
    'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
    > /etc/apt/sources.list.d/debian.sources \
    && apt-get update -o Acquire::Retries=10 \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        ca-certificates \
        unzip \
        nodejs \
    && curl --fail --location --silent --show-error --http1.1 \
        --connect-timeout 20 --max-time 300 \
        --retry 5 --retry-delay 2 --retry-all-errors \
        --output /tmp/deno.zip \
        "https://github.com/denoland/deno/releases/download/v${DENO_VERSION}/deno-x86_64-unknown-linux-gnu.zip" \
    && echo "${DENO_SHA256}  /tmp/deno.zip" | sha256sum -c - \
    && unzip -q /tmp/deno.zip -d /usr/local/bin \
    && chmod 0755 /usr/local/bin/deno \
    && rm -f /tmp/deno.zip \
    && test "$(deno --version | head -n 1 | cut -d ' ' -f 2)" = "${DENO_VERSION}" \
    && deno --version \
    && node --version \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY alembic.ini ./
COPY alembic ./alembic

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --default-timeout=300 --retries 10 -e . \
    && pip install --default-timeout=300 --retries 10 --upgrade yt-dlp

COPY . .

RUN groupadd --system --gid 10001 appuser \
    && useradd --system --uid 10001 --gid appuser --home-dir /app --shell /usr/sbin/nologin appuser \
    && mkdir -p \
        /app/storage \
        /app/storage/cache \
        /app/storage/cookies \
        /app/storage/downloads \
        /app/storage/logs \
        /app/storage/temp \
        /app/storage/transcripts \
        /app/storage/uploads \
    && chown -R 10001:10001 /app/storage

EXPOSE 8000

USER 10001:10001

CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
