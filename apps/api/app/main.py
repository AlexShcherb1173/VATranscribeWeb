from __future__ import annotations

DEFAULT_REQUEST_ID_HEADER = "X-Request-ID"

from contextlib import asynccontextmanager
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.config import get_settings
from apps.api.app.observability import configure_logging, init_sentry
from apps.api.app.routers import router as api_router
from apps.api.app.security_foundation.rate_limits import build_rate_limit_key, rate_limiter
from apps.api.app.schemas import ApiInfoResponse

settings = get_settings()
configure_logging(settings)
init_sentry(settings)
request_logger = logging.getLogger("apps.api.request")


def ensure_storage_dirs() -> None:
    for path in settings.storage_dirs:
        path.mkdir(parents=True, exist_ok=True)


ensure_storage_dirs()


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_storage_dirs()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)




@app.middleware("http")
async def request_id_and_access_log_middleware(request: Request, call_next):
    request_id = request.headers.get(settings.request_id_header) or uuid4().hex
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        request_logger.exception(
            "request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers[settings.request_id_header] = request_id
    request_logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

@app.middleware("http")
async def api_rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    is_api_path = path.startswith(settings.api_prefix)
    is_health_path = path.startswith(f"{settings.api_prefix}/health/")

    if is_api_path and not is_health_path:
        rate_limiter.check(
            key=build_rate_limit_key("api:general", request),
            limit=settings.rate_limit_general_api_per_minute,
            window_seconds=60,
        )

    return await call_next(request)


app.include_router(api_router, prefix=settings.api_prefix)


@app.get('/', response_model=ApiInfoResponse, tags=['meta'])
def root() -> ApiInfoResponse:
    return ApiInfoResponse(
        app=settings.app_name,
        env=settings.app_env,
        version='0.1.0',
        docs_url=settings.docs_url,
        api_prefix=settings.api_prefix,
        endpoints={
            'health_live': f'{settings.api_prefix}/health/live',
            'health_ready': f'{settings.api_prefix}/health/ready',
            'auth_register': f'{settings.api_prefix}/auth/register',
            'auth_login': f'{settings.api_prefix}/auth/login',
            'auth_me': f'{settings.api_prefix}/auth/me',
            'profile': f'{settings.api_prefix}/profile',
            'quota': f'{settings.api_prefix}/quota/me',
            'billing_overview': f'{settings.api_prefix}/billing/overview',
            'billing_upgrade': f'{settings.api_prefix}/billing/upgrade',
            'jobs_list': f'{settings.api_prefix}/jobs',
            'jobs_get': f'{settings.api_prefix}/jobs/{{job_id}}',
            'jobs_create': f'{settings.api_prefix}/jobs',
            'jobs_logs': f'{settings.api_prefix}/jobs/{{job_id}}/logs',
            'jobs_enqueue': f'{settings.api_prefix}/jobs/{{job_id}}/enqueue',
            'jobs_retry': f'{settings.api_prefix}/jobs/{{job_id}}/retry',
            'jobs_cancel': f'{settings.api_prefix}/jobs/{{job_id}}/cancel',
            'downloads_analyze': f'{settings.api_prefix}/downloads/analyze',
            'downloads_jobs': f'{settings.api_prefix}/downloads/jobs',
            'uploads': f'{settings.api_prefix}/uploads',
            'media_assets_list': f'{settings.api_prefix}/media-assets',
            'media_asset_get': f'{settings.api_prefix}/media-assets/{{media_asset_id}}',
            'media_asset_download': f'{settings.api_prefix}/media-assets/{{media_asset_id}}/download',
            'media_asset_delete': f'{settings.api_prefix}/media-assets/{{media_asset_id}}',
            'transcriptions_jobs': f'{settings.api_prefix}/transcriptions/jobs',
            'transcripts_list': f'{settings.api_prefix}/transcripts',
            'transcript_get': f'{settings.api_prefix}/transcripts/{{transcript_id}}',
            'transcript_delete': f'{settings.api_prefix}/transcripts/{{transcript_id}}',
            'export_artifact_get': f'{settings.api_prefix}/export-artifacts/{{artifact_id}}',
            'export_artifact_download': f'{settings.api_prefix}/export-artifacts/{{artifact_id}}/download',
            'export_artifact_delete': f'{settings.api_prefix}/export-artifacts/{{artifact_id}}',
            'consents': f'{settings.api_prefix}/consents/me',
            'legal_documents': f'{settings.api_prefix}/legal/documents',
            'privacy': f'{settings.api_prefix}/privacy/me',
            'security_ping': f'{settings.api_prefix}/security/ping-rate-limit',
        },
    )
