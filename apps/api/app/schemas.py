from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field



class LegalDocumentAcceptanceRequest(BaseModel):
    document_type: str = Field(min_length=2, max_length=100)
    document_version: str = Field(min_length=1, max_length=50)
    accepted: bool = True


class LegalDocumentRead(BaseModel):
    id: str
    document_type: str
    version: str
    title: str
    content: str
    is_active: bool
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserConsentRead(BaseModel):
    id: str
    user_id: str
    document_type: str
    document_version: str
    accepted: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ConsentAcceptCurrentResponse(BaseModel):
    items: list[UserConsentRead] = Field(default_factory=list)



class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(pattern="^(export|delete_account|delete_files|revoke_consent)$")
    comment: str | None = Field(default=None, max_length=2000)


class PrivacyRequestRead(BaseModel):
    id: str
    user_id: str
    request_type: str
    status: str
    comment: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PrivacyOverviewResponse(BaseModel):
    status: str = "ok"
    requests: list[PrivacyRequestRead] = Field(default_factory=list)

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    accepted_legal_documents: list[LegalDocumentAcceptanceRequest] = Field(default_factory=list)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class YouTubeCookiesStatusResponse(BaseModel):
    configured: bool
    source_filename: str | None = None
    cookie_format: str | None = None
    size_bytes: int | None = None
    updated_at: datetime | None = None



class LogoutResponse(BaseModel):
    ok: bool
    detail: str


class UserRead(BaseModel):
    id: str
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class ApiInfoResponse(BaseModel):
    app: str
    env: str
    version: str
    docs_url: str | None = None
    api_prefix: str
    endpoints: dict[str, str]


class HealthReadyDependency(BaseModel):
    ok: bool
    detail: str


class HealthLiveResponse(BaseModel):
    status: str = "ok"
    app: str
    env: str


class HealthReadyResponse(BaseModel):
    status: str
    app: str
    env: str
    checks: dict[str, HealthReadyDependency] = Field(default_factory=dict)


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=500)


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str | None = None
    avatar_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserQuotaResponse(BaseModel):
    id: str
    user_id: str
    storage_bytes_used: int
    transcription_seconds_used: int
    jobs_count_used: int
    storage_bytes_limit: int
    transcription_seconds_limit: int
    jobs_count_limit: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BillingPlanResponse(BaseModel):
    id: str
    code: str
    name: str
    price_monthly: int
    currency: str
    storage_bytes_limit: int
    transcription_seconds_limit: int
    jobs_count_limit: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class BillingSubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    status: str
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool

    model_config = ConfigDict(from_attributes=True)


class UsageHistoryPointResponse(BaseModel):
    label: str
    storage_bytes_used: int
    transcription_seconds_used: int
    jobs_count_used: int


class BillingOverviewResponse(BaseModel):
    current_plan: BillingPlanResponse
    available_plans: list[BillingPlanResponse] = Field(default_factory=list)
    subscription: BillingSubscriptionResponse
    quota: UserQuotaResponse
    usage_history: list[UsageHistoryPointResponse] = Field(default_factory=list)


class BillingUpgradeRequest(BaseModel):
    plan_code: str
    billing_period: str = "monthly"


class BillingUpgradeResponse(BaseModel):
    current_plan: BillingPlanResponse
    subscription: BillingSubscriptionResponse
    quota: UserQuotaResponse


class MediaAssetResponse(BaseModel):
    id: str
    kind: str
    original_name: str
    stored_name: str
    mime_type: str | None = None
    extension: str | None = None
    size_bytes: int
    duration_sec: int | None = None
    checksum_sha256: str | None = None
    created_at: datetime | None = None
    download_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DownloadAnalyzeRequest(BaseModel):
    url: str


class DownloadAnalyzeResponse(BaseModel):
    url: str
    platform: str | None = None
    title: str | None = None
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
    available_formats: list[dict[str, Any]] = Field(default_factory=list)
    extract_audio: bool = False


class DownloadJobCreateRequest(BaseModel):
    url: str
    download_mode: str = "video_mp4_compatible"
    requested_format: str
    requested_file_name: str
    mp4_mode: str = "compatible"
    selected_format_id: str | None = None
    selected_video_format_id: str | None = None
    selected_audio_format_id: str | None = None


class JobCreateRequest(BaseModel):
    type: str
    source_type: str | None = None
    title: str | None = None
    input_url: str | None = None
    requested_format: str | None = None
    requested_file_name: str | None = None
    mp4_mode: str | None = None
    selected_video_format_id: str | None = None
    selected_audio_format_id: str | None = None
    selected_format_id: str | None = None
    transcription_media_asset_id: str | None = None
    transcription_model: str | None = None
    transcription_language: str | None = None
    download_audio: bool = False
    download_video: bool = False


class JobResponse(BaseModel):
    id: str
    user_id: str | None = None
    type: str
    status: str
    source_type: str | None = None
    output_media_asset_id: str | None = None
    output_media_asset: MediaAssetResponse | None = None
    transcription_media_asset: MediaAssetResponse | None = None
    title: str | None = None
    input_url: str | None = None
    requested_format: str | None = None
    requested_file_name: str | None = None
    mp4_mode: str | None = None
    selected_video_format_id: str | None = None
    selected_audio_format_id: str | None = None
    transcription_media_asset_id: str | None = None
    transcription_model: str | None = None
    transcription_language: str | None = None
    download_audio: bool = False
    download_video: bool = False
    error_message: str | None = None
    progress_percent: int = 0
    progress_stage: str | None = None
    progress_message: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class JobActionResponse(BaseModel):
    ok: bool
    job_id: str
    status: str
    detail: str


class JobLogResponse(BaseModel):
    id: str
    job_id: str
    level: str
    message: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TranscriptionJobCreateRequest(BaseModel):
    media_asset_id: str
    model_name: str | None = "medium"
    language: str | None = None


class TranscriptSegmentResponse(BaseModel):
    id: str
    transcript_id: str
    start_sec: int
    end_sec: int
    text: str
    speaker_label: str | None = None
    confidence: str | None = None
    order_index: int

    model_config = ConfigDict(from_attributes=True)


class ExportArtifactResponse(BaseModel):
    id: str
    transcript_id: str
    format: str
    size_bytes: int
    created_at: datetime | None = None
    download_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TranscriptResponse(BaseModel):
    id: str
    job_id: str
    media_asset_id: str
    language: str
    model_name: str
    engine: str
    full_text: str
    created_at: datetime | None = None
    segments: list[TranscriptSegmentResponse] = Field(default_factory=list)
    exports: list[ExportArtifactResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# P2-02 Admin 2FA schemas
class AdminTwoFactorStatusResponse(BaseModel):
    enabled: bool
    confirmed_at: datetime | None = None
    recovery_codes_remaining: int = 0


class AdminTwoFactorSetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class AdminTwoFactorVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class AdminTwoFactorDisableRequest(BaseModel):
    code: str | None = Field(default=None, min_length=6, max_length=32)
    recovery_code: str | None = Field(default=None, min_length=8, max_length=128)


class AdminTwoFactorConfirmResponse(BaseModel):
    enabled: bool
    recovery_codes: list[str] = Field(default_factory=list)


class AdminTwoFactorRecoveryCodesResponse(BaseModel):
    recovery_codes: list[str] = Field(default_factory=list)


class AdminSecurityCheckResponse(BaseModel):
    status: str = "ok"
    admin_2fa: str = "enabled"

