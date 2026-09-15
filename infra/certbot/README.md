# Certbot runtime directory

Tracked files are documentation and `.gitkeep` placeholders only. Real
certificate material must never be committed.

Runtime layout on the production host:

```text
infra/certbot/conf/   # Certbot state and Let's Encrypt source material
infra/certbot/www/    # HTTP-01 webroot
```

The Certbot container owns the source certificate tree.

The non-root nginx container does not mount the source
`infra/certbot/conf` directory. Instead, active certificate files are copied
into the `vatranscribe_nginx_certs` named volume.

The named volume is mounted by nginx as:

```text
/etc/letsencrypt/live/<primary-domain>/fullchain.pem
/etc/letsencrypt/live/<primary-domain>/privkey.pem
```

This preserves the established nginx certificate paths while preventing the
web container from reading Certbot account data, renewal configuration, and
the complete certificate archive.

The copied files are owned by UID/GID `101:101`. The private key has mode
`0400`. The named volume is mounted read-only by the web container.

Certificate operations:

```bash
./infra/deploy/certbot-issue.sh
./infra/deploy/certbot-renew.sh
./infra/deploy/sync-nginx-certificates.sh
```
