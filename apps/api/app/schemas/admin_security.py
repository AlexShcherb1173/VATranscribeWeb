from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
