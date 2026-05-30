from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlanSpec:
    id: str
    code: str
    name: str
    price_monthly: int
    currency: str
    storage_bytes_limit: int
    transcription_seconds_limit: int
    jobs_count_limit: int
    is_active: bool = True


FREE_PLAN_ID = "00000000-0000-0000-0000-000000000001"
PRO_PLAN_ID = "00000000-0000-0000-0000-000000000002"
BUSINESS_PLAN_ID = "00000000-0000-0000-0000-000000000003"


PLAN_CATALOG: dict[str, PlanSpec] = {
    "free": PlanSpec(
        id=FREE_PLAN_ID,
        code="free",
        name="Free",
        price_monthly=0,
        currency="USD",
        storage_bytes_limit=10 * 1024 * 1024 * 1024,   # 10 GB
        transcription_seconds_limit=36_000,            # 10 hours
        jobs_count_limit=500,
    ),
    "pro": PlanSpec(
        id=PRO_PLAN_ID,
        code="pro",
        name="Pro",
        price_monthly=12,
        currency="USD",
        storage_bytes_limit=100 * 1024 * 1024 * 1024,  # 100 GB
        transcription_seconds_limit=144_000,           # 40 hours
        jobs_count_limit=5_000,
    ),
    "business": PlanSpec(
        id=BUSINESS_PLAN_ID,
        code="business",
        name="Business",
        price_monthly=49,
        currency="USD",
        storage_bytes_limit=500 * 1024 * 1024 * 1024,  # 500 GB
        transcription_seconds_limit=720_000,           # 200 hours
        jobs_count_limit=20_000,
    ),
}


def get_plan_spec_or_raise(plan_code: str) -> PlanSpec:
    plan = PLAN_CATALOG.get(plan_code)
    if plan is None:
        raise ValueError(f"Unknown plan_code: {plan_code}")
    return plan