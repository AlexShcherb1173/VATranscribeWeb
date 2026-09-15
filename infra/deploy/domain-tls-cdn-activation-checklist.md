# P3-03 Domain / TLS / CDN activation checklist

DO NOT commit real DNS/CDN tokens, TLS private keys, Let's Encrypt account keys, SSH private keys, server passwords, or generated live evidence containing secrets.

Runtime env source for activation checks: `/opt/vatranscribe/secrets/.env.runtime`

## Inputs

- [ ] `ROOT_DOMAIN=vatranscribe.ru`
- [ ] `MARKETING_DOMAIN=vatranscribe.ru`
- [ ] `APP_DOMAIN=app.vatranscribe.ru`
- [ ] `API_DOMAIN=api.vatranscribe.ru`
- [ ] `ADMIN_DOMAIN=admin.vatranscribe.ru`
- [ ] `PRODUCTION_HOST_PUBLIC_IP` is set on the production host.
- [ ] `CERTBOT_EMAIL` is replaced with a real operations email.
- [ ] `CERTBOT_DOMAINS` matches the domains above.
- [ ] `CHECK_DNS_EXPECTED_IP=true` is enabled when the production IP is final.

## DNS

- [ ] A/AAAA records resolve for all public domains.
- [ ] CNAME records are documented when CDN provider requires them.
- [ ] CAA policy is documented.
- [ ] DNS propagation checked from an external resolver.
- [ ] `infra/deploy/validate-dns-live.sh` passes.

## TLS / Certbot

- [ ] Port 80 is reachable for HTTP-01 challenge.
- [ ] Port 443 is reachable.
- [ ] `infra/deploy/certbot-issue.sh` completes live certificate issue.
- [ ] `infra/deploy/certbot-renew-dry-run.sh` passes.
- [ ] `infra/deploy/check-tls-renewal.sh` passes.
- [ ] `infra/deploy/validate-tls-hsts-live.sh` passes.

## HSTS

- [ ] `Strict-Transport-Security` exists on HTTPS responses.
- [ ] `max-age=31536000` is configured for production.
- [ ] `includeSubDomains` is present.
- [ ] HSTS preload remains disabled until all subdomains are stable.

## CDN / cache

- [ ] CDN provider is selected and documented.
- [ ] API traffic is not cached by CDN.
- [ ] HTML responses are `no-cache` or short TTL.
- [ ] Static hashed assets are long TTL and immutable.
- [ ] `CDN_STATIC_TEST_URLS` contains at least one real static asset URL for release evidence.
- [ ] `infra/deploy/validate-cdn-cache-live.sh` passes.

## Evidence

- [ ] Redacted DNS evidence is captured.
- [ ] Redacted TLS/HSTS evidence is captured.
- [ ] Redacted CDN/cache evidence is captured.
- [ ] Evidence is stored outside Git.
- [ ] Release checklist is updated with final P3-03 status.

## Close criteria

P3-03 can be marked production-closed only when DNS, CDN, live certbot issue, renewal dry-run, and HSTS checks are all verified against the real production domains.
