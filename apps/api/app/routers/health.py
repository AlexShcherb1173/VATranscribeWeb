from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.app.config import Settings, get_settings
from apps.api.app.database import get_db
from apps.api.app.schemas import (
    HealthLiveResponse,
    HealthReadyDependency,
    HealthReadyResponse,
)

router = APIRouter(prefix="/health")


def get_redis_client(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


@router.get(
    "/live",
    response_model=HealthLiveResponse,
    summary="Liveness probe",
)
def health_live(settings: Settings = Depends(get_settings)) -> HealthLiveResponse:
    return HealthLiveResponse(
        status="ok",
        app=settings.app_name,
        env=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=HealthReadyResponse,
    summary="Readiness probe",
)
def health_ready(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    checks: dict[str, HealthReadyDependency] = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = HealthReadyDependency(
            ok=True,
            detail="Database reachable",
        )
    except Exception as exc:
        checks["database"] = HealthReadyDependency(
            ok=False,
            detail=str(exc),
        )

    try:
        redis_client = get_redis_client(settings)
        redis_client.ping()
        checks["redis"] = HealthReadyDependency(
            ok=True,
            detail="Redis reachable",
        )
    except Exception as exc:
        checks["redis"] = HealthReadyDependency(
            ok=False,
            detail=str(exc),
        )

    try:
        for path in settings.storage_dirs:
            path.mkdir(parents=True, exist_ok=True)
        checks["storage"] = HealthReadyDependency(
            ok=True,
            detail="Storage directories ready",
        )
    except Exception as exc:
        checks["storage"] = HealthReadyDependency(
            ok=False,
            detail=str(exc),
        )

    overall_ok = all(item.ok for item in checks.values())

    response = HealthReadyResponse(
        status="ok" if overall_ok else "error",
        app=settings.app_name,
        env=settings.app_env,
        checks=checks,
    )

    if not overall_ok:
        return JSONResponse(
            status_code=503,
            content=response.model_dump(mode="json"),
        )

    return response