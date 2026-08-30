"""AS2Expert — official Python client for the AS2Expert REST API.

Send and receive AS2/EDI messages and manage partners, certificates and stations.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .client import AS2ExpertClient, ENVIRONMENTS
from .errors import (
    As2ExpertError, AuthError, ValidationError, NotFoundError, RateLimitError,
    ServerError, TransportError,
)
from .webhooks import verify_signature, sign_payload

__all__ = [
    "AS2ExpertClient", "ENVIRONMENTS",
    "As2ExpertError", "AuthError", "ValidationError", "NotFoundError",
    "RateLimitError", "ServerError", "TransportError",
    "verify_signature", "sign_payload", "__version__",
]
