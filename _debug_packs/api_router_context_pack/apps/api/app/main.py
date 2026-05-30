from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apps.api.app.config import get_settings
from apps.api.app.routers import router as api_router
from apps.api.app.schemas import ApiInfoResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    for path in settings.storage_dirs:
        path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")


@app.get("/", response_model=ApiInfoResponse, tags=["meta"])
def root() -> ApiInfoResponse:
    return ApiInfoResponse(
        app=settings.app_name,
        env=settings.app_env,
        version="0.1.0",
        docs_url="/docs",
        api_prefix=settings.api_prefix,
        endpoints={
            "health_live": f"{settings.api_prefix}/health/live",
            "health_ready": f"{settings.api_prefix}/health/ready",
            "auth_register": f"{settings.api_prefix}/auth/register",
            "auth_login": f"{settings.api_prefix}/auth/login",
            "auth_me": f"{settings.api_prefix}/auth/me",
            "profile": f"{settings.api_prefix}/profile",
            "quota": f"{settings.api_prefix}/quota/me",
            "billing_overview": f"{settings.api_prefix}/billing/overview",
            "billing_upgrade": f"{settings.api_prefix}/billing/upgrade",
            "jobs_list": f"{settings.api_prefix}/jobs",
            "jobs_get": f"{settings.api_prefix}/jobs/{{job_id}}",
            "jobs_create": f"{settings.api_prefix}/jobs",
            "jobs_logs": f"{settings.api_prefix}/jobs/{{job_id}}/logs",
            "jobs_enqueue": f"{settings.api_prefix}/jobs/{{job_id}}/enqueue",
            "jobs_retry": f"{settings.api_prefix}/jobs/{{job_id}}/retry",
            "jobs_cancel": f"{settings.api_prefix}/jobs/{{job_id}}/cancel",
            "downloads_analyze": f"{settings.api_prefix}/downloads/analyze",
            "downloads_jobs": f"{settings.api_prefix}/downloads/jobs",
            "uploads": f"{settings.api_prefix}/uploads",
            "media_assets_list": f"{settings.api_prefix}/media-assets",
            "media_asset_get": f"{settings.api_prefix}/media-assets/{{media_asset_id}}",
            "media_asset_download": f"{settings.api_prefix}/media-assets/{{media_asset_id}}/download",
            "media_asset_delete": f"{settings.api_prefix}/media-assets/{{media_asset_id}}",
            "transcriptions_jobs": f"{settings.api_prefix}/transcriptions/jobs",
            "transcripts_list": f"{settings.api_prefix}/transcripts",
            "transcript_get": f"{settings.api_prefix}/transcripts/{{transcript_id}}",
            "transcript_delete": f"{settings.api_prefix}/transcripts/{{transcript_id}}",
            "export_artifact_get": f"{settings.api_prefix}/export-artifacts/{{artifact_id}}",
            "export_artifact_download": f"{settings.api_prefix}/export-artifacts/{{artifact_id}}/download",
            "export_artifact_delete": f"{settings.api_prefix}/export-artifacts/{{artifact_id}}",
            "storage_static": "/storage/...",
        },
    )