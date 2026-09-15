from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

USER_FACING_FILES = [
    "apps/marketing/src/config/legal.ts",
    "apps/marketing/src/config/legal.ru.ts",
    "apps/web/src/shared/i18n/I18nProvider.tsx",
    "apps/web/src/pages/shared/i18n/I18nProvider.tsx",
    "apps/marketing/src/pages/404.astro",
    "apps/marketing/src/pages/500.astro",
    "apps/marketing/src/pages/ru/404.astro",
    "apps/marketing/src/pages/ru/500.astro",
    "apps/web/src/pages/not-found/NotFoundPage.tsx",
]

BLOCKED_PHRASES = [
    "Lorem ipsum",
    "TODO",
    "FIXME",
    "test@example.com",
    "admin@example.com",
    "legal@example.com",
    "privacy@example.com",
    "temporary payment form placeholder",
    "Fake payment",
    "fake payment completed",
    "Тестовая оплата",
    "временная заглушка платежной формы",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_user_facing_files_do_not_contain_launch_blocking_placeholders():
    failures: list[str] = []
    for path in USER_FACING_FILES:
        content = read(path)
        for phrase in BLOCKED_PHRASES:
            if phrase in content:
                failures.append(f"{path}: {phrase}")

    assert failures == []


def test_public_legal_contacts_use_project_domain_aliases():
    legal_en = read("apps/marketing/src/config/legal.ts")
    legal_ru = read("apps/marketing/src/config/legal.ru.ts")
    combined = legal_en + "\n" + legal_ru

    assert "legal@vatranscribe.ru" in combined
    assert "privacy@vatranscribe.ru" in combined
    assert "legal@example.com" not in combined
    assert "privacy@example.com" not in combined


def test_release_checklist_documents_allowed_template_exception():
    checklist = read("docs/release/no-placeholder-checklist.md")
    assert "Allowed examples" in checklist
    assert ".env.example" in checklist
    assert "production validation scripts" in checklist
