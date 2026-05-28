from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


# =============================================================================
# Runtime paths
# =============================================================================

PROJECT_ROOT = Path.cwd()

STORAGE_ROOT = Path(os.getenv("STORAGE_ROOT", "storage"))
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", STORAGE_ROOT / "uploads"))
DOWNLOADS_DIR = Path(os.getenv("DOWNLOADS_DIR", STORAGE_ROOT / "downloads"))
DOWNLOADS_AUDIO_DIR = Path(os.getenv("DOWNLOADS_AUDIO_DIR", STORAGE_ROOT / "downloads" / "audio"))
DOWNLOADS_VIDEO_DIR = Path(os.getenv("DOWNLOADS_VIDEO_DIR", STORAGE_ROOT / "downloads" / "video"))
TRANSCRIPTS_JSON_DIR = Path(os.getenv("TRANSCRIPTS_JSON_DIR", STORAGE_ROOT / "transcripts" / "json"))
TRANSCRIPTS_TXT_DIR = Path(os.getenv("TRANSCRIPTS_TXT_DIR", STORAGE_ROOT / "transcripts" / "txt"))
TRANSCRIPTS_SRT_DIR = Path(os.getenv("TRANSCRIPTS_SRT_DIR", STORAGE_ROOT / "transcripts" / "srt"))
TRANSCRIPTS_VTT_DIR = Path(os.getenv("TRANSCRIPTS_VTT_DIR", STORAGE_ROOT / "transcripts" / "vtt"))
LOGS_DIR = Path(os.getenv("LOGS_DIR", STORAGE_ROOT / "logs"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", STORAGE_ROOT / "temp"))
COOKIES_DIR = Path(os.getenv("COOKIES_DIR", STORAGE_ROOT / "cookies"))
CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", STORAGE_ROOT / "cache"))


def ensure_runtime_directories() -> None:
    """
    Create runtime directories required by API/worker.

    Important:
    FastAPI/Starlette StaticFiles raises RuntimeError if mounted directory
    does not exist. Therefore STORAGE_ROOT must exist before app.mount().
    """

    directories = [
        STORAGE_ROOT,
        UPLOADS_DIR,
        DOWNLOADS_DIR,
        DOWNLOADS_AUDIO_DIR,
        DOWNLOADS_VIDEO_DIR,
        TRANSCRIPTS_JSON_DIR,
        TRANSCRIPTS_TXT_DIR,
        TRANSCRIPTS_SRT_DIR,
        TRANSCRIPTS_VTT_DIR,
        LOGS_DIR,
        TEMP_DIR,
        COOKIES_DIR,
        CACHE_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


ensure_runtime_directories()


# =============================================================================
# App config
# =============================================================================

APP_NAME = os.getenv("APP_NAME", "VATranscribe")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}
API_PREFIX = os.getenv("API_PREFIX", "/api/v1").rstrip("/")

CORS_ORIGINS_RAW = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:5174,http://127.0.0.1:5174,"
    "http://localhost:5175,http://127.0.0.1:5175,"
    "http://localhost:4321,http://127.0.0.1:4321",
)


def parse_csv_env(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


CORS_ORIGINS = parse_csv_env(CORS_ORIGINS_RAW)


app = FastAPI(
    title=APP_NAME,
    version="0.1.0",
    debug=DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)


# =============================================================================
# Middleware
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Static files
# =============================================================================

app.mount(
    "/storage",
    StaticFiles(directory=str(STORAGE_ROOT)),
    name="storage",
)


# =============================================================================
# Health endpoints
# =============================================================================

@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": APP_NAME,
        "env": APP_ENV,
        "status": "ok",
        "docs": "/docs",
    }


@app.get(f"{API_PREFIX}/health/live")
def health_live() -> dict[str, str]:
    return {
        "status": "live",
    }


@app.get(f"{API_PREFIX}/health/ready")
def health_ready() -> dict[str, str]:
    return {
        "status": "ready",
    }


# =============================================================================
# Router loading
# =============================================================================

ROUTER_MODULES: tuple[str, ...] = (
    "apps.api.app.routers.auth",
    "apps.api.app.routers.profile",
    "apps.api.app.routers.settings",
    "apps.api.app.routers.plans",
    "apps.api.app.routers.billing",
    "apps.api.app.routers.quota",
    "apps.api.app.routers.downloads",
    "apps.api.app.routers.uploads",
    "apps.api.app.routers.files",
    "apps.api.app.routers.media_assets",
    "apps.api.app.routers.jobs",
    "apps.api.app.routers.transcriptions",
    "apps.api.app.routers.transcripts",
    "apps.api.app.routers.exports",
)


def include_router_from_module(module_path: str) -> None:
    """
    Import module and include its `router` object if present.

    Expected router convention:
        router = APIRouter(...)

    The project uses /api/v1 prefix from API_PREFIX.
    Routers themselves should normally define local prefixes:
        APIRouter(prefix="/jobs", tags=["jobs"])
    """

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        logger.warning("Router module not found: %s. Error: %s", module_path, exc)
        return

    router = getattr(module, "router", None)

    if router is None:
        logger.warning("Router module has no `router`: %s", module_path)
        return

    if not isinstance(router, APIRouter):
        logger.warning("Object `router` is not APIRouter in module: %s", module_path)
        return

    app.include_router(router, prefix=API_PREFIX)
    logger.info("Included router: %s", module_path)


def include_project_routers(router_modules: Iterable[str]) -> None:
    for module_path in router_modules:
        include_router_from_module(module_path)


include_project_routers(ROUTER_MODULES)


# =============================================================================
# Startup / shutdown
# =============================================================================

@app.on_event("startup")
async def on_startup() -> None:
    ensure_runtime_directories()
    logger.info("%s started in %s mode", APP_NAME, APP_ENV)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("%s shutdown complete", APP_NAME)