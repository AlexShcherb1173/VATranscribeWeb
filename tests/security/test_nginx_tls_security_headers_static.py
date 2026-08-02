from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEV_NGINX = PROJECT_ROOT / "infra" / "docker" / "nginx.conf"
PROD_NGINX = PROJECT_ROOT / "infra" / "docker" / "nginx.prod.conf.template"
PROD_COMPOSE = PROJECT_ROOT / "infra" / "compose" / "docker-compose.prod.yml"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
ENV_PRODUCTION_EXAMPLE = PROJECT_ROOT / ".env.production.example"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_production_nginx_template_has_tls_and_https_redirect():
    text = read(PROD_NGINX)
    assert "listen 80;" in text
    assert "return 301 https://$host$request_uri;" in text
    assert "listen 443 ssl http2;" in text
    assert "ssl_certificate ${NGINX_SSL_CERTIFICATE};" in text
    assert "ssl_certificate_key ${NGINX_SSL_CERTIFICATE_KEY};" in text
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in text


def test_hsts_and_core_security_headers_are_present():
    text = read(PROD_NGINX)
    assert "Strict-Transport-Security" in text
    assert "max-age=${NGINX_HSTS_MAX_AGE}; includeSubDomains" in text
    assert "preload" not in text.lower()
    assert 'X-Content-Type-Options "nosniff"' in text
    assert 'Referrer-Policy "strict-origin-when-cross-origin"' in text
    assert "Permissions-Policy" in text
    assert 'X-Frame-Options "DENY"' in text


def test_csp_baseline_is_strict_in_production_template():
    text = read(PROD_NGINX)
    assert "Content-Security-Policy" in text
    assert "default-src 'self'" in text
    assert "script-src 'self'" in text
    assert "img-src 'self' data: blob:" in text
    assert "font-src 'self' data:" in text
    assert "connect-src 'self' ${PUBLIC_API_ORIGIN}" in text
    assert "frame-ancestors 'none'" in text
    assert "base-uri 'self'" in text
    assert "form-action 'self'" in text
    assert "http://localhost" not in text
    assert "http://127.0.0.1" not in text


def test_rate_limit_zones_exist_in_dev_and_prod_nginx():
    for path in (DEV_NGINX, PROD_NGINX):
        text = read(path)
        assert "limit_req_zone $binary_remote_addr zone=general_api_limit" in text
        assert "limit_req_zone $binary_remote_addr zone=auth_limit" in text
        assert "limit_req_zone $binary_remote_addr zone=auth_strict_limit" in text
        assert "limit_req_zone $binary_remote_addr zone=upload_limit" in text
        assert "limit_req_zone $binary_remote_addr zone=download_limit" in text
        assert "limit_req_status 429;" in text


def test_request_body_limits_are_split_by_surface():
    dev = read(DEV_NGINX)
    prod = read(PROD_NGINX)
    assert "client_max_body_size 20m;" in dev
    assert "client_max_body_size 1m;" in dev
    assert "client_max_body_size 2m;" in dev
    assert "client_max_body_size 1024m;" in dev
    assert "client_max_body_size ${NGINX_GLOBAL_BODY_LIMIT};" in prod
    assert "client_max_body_size ${NGINX_AUTH_BODY_LIMIT};" in prod
    assert "client_max_body_size ${NGINX_ANALYZE_BODY_LIMIT};" in prod
    assert "client_max_body_size ${NGINX_UPLOAD_BODY_LIMIT};" in prod


def test_production_compose_exposes_https_and_mounts_tls_template():
    text = read(PROD_COMPOSE)
    assert "${WEB_HTTP_PORT:-80}:80" in text
    assert "${WEB_HTTPS_PORT:-443}:443" in text
    assert "nginx.prod.conf.template:/etc/nginx/templates/default.conf.template:ro" in text
    assert "vatranscribe_nginx_certs:/etc/letsencrypt:ro" in text
    assert "./infra/certbot/conf:/etc/letsencrypt" in text
    assert "vatranscribe_nginx_certs:/etc/nginx-certs" in text
    assert "./infra/certbot/www:/var/www/certbot:ro" in text


def test_env_examples_document_nginx_tls_settings():
    for path in (ENV_EXAMPLE, ENV_PRODUCTION_EXAMPLE):
        text = read(path)
        assert "NGINX_SERVER_NAME=" in text
        assert "NGINX_SSL_CERTIFICATE=" in text
        assert "NGINX_SSL_CERTIFICATE_KEY=" in text
        assert "NGINX_HSTS_MAX_AGE=31536000" in text
        assert "NGINX_AUTH_STRICT_RATE=5r/m" in text
        assert "NGINX_UPLOAD_BODY_LIMIT=1024m" in text
