"""Typed error hierarchy for the AS2Expert client."""
from __future__ import annotations

from typing import Any, Optional


class As2ExpertError(Exception):
    """Base error. Carries the HTTP status and the API payload when available."""

    def __init__(self, message: str, *, status_code: Optional[int] = None,
                 payload: Optional[Any] = None, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload
        self.code = code


class AuthError(As2ExpertError):
    """401/403 — missing/invalid token or insufficient scope."""


class ValidationError(As2ExpertError):
    """400/422 — the request failed server-side validation."""

    def __init__(self, message: str, *, fields: Optional[list] = None, **kw: Any):
        super().__init__(message, **kw)
        self.fields = fields or []


class NotFoundError(As2ExpertError):
    """404 — the resource does not exist."""


class RateLimitError(As2ExpertError):
    """429 — too many requests. ``retry_after`` is seconds to wait, when known."""

    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kw: Any):
        super().__init__(message, **kw)
        self.retry_after = retry_after


class ServerError(As2ExpertError):
    """5xx — the API failed."""


class TransportError(As2ExpertError):
    """The request never completed (connection/timeout/TLS)."""


def error_for_status(status_code: int, message: str, payload: Any = None,
                     code: Optional[str] = None) -> As2ExpertError:
    kw = {"status_code": status_code, "payload": payload, "code": code}
    if status_code in (401, 403):
        return AuthError(message, **kw)
    if status_code in (400, 422):
        fields = payload.get("fields") if isinstance(payload, dict) else None
        return ValidationError(message, fields=fields, **kw)
    if status_code == 404:
        return NotFoundError(message, **kw)
    if status_code == 429:
        ra = payload.get("retry_after") if isinstance(payload, dict) else None
        return RateLimitError(message, retry_after=ra, **kw)
    if status_code >= 500:
        return ServerError(message, **kw)
    return As2ExpertError(message, **kw)
