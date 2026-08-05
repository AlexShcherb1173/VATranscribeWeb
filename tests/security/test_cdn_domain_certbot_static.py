from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_env_examples_document_domain_cdn_and_certbot_settings():
    for path in (".env.example", ".env.production.example"):
        text = read(path)
        assert "ROOT_DOMAIN=vatranscribe.ru" in text
        assert "APP_DOMAIN=app.vatranscribe.ru" in text
        assert "API_DOMAIN=api.vatranscribe.ru" in text
        assert "ADMIN_DOMAIN=admin.vatranscribe.ru" in text
        assert "CDN_PROVIDER=provider-neutral" in text
        assert "CDN_API_ENABLED=false" in text
        assert "CDN_ASSET_CACHE_SECONDS=31536000" in text
        assert "CERTBOT_EMAIL=" in text
        assert "CERTBOT_DOMAINS=vatranscribe.ru,app.vatranscribe.ru,api.vatranscribe.ru,admin.vatranscribe.ru" in text
        assert "HSTS_PRELOAD_ENABLED=false" in text


def test_nginx_supports_acme_challenge_and_cache_headers():
    text = read("infra/docker/nginx.prod.conf.template")
    assert "location ^~ /.well-known/acme-challenge/" in text
    assert "root /var/www/certbot;" in text
    assert "try_files $uri =404;" in text
    assert "return 301 https://$host$request_uri;" in text
    assert "Cache-Control \"no-store\"" in text
    assert "location ^~ /app/assets/" in text
    assert "location ^~ /assets/" in text
    assert "location ^~ /_astro/" in text
    assert "public, max-age=${CDN_ASSET_CACHE_SECONDS}, immutable" in text
    assert "no-cache, max-age=0, must-revalidate" in text
    assert "preload" not in text.lower()


def test_api_routes_are_not_cacheable():
    text = read("infra/docker/nginx.prod.conf.template")
    assert "location /api/" in text
    assert 'add_header Cache-Control "no-store" always;' in text
    assert "CDN_API_ENABLED=false" in read(".env.production.example")


def test_prod_compose_defines_certbot_service_and_mounts_webroot():
    text = read("infra/compose/docker-compose.prod.yml")
    assert "container_name: vatranscribe-certbot" in text
    assert "certbot/certbot" in text
    assert "profiles:" in text and "certbot" in text
    assert "./infra/certbot/conf:/etc/letsencrypt" in text
    assert "./infra/certbot/www:/var/www/certbot" in text
    assert "CDN_ASSET_CACHE_SECONDS" in text


def test_certbot_and_domain_scripts_exist_with_required_commands():
    issue = read("infra/deploy/certbot-issue.sh")
    renew = read("infra/deploy/certbot-renew.sh")
    dry = read("infra/deploy/certbot-renew-dry-run.sh")
    check_domain = read("infra/deploy/check-domain-readiness.sh")
    check_tls = read("infra/deploy/check-tls-renewal.sh")
    assert "certonly" in issue
    assert "--webroot" in issue
    assert "--agree-tos" in issue
    assert "--staging" in issue
    assert "openssl req -x509" in issue
    assert "nginx -s reload" in issue
    assert "renew --webroot" in renew
    assert "renew --dry-run" in dry
    assert "PRODUCTION_HOST_PUBLIC_IP" in check_domain
    assert "openssl s_client" in check_tls
    assert "x509 -checkend" in check_tls


def test_systemd_timer_and_docs_exist():
    service = read("infra/deploy/systemd/vatranscribe-certbot-renew.service")
    timer = read("infra/deploy/systemd/vatranscribe-certbot-renew.timer")
    assert "certbot-renew.sh" in service
    assert "OnCalendar=" in timer
    assert "Persistent=true" in timer
    assert "dns records" in read("infra/deploy/dns-records.md").lower()
    assert "cdn cache rules" in read("infra/deploy/cdn-cache-rules.md").lower()
    assert "certbot-renew-dry-run" in read("docs/deployment/domain-cdn-certbot.md")


def test_secret_renderer_and_validator_include_domain_tls_vars():
    render = read("infra/deploy/render-runtime-env.sh")
    validate = read("infra/deploy/validate-production-secrets.sh")
    for name in (
        "ROOT_DOMAIN",
        "MARKETING_DOMAIN",
        "APP_DOMAIN",
        "API_DOMAIN",
        "ADMIN_DOMAIN",
        "CERTBOT_EMAIL",
        "CERTBOT_DOMAINS",
        "CDN_API_ENABLED",
        "HSTS_PRELOAD_ENABLED",
    ):
        assert name in render
        assert name in validate
    assert "CDN_API_ENABLED false" in validate
    assert "HSTS_PRELOAD_ENABLED false" in validate


def test_certbot_runtime_root_matches_immutable_release_layout():
    scripts = (
        "infra/deploy/certbot-issue.sh",
        "infra/deploy/certbot-renew.sh",
        "infra/deploy/certbot-renew-dry-run.sh",
        "infra/deploy/sync-nginx-certificates.sh",
    )
    expected_root = "PROJECT_ROOT=\"${PROJECT_ROOT:-/opt/vatranscribe/app}\""

    for path in scripts:
        content = read(path)
        assert expected_root in content
        assert "/srv/vatranscribe" not in content

    service = read("infra/deploy/systemd/vatranscribe-certbot-renew.service")
    assert "WorkingDirectory=/opt/vatranscribe/app" in service
    assert "Environment=PROJECT_ROOT=/opt/vatranscribe/app" in service
    assert "ExecStart=/opt/vatranscribe/app/infra/deploy/certbot-renew.sh" in service
    assert "/srv/vatranscribe" not in service

    timer = read("infra/deploy/systemd/vatranscribe-certbot-renew.timer")
    assert "Unit=vatranscribe-certbot-renew.service" in timer
