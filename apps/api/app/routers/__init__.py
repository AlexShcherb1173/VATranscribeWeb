from __future__ import annotations

from fastapi import APIRouter

from apps.api.app.routers.auth import router as auth_router
from apps.api.app.routers.admin_security import router as admin_security_router
from apps.api.app.routers.billing import router as billing_router
from apps.api.app.routers.payment_webhooks import router as payment_webhooks_router
from apps.api.app.routers.plans import router as plans_router
from apps.api.app.routers.downloads import router as downloads_router
from apps.api.app.routers.youtube_cookies import router as youtube_cookies_router
from apps.api.app.routers.export_artifacts import router as export_artifacts_router
from apps.api.app.routers.health import router as health_router
from apps.api.app.routers.jobs import router as jobs_router
from apps.api.app.routers.media_assets import router as media_assets_router
from apps.api.app.routers.profile import router as profile_router
from apps.api.app.routers.quota import router as quota_router
from apps.api.app.routers.settings import router as settings_router
from apps.api.app.routers.transcriptions import router as transcriptions_router
from apps.api.app.routers.transcripts import router as transcripts_router
from apps.api.app.routers.uploads import router as uploads_router

# Stage 2 security/privacy foundation routers
from apps.api.app.routers.consents import router as consents_router
from apps.api.app.routers.legal import router as legal_router
from apps.api.app.routers.privacy import router as privacy_router
from apps.api.app.routers.security import router as security_router


router = APIRouter()

# Core transferred routers
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(admin_security_router)
router.include_router(profile_router)
router.include_router(quota_router)
router.include_router(billing_router)
router.include_router(payment_webhooks_router)
router.include_router(plans_router)
router.include_router(jobs_router)
router.include_router(downloads_router)
router.include_router(youtube_cookies_router)
router.include_router(uploads_router)
router.include_router(media_assets_router)
router.include_router(transcriptions_router)
router.include_router(transcripts_router)
router.include_router(export_artifacts_router)
router.include_router(settings_router)

# Stage 2 security/privacy foundation routers
router.include_router(consents_router)
router.include_router(legal_router)
router.include_router(privacy_router)
router.include_router(security_router)
