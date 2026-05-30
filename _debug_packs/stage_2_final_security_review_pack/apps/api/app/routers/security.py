from __future__ import annotations

from fastapi import APIRouter, Request

from apps.api.app.security_foundation.rate_limits import rate_limiter


router = APIRouter(prefix='/security', tags=['security'])


@router.get('/ping-rate-limit')
def ping_rate_limit(request: Request) -> dict[str, str]:
    client = request.client.host if request.client else 'unknown'
    rate_limiter.check(
        key='security_ping:' + client,
        limit=10,
        window_seconds=60,
    )
    return {'status': 'ok'}
