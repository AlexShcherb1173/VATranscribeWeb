from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from apps.api.app.models import Plan, Subscription, UsageSnapshot, User, UserQuota
from apps.api.app.services.account_bootstrap import ensure_user_quota
from apps.api.app.services.plan_catalog import PLAN_CATALOG, get_plan_spec_or_raise


def _normalize_billing_period_days(billing_period: str) -> int:
    normalized = (billing_period or "monthly").strip().lower()
    if normalized == "yearly":
        return 365
    return 30


def ensure_catalog_plans(db: Session) -> list[Plan]:
    """
    Синхронизирует таблицу plans с кодовым catalog.
    Работает как защитный слой, даже если seed-миграция ещё не выполнена.
    """
    existing = {
        plan.code: plan
        for plan in db.scalars(select(Plan)).all()
    }

    changed = False

    for spec in PLAN_CATALOG.values():
        plan = existing.get(spec.code)
        if plan is None:
            db.add(
                Plan(
                    id=spec.id,
                    code=spec.code,
                    name=spec.name,
                    price_monthly=spec.price_monthly,
                    currency=spec.currency,
                    storage_bytes_limit=spec.storage_bytes_limit,
                    transcription_seconds_limit=spec.transcription_seconds_limit,
                    jobs_count_limit=spec.jobs_count_limit,
                    is_active=spec.is_active,
                )
            )
            changed = True
            continue

        if (
            plan.name != spec.name
            or plan.price_monthly != spec.price_monthly
            or plan.currency != spec.currency
            or plan.storage_bytes_limit != spec.storage_bytes_limit
            or plan.transcription_seconds_limit != spec.transcription_seconds_limit
            or plan.jobs_count_limit != spec.jobs_count_limit
            or plan.is_active != spec.is_active
        ):
            plan.name = spec.name
            plan.price_monthly = spec.price_monthly
            plan.currency = spec.currency
            plan.storage_bytes_limit = spec.storage_bytes_limit
            plan.transcription_seconds_limit = spec.transcription_seconds_limit
            plan.jobs_count_limit = spec.jobs_count_limit
            plan.is_active = spec.is_active
            db.add(plan)
            changed = True

    if changed:
        db.commit()

    return list(
        db.scalars(
            select(Plan)
            .where(Plan.is_active.is_(True))
            .order_by(Plan.price_monthly.asc(), Plan.created_at.asc())
        ).all()
    )


def get_available_plans(db: Session) -> list[Plan]:
    ensure_catalog_plans(db)
    return list(
        db.scalars(
            select(Plan)
            .where(Plan.is_active.is_(True))
            .order_by(Plan.price_monthly.asc(), Plan.created_at.asc())
        ).all()
    )


def get_plan_by_code(db: Session, plan_code: str) -> Plan:
    """
    Возвращает активный план по code.
    """
    get_plan_spec_or_raise(plan_code)
    ensure_catalog_plans(db)

    plan = db.scalar(
        select(Plan).where(Plan.code == plan_code, Plan.is_active.is_(True))
    )
    if plan is None:
        raise ValueError(f"Plan not found for code={plan_code}")
    return plan


def get_active_subscription(db: Session, user_id: str) -> Subscription | None:
    return db.scalar(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(
            Subscription.user_id == str(user_id),
            Subscription.status == "active",
        )
        .order_by(Subscription.created_at.desc())
    )


def sync_quota_limits_from_plan(db: Session, user: User, plan: Plan) -> UserQuota:
    """
    Синхронизирует только limit-поля из плана в user_quotas.
    Used-поля не трогаем.
    """
    quota = ensure_user_quota(db, user)

    changed = False

    if quota.storage_bytes_limit != plan.storage_bytes_limit:
        quota.storage_bytes_limit = plan.storage_bytes_limit
        changed = True

    if quota.transcription_seconds_limit != plan.transcription_seconds_limit:
        quota.transcription_seconds_limit = plan.transcription_seconds_limit
        changed = True

    if quota.jobs_count_limit != plan.jobs_count_limit:
        quota.jobs_count_limit = plan.jobs_count_limit
        changed = True

    if changed:
        db.add(quota)
        db.commit()
        db.refresh(quota)

    return quota


def ensure_default_subscription(db: Session, user: User) -> tuple[Plan, Subscription, UserQuota]:
    """
    Гарантирует, что у пользователя есть активная подписка.
    Если её нет, создаёт free subscription.
    """
    current = get_active_subscription(db, user.id)
    if current is not None:
        plan = current.plan or db.get(Plan, current.plan_id)
        if plan is None:
            plan = get_plan_by_code(db, "free")
        quota = sync_quota_limits_from_plan(db, user, plan)
        return plan, current, quota

    free_plan = get_plan_by_code(db, "free")
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        id=str(uuid.uuid4()),
        user_id=str(user.id),
        plan_id=free_plan.id,
        status="active",
        started_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    quota = sync_quota_limits_from_plan(db, user, free_plan)
    return free_plan, subscription, quota


def build_usage_history(db: Session, user: User, limit: int = 14) -> list[dict]:
    """
    Возвращает chart-friendly usage history.
    Берём snapshots, агрегируем по label и оставляем последнее состояние на label.
    """
    snapshots = list(
        db.scalars(
            select(UsageSnapshot)
            .where(UsageSnapshot.user_id == str(user.id))
            .order_by(UsageSnapshot.created_at.asc())
        ).all()
    )

    if not snapshots:
        quota = ensure_user_quota(db, user)
        today_label = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return [
            {
                "label": today_label,
                "storage_bytes_used": quota.storage_bytes_used,
                "transcription_seconds_used": quota.transcription_seconds_used,
                "jobs_count_used": quota.jobs_count_used,
            }
        ]

    by_label: dict[str, UsageSnapshot] = {}
    for snapshot in snapshots:
        by_label[snapshot.label] = snapshot

    points = [
        {
            "label": label,
            "storage_bytes_used": snap.storage_bytes_used,
            "transcription_seconds_used": snap.transcription_seconds_used,
            "jobs_count_used": snap.jobs_count_used,
        }
        for label, snap in sorted(by_label.items(), key=lambda item: item[0])
    ]

    return points[-limit:]


def get_billing_overview(db: Session, user: User) -> dict:
    current_plan, subscription, quota = ensure_default_subscription(db, user)
    available_plans = get_available_plans(db)
    usage_history = build_usage_history(db, user)

    return {
        "current_plan": current_plan,
        "available_plans": available_plans,
        "subscription": subscription,
        "quota": quota,
        "usage_history": usage_history,
    }


def upgrade_user_plan(
    db: Session,
    user: User,
    plan_code: str,
    billing_period: str = "monthly",
) -> tuple[Plan, Subscription, UserQuota]:
    """
    Fake billing upgrade:
    - валидирует target plan
    - отменяет текущую active subscription
    - создаёт новую active subscription
    - синкает plan limits -> user_quotas
    """
    target_plan = get_plan_by_code(db, plan_code)
    current_subscription = get_active_subscription(db, user.id)

    if current_subscription is not None and current_subscription.plan_id == target_plan.id:
        quota = sync_quota_limits_from_plan(db, user, target_plan)
        return target_plan, current_subscription, quota

    now = datetime.now(timezone.utc)
    period_days = _normalize_billing_period_days(billing_period)

    if current_subscription is not None:
        current_subscription.status = "canceled"
        db.add(current_subscription)

    new_subscription = Subscription(
        id=str(uuid.uuid4()),
        user_id=str(user.id),
        plan_id=target_plan.id,
        status="active",
        started_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=period_days),
        cancel_at_period_end=False,
    )
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)

    quota = sync_quota_limits_from_plan(db, user, target_plan)
    return target_plan, new_subscription, quota