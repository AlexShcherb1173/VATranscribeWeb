from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_config_declares_billing_production_gate_settings():
    text = read("apps/api/app/config.py")
    assert "ALLOWED_PAYMENT_PROVIDERS" in text
    assert "PAYMENT_PROVIDER" in text
    assert "PAYMENT_WEBHOOK_SECRET" in text
    assert "PAYMENT_API_KEY" in text
    assert "PAYMENT_WEBHOOK_SIGNATURE_HEADER" in text
    assert "BILLING_FAKE_UPGRADE_ENABLED" in text
    assert "BILLING_PAID_PLANS_ENABLED" in text
    assert "BILLING_FAKE_UPGRADE_ENABLED must be false in production" in text
    assert "BILLING_PAID_PLANS_ENABLED cannot be true when PAYMENT_PROVIDER=disabled" in text


def test_billing_upgrade_blocks_paid_activation_without_fake_gate():
    text = read("apps/api/app/services/billing_service.py")
    assert "BillingUpgradeForbidden" in text
    assert "Paid plan activation requires a verified payment webhook" in text
    assert "allow_fake_upgrade" in text
    assert "activate_paid_subscription_from_verified_payment" in text
    assert "Production paid-plan activation must go through a verified payment webhook" in text


def test_billing_router_uses_settings_gate_and_audit_event():
    text = read("apps/api/app/routers/billing.py")
    assert "settings.fake_billing_upgrade_allowed" in text
    assert "BillingUpgradeForbidden" in text
    assert "billing.upgrade_blocked" in text
    assert "HTTP_403_FORBIDDEN" in text


def test_payment_webhook_router_and_service_exist():
    router = read("apps/api/app/routers/payment_webhooks.py")
    service = read("apps/api/app/services/payment_event_service.py")
    init = read("apps/api/app/routers/__init__.py")
    assert 'APIRouter(prefix="/payment-webhooks"' in router
    assert "process_payment_webhook" in router
    assert "payment.webhook_processed" in router
    assert "payment.webhook_rejected" in router
    assert "compute_webhook_signature" in service
    assert "verify_webhook_signature" in service
    assert "record_payment_event_once" in service
    assert "provider_event_key" in service
    assert "activate_paid_subscription_from_verified_payment" in service
    assert "payment_webhooks_router" in init


def test_payment_event_model_and_migration_exist():
    models = read("apps/api/app/models.py")
    migration = read("alembic/versions/20260610_0003_payment_events.py")
    assert "class PaymentEvent" in models
    assert "provider_event_key" in models
    assert "payment_events" in migration
    assert 'UniqueConstraint("provider_event_key")' in migration
    assert "down_revision" in migration and "20260610_0002" in migration


def test_env_and_deploy_secret_validation_include_billing_gate():
    for path in (".env.example", ".env.production.example"):
        text = read(path)
        assert "PAYMENT_PROVIDER=disabled" in text
        assert "PAYMENT_WEBHOOK_SECRET" in text
        assert "PAYMENT_API_KEY" in text
        assert "PAYMENT_WEBHOOK_SIGNATURE_HEADER" in text
        assert "BILLING_PAID_PLANS_ENABLED" in text
    prod = read(".env.production.example")
    assert "BILLING_FAKE_UPGRADE_ENABLED=false" in prod
    validate = read("infra/deploy/validate-production-secrets.sh")
    assert "BILLING_FAKE_UPGRADE_ENABLED false" in validate
    assert "BILLING_PAID_PLANS_ENABLED cannot be true when PAYMENT_PROVIDER=disabled" in validate
    assert "PAYMENT_PROVIDER has unsupported value" in validate
    render = read("infra/deploy/render-runtime-env.sh")
    assert "BILLING_FAKE_UPGRADE_ENABLED" in render
    assert "PAYMENT_WEBHOOK_SIGNATURE_HEADER" in render


def test_billing_docs_exist():
    for path in (
        "docs/billing/production-billing-gate.md",
        "docs/architecture/stage-4-p2-04-billing-production-gate.md",
    ):
        text = read(path).lower()
        assert "production" in text
        assert "webhook" in text
        assert "fake" in text
        assert "fiscal" in text
