# VATranscribe egress policy for Docker Compose production

This policy is a defense-in-depth layer for `yt-dlp` and other network clients running inside the `api` and `worker` containers.

P1-02 validates user URLs at the application level. This host-level policy reduces blast radius if a URL bypasses application validation or a third-party network client follows an unexpected redirect.

## Policy

Allowed:

- `api` / `worker` -> `db:5432`
- `api` / `worker` -> `redis:6379`
- `api` / `worker` -> public TCP `80,443`

Denied:

- loopback: `127.0.0.0/8`
- private IPv4: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- link-local and metadata: `169.254.0.0/16`, `169.254.169.254/32`
- carrier-grade NAT and reserved ranges: `100.64.0.0/10`, `0.0.0.0/8`, `240.0.0.0/4`

## Apply

Run on the Linux Docker host after production containers are up:

```bash
cp infra/security/egress-policy.env.example infra/security/egress-policy.env
sudo bash infra/security/apply-egress-policy.sh infra/security/egress-policy.env
```

## Remove

```bash
sudo bash infra/security/remove-egress-policy.sh infra/security/egress-policy.env
```

## Notes

- The script uses the Docker `DOCKER-USER` chain, so the rules are evaluated before Docker's own forwarding rules.
- IPv6 requires a separate `ip6tables`/nftables policy or disabling IPv6 on the production Docker networks.
- Do not auto-run this from application containers. It is a host firewall action.
- Validate on staging before production.
