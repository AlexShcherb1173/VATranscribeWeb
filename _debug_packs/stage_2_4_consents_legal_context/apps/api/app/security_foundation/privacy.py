from __future__ import annotations

import hashlib


def hash_ip_address(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()


def mask_email(email: str) -> str:
    if '@' not in email:
        return email
    name, domain = email.split('@', 1)
    if len(name) <= 2:
        masked = '*' * len(name)
    else:
        masked = name[0] + '*' * (len(name) - 2) + name[-1]
    return masked + '@' + domain
