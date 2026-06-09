# Stage 4 P1-05 — Container production hardening

Status: patch candidate.

## Scope

P1-05 hardens the Docker Compose production runtime:

- API and worker run as non-root `10001:10001`.
- `C_FORCE_ROOT=true` is removed from the worker image and overridden to `false` in production compose.
- API is exposed only to the internal Docker network; public traffic must go through Nginx.
- Postgres and Redis no longer publish host ports in production compose.
- API and worker no longer bind-mount the whole project directory in production compose.
- API and worker use a dedicated writable `/app/storage` volume.
- API and worker use `read_only: true` and `tmpfs` for `/tmp`.
- API and worker drop Linux capabilities with `cap_drop: ALL`.
- API, worker and web use `no-new-privileges:true` where compatible.

## P1-05b — Network egress hardening for yt-dlp

P1-02 blocks SSRF at API input, core fallback and urllib redirect handling. However, `yt-dlp` has its own network stack. Production therefore also needs host/container egress controls.

This patch adds an iptables `DOCKER-USER` policy template:

- allow API/worker to DB `5432`;
- allow API/worker to Redis `6379`;
- deny loopback/private/link-local/metadata egress;
- allow public HTTP/HTTPS `80,443` for external media downloads;
- optionally reject all other API/worker egress in strict mode.

The firewall script is not auto-run. It must be applied on the Linux Docker host after production containers are running.

## Production validation

Run:

```powershell
pytest tests/security/test_container_production_hardening_static.py -v
pytest tests/security/test_network_egress_policy_static.py -v
pytest -v
npm --prefix apps/web run build
docker compose -f docker-compose.yml -f infra/compose/docker-compose.prod.yml config
```

On the Linux production/staging host:

```bash
cp infra/security/egress-policy.env.example infra/security/egress-policy.env
sudo bash infra/security/apply-egress-policy.sh infra/security/egress-policy.env
```

Rollback:

```bash
sudo bash infra/security/remove-egress-policy.sh infra/security/egress-policy.env
```

## Known limitations

- Docker Compose YAML alone cannot express robust egress-deny policies.
- IPv6 needs separate `ip6tables`/nftables handling or explicit production disablement.
- The firewall script should be validated on staging because container IPs are runtime-specific.
