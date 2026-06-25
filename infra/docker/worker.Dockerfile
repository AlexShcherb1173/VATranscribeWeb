FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    DENO_INSTALL=/usr/local \
    XDG_CACHE_HOME=/app/storage/cache \
    TORCH_HOME=/app/storage/cache/torch

WORKDIR /app

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
        git \
        build-essential \
        libsndfile1 \
    && curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh \
    && ln -sf /usr/local/bin/deno /usr/bin/deno \
    && deno --version \
    && node --version \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY scripts/maintenance/requirements-worker-demucs.txt ./requirements-worker-demucs.txt
COPY apps ./apps
COPY packages ./packages
COPY alembic.ini ./
COPY alembic ./alembic

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --default-timeout=300 --retries 10 -e . \
    && pip install --default-timeout=300 --retries 10 --upgrade yt-dlp \
    && pip install --default-timeout=300 --retries 10 faster-whisper ctranslate2 onnxruntime \
    && pip install --default-timeout=300 --retries 10 --index-url https://download.pytorch.org/whl/cpu \
        torch==2.5.1+cpu \
        torchaudio==2.5.1+cpu \
    && pip install --default-timeout=300 --retries 10 -r requirements-worker-demucs.txt \
    && python -c "import torch, torchaudio, demucs; print('Demucs permanent build OK:', torch.__version__)"

COPY . .

RUN groupadd --system --gid 10001 appuser \
    && useradd --system --uid 10001 --gid appuser --home-dir /app --shell /usr/sbin/nologin appuser \
    && mkdir -p \
        /app/storage \
        /app/storage/cache \
        /app/storage/cache/torch \
        /app/storage/cookies \
        /app/storage/downloads \
        /app/storage/logs \
        /app/storage/temp \
        /app/storage/transcripts \
        /app/storage/uploads \
    && chown -R 10001:10001 /app/storage

USER 10001:10001

CMD ["celery", "-A", "apps.worker.app.worker:celery", "worker", "--loglevel=info", "--pool=solo", "--concurrency=1"]
