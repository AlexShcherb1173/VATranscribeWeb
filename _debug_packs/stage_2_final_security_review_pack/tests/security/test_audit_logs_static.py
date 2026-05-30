from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_audit_log_model_exists():
    text = read("apps/api/app/models.py")
    assert "class AuditLog(Base):" in text
    assert '__tablename__ = "audit_logs"' in text
    assert "meta_json" in text
    assert "ip_hash" in text
    assert "user_agent_hash" in text


def test_audit_service_records_audit_event():
    text = read("apps/api/app/services/audit_service.py")
    assert "def record_audit_event(" in text
    assert "AuditLog(" in text
    assert "_get_client_ip" in text
    assert "_get_user_agent" in text


def test_auth_router_writes_audit_events():
    text = read("apps/api/app/routers/auth.py")
    assert "auth.register_success" in text
    assert "auth.register_failed" in text
    assert "auth.login_success" in text
    assert "auth.login_failed" in text
    assert "auth.refresh_success" in text
    assert "auth.refresh_failed" in text
    assert "auth.logout" in text
    assert "auth.logout_all" in text


def test_billing_router_writes_audit_events():
    text = read("apps/api/app/routers/billing.py")
    assert "billing.overview_viewed" in text
    assert "billing.upgrade_requested" in text
    assert "billing.upgrade_succeeded" in text
    assert "billing.upgrade_failed" in text
