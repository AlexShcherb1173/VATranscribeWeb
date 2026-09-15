# P2-05 Domain, CDN and Certbot activation

## Defaults

- Root/marketing: `vatranscribe.ru`
- App: `app.vatranscribe.ru`
- API: `api.vatranscribe.ru`
- Admin: `admin.vatranscribe.ru`
- Challenge: HTTP-01 via nginx webroot
- Wildcard certificate: disabled
- HSTS preload: disabled for now
- CDN for API: disabled
- CDN for static assets: enabled by policy after provider selection

## Required production steps

1. Fill `/opt/vatranscribe/secrets/.env.runtime` with real values:
   - `PRODUCTION_HOST_PUBLIC_IP`
   - `CERTBOT_EMAIL`
   - `CERTBOT_DOMAINS`
   - domain variables and public origins
2. Configure DNS records from `infra/deploy/dns-records.md`.
3. Run domain readiness check:

```bash
CHECK_DNS_EXPECTED_IP=true ./infra/deploy/check-domain-readiness.sh
```

4. Issue certificate:

```bash
CERTBOT_STAGING=true ./infra/deploy/certbot-issue.sh
CERTBOT_STAGING=false ./infra/deploy/certbot-issue.sh
```

5. Test renewal:

```bash
./infra/deploy/certbot-renew-dry-run.sh
```

6. Install systemd timer:

```bash
sudo cp infra/deploy/systemd/vatranscribe-certbot-renew.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vatranscribe-certbot-renew.timer
systemctl list-timers | grep vatranscribe-certbot-renew
```

7. Configure CDN cache rules from `infra/deploy/cdn-cache-rules.md`.

## Release gate

Public production is not release-ready until:

- `certbot-renew-dry-run.sh` passes;
- `check-tls-renewal.sh` passes;
- CDN cache bypass for `/api/*` is verified;
- static asset cache headers are verified;
- HSTS preload remains disabled until explicit approval.
