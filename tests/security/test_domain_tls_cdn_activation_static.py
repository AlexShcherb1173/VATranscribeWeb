from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_bytes(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def test_domain_tls_cdn_live_validation_scripts_exist_and_are_lf_safe():
    scripts = [
        "infra/deploy/validate-dns-live.sh",
        "infra/deploy/validate-tls-hsts-live.sh",
        "infra/deploy/validate-cdn-cache-live.sh",
    ]
    for script in scripts:
        data = read_bytes(script)
        assert data.startswith(b"#!/usr/bin/env bash")
        assert b"\r\n" not in data
        content = data.decode("utf-8")
        assert "set -euo pipefail" in content
        assert "/opt/vatranscribe/secrets/.env.runtime" in content


def test_dns_live_validator_checks_domains_expected_ip_and_caa():
    content = read("infra/deploy/validate-dns-live.sh")
    assert "CERTBOT_DOMAINS" in content
    assert "PRODUCTION_HOST_PUBLIC_IP" in content
    assert "CHECK_DNS_EXPECTED_IP" in content
    assert "DNS_REQUIRE_CAA" in content
    assert "dig +short A" in content
    assert "dig +short CAA" in content
    assert "DNS_A_RECORDS" in content
    assert "DNS_CAA_RECORDS" in content


def test_tls_hsts_validator_checks_certificate_redirect_and_hsts():
    content = read("infra/deploy/validate-tls-hsts-live.sh")
    assert "openssl s_client" in content
    assert "openssl x509" in content
    assert "TLS_EXPIRY_WARN_DAYS" in content
    assert "Strict-Transport-Security" in content
    assert "NGINX_HSTS_MAX_AGE" in content
    assert "HTTP_TO_HTTPS_REDIRECT_REQUIRED" in content
    assert "https://" in content


def test_cdn_cache_validator_blocks_api_cache_and_checks_static_assets():
    content = read("infra/deploy/validate-cdn-cache-live.sh")
    assert "CDN_API_ENABLED" in content
    assert "CDN_STATIC_TEST_URLS" in content
    assert "Cache-Control" in content
    assert "no-store|no-cache" in content
    assert "public|max-age" in content
    assert "immutable" in content
    assert "/api/v1/health/live" in content


def test_domain_tls_cdn_docs_and_evidence_templates_exist():
    docs = [
        "infra/deploy/domain-tls-cdn-evidence-template.md",
        "infra/deploy/domain-tls-cdn-activation-checklist.md",
        "docs/deployment/domain-tls-cdn-activation.md",
        "docs/architecture/stage-4-p3-03-domain-tls-cdn-activation.md",
        "docs/release/p3-production-activation-checklist.md",
    ]
    for doc in docs:
        content = read(doc)
        assert "P3-03" in content
        assert "/opt/vatranscribe/secrets/.env.runtime" in content
        assert "DO NOT" in content or "Do not" in content
        assert "DNS" in content
        assert "CDN" in content
        assert "HSTS" in content
        assert "certbot" in content.lower()
        assert "dry-run" in content
        assert "evidence" in content.lower()


def test_release_checklist_contains_p3_03_close_criteria():
    content = read("docs/release/p3-production-activation-checklist.md")
    assert "P3-03 Domain / TLS / CDN activation" in content
    assert "validate-dns-live.sh" in content
    assert "certbot-renew-dry-run.sh" in content
    assert "validate-tls-hsts-live.sh" in content
    assert "validate-cdn-cache-live.sh" in content
    assert "API traffic is not cached" in content
    assert "Redacted DNS/TLS/CDN evidence" in content


def test_gitignore_excludes_live_domain_tls_cdn_evidence():
    content = read(".gitignore")
    assert "domain-tls-cdn-evidence*.md" in content
    assert "*.curl-headers.txt" in content
    assert "*.tls-evidence.txt" in content
    assert "*.dns-evidence.txt" in content
