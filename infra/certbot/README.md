# Certbot runtime directory

This directory is mounted by the production nginx and certbot containers.

Tracked files are documentation and `.gitkeep` placeholders only. Real certificate material must never be committed.

Runtime layout on the production host:

```text
infra/certbot/conf/   # /etc/letsencrypt in certbot and nginx
infra/certbot/www/    # HTTP-01 webroot for /.well-known/acme-challenge/
```

The directories are populated by:

```bash
./infra/deploy/certbot-issue.sh
./infra/deploy/certbot-renew.sh
```
