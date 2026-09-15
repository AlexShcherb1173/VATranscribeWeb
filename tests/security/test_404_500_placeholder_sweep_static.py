from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_marketing_error_pages_exist_and_are_noindexed():
    for path in [
        "apps/marketing/src/pages/404.astro",
        "apps/marketing/src/pages/500.astro",
        "apps/marketing/src/pages/ru/404.astro",
        "apps/marketing/src/pages/ru/500.astro",
    ]:
        content = read(path)
        assert "MarketingLayout" in content
        assert "noindex={true}" in content
        assert "Lorem ipsum" not in content
        assert "TODO" not in content


def test_web_not_found_route_and_error_boundary_exist():
    router = read("apps/web/src/app/router/index.tsx")
    not_found = read("apps/web/src/pages/not-found/NotFoundPage.tsx")
    error_boundary = read("apps/web/src/shared/ui/ErrorBoundary.tsx")
    main = read("apps/web/src/main.tsx")

    assert "NotFoundPage" in router
    assert 'path: "*"' in router or "path: '*'" in router
    assert "Page not found" in not_found
    assert "ErrorBoundary" in main
    assert "import.meta.env.DEV" in error_boundary
    assert "stack" not in error_boundary.lower()


def test_api_production_safe_exception_handlers_are_registered():
    main = read("apps/api/app/main.py")
    handlers = read("apps/api/app/exception_handlers.py")

    assert "register_exception_handlers" in main
    assert "register_exception_handlers(app, settings=settings)" in main
    assert "StarletteHTTPException" in handlers
    assert "RequestValidationError" in handlers
    assert "Internal server error" in handlers
    assert "settings.is_production" in handlers
    assert "traceback" not in handlers.lower()


def test_robots_and_sitemap_are_present_and_404_not_in_sitemap_source():
    robots = read("apps/marketing/src/pages/robots.txt.ts")
    sitemap = read("apps/marketing/src/pages/sitemap.xml.ts")
    seo = read("apps/marketing/src/config/seo.ts")

    assert "Sitemap:" in robots
    assert "allSeoPages" in sitemap
    assert ".filter((page) => !page.noindex)" in sitemap
    assert 'path: "/404"' not in seo
    assert 'path: "/500"' not in seo
