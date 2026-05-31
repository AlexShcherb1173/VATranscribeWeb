from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_auth_register_imports_password_policy():
    text = read("apps/api/app/routers/auth.py")

    assert "from apps.api.app.security_foundation.password_policy import PasswordPolicyError, validate_password_strength" in text


def test_auth_register_validates_password_before_consents_and_user_creation():
    text = read("apps/api/app/routers/auth.py")

    register_index = text.index('@router.post("/register"')
    login_index = text.index('@router.post("/login"')
    register_block = text[register_index:login_index]

    password_policy_index = register_block.index("validate_password_strength(payload.password)")
    consents_index = register_block.index("validate_required_consents(")
    user_create_index = register_block.index("user = User(")

    assert password_policy_index < consents_index < user_create_index


def test_auth_register_audits_password_policy_failure():
    text = read("apps/api/app/routers/auth.py")

    register_index = text.index('@router.post("/register"')
    login_index = text.index('@router.post("/login"')
    register_block = text[register_index:login_index]

    assert "PasswordPolicyError" in register_block
    assert '"reason": "password_policy_failed"' in register_block
    assert '"policy_error": str(exc)' in register_block
    assert "auth.register_failed" in register_block
    assert "HTTP_422_UNPROCESSABLE_ENTITY" in register_block
