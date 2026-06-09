# Stage 4 / P1-03 — Redis-backed rate limiting + trusted proxy

## Статус

`P1-03_redis_rate_limiting_trusted_proxy` усиливает application-layer защиту поверх Nginx `limit_req` из P1-01.

## Что закрыто

- Добавлен `RedisBackedRateLimiter`.
- Сохранён `InMemoryRateLimiter` только как dev/test fallback.
- Добавлен `ConfiguredRateLimiter`, выбирающий backend через настройки.
- В production `RATE_LIMIT_BACKEND` должен быть `redis`.
- При недоступности Redis в production limiter работает fail-closed: HTTP 503.
- Добавлен единый `get_client_ip()` с trusted proxy CIDR-моделью.
- `X-Forwarded-For`, `X-Real-IP`, `Forwarded` учитываются только если непосредственный клиент входит в `TRUSTED_PROXY_CIDRS`.
- Private/loopback/link-local/reserved IP из forwarded headers не принимаются как внешний клиентский IP.
- Audit/consent IP hashing переведён на безопасный helper.
- Auth/download/upload/job routes используют лимиты из settings.
- Добавлен общий API middleware limiter.

## Основные env-переменные

```env
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_REDIS_URL=redis://redis:6379/2
RATE_LIMIT_FAIL_OPEN=false
TRUSTED_PROXY_CIDRS=127.0.0.1/32,::1/128,172.16.0.0/12
RATE_LIMIT_GENERAL_API_PER_MINUTE=120
RATE_LIMIT_AUTH_PER_MINUTE=10
RATE_LIMIT_AUTH_STRICT_PER_MINUTE=5
RATE_LIMIT_UPLOAD_PER_MINUTE=10
RATE_LIMIT_DOWNLOAD_PER_MINUTE=30
RATE_LIMIT_ANALYZE_PER_MINUTE=10
```

## Production notes

Для production `TRUSTED_PROXY_CIDRS` должен содержать только реальные CIDR reverse proxy/CDN/origin proxy. Не использовать `0.0.0.0/0`, `::/0` или широкие диапазоны без необходимости.

Nginx остаётся первым слоем throttling. API Redis limiter является вторым слоем и работает между несколькими API-инстансами.
