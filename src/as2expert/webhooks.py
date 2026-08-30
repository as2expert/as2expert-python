"""Helpers to verify inbound AS2Expert webhook signatures.

AS2Expert signs webhook deliveries with HMAC-SHA256 over ``"<timestamp>.<body>"``,
sent in the headers ``X-AS2Expert-Timestamp`` and ``X-AS2Expert-Signature``
(``sha256=<hex>``). Use :func:`verify_signature` in your receiver.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Union

_MAX_SKEW = 300   # seconds


def sign_payload(secret: str, timestamp: Union[str, int], body: str) -> str:
    """Return the ``sha256=<hex>`` signature for a body + timestamp (for tests)."""
    mac = hmac.new(secret.encode("utf-8"),
                   ("%s.%s" % (timestamp, body)).encode("utf-8"), hashlib.sha256)
    return "sha256=" + mac.hexdigest()


def verify_signature(secret: str, timestamp: Union[str, int], body: str,
                     signature: str, *, tolerance_seconds: int = _MAX_SKEW,
                     now: Union[int, None] = None) -> bool:
    """True iff ``signature`` matches and ``timestamp`` is within tolerance."""
    if not secret or not signature or timestamp in (None, ""):
        return False
    try:
        ts = int(str(timestamp))
    except (TypeError, ValueError):
        return False
    current = int(time.time()) if now is None else int(now)
    if abs(current - ts) > tolerance_seconds:
        return False
    expected = sign_payload(secret, timestamp, body)
    provided = signature if signature.startswith("sha256=") else ("sha256=" + signature)
    return hmac.compare_digest(expected, provided)
