"""HTTP transport: auth, base URL, retries, and error mapping.

The AS2Expert API is POST-only and Bearer-authenticated. Responses are JSON with
a ``status`` field ("success"/"error"); on ``error`` (or a non-2xx code) we raise
a typed :mod:`as2expert.errors`.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

from . import __version__
from .errors import As2ExpertError, TransportError, error_for_status

DEFAULT_TIMEOUT = 30.0
_RETRY_STATUS = {429, 500, 502, 503, 504}


class Transport:
    def __init__(self, token: str, base_url: str, *, timeout: float = DEFAULT_TIMEOUT,
                 verify_tls: bool = True, max_retries: int = 2,
                 session: Optional[requests.Session] = None,
                 user_agent: Optional[str] = None):
        if not token:
            raise ValueError("An API token is required")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.verify_tls = verify_tls
        self.max_retries = max_retries
        self._session = session or requests.Session()
        self._session.headers.update({
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": user_agent or ("as2expert-python/" + __version__),
        })

    def post(self, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self.base_url + "/" + path.lstrip("/")
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._session.post(url, json=body or {}, timeout=self.timeout,
                                          verify=self.verify_tls)
            except requests.RequestException as exc:
                if attempt <= self.max_retries:
                    time.sleep(_backoff(attempt))
                    continue
                raise TransportError("Request to %s failed: %s" % (url, exc)) from exc
            if resp.status_code in _RETRY_STATUS and attempt <= self.max_retries:
                time.sleep(_backoff(attempt))
                continue
            return _parse(resp)

    def close(self) -> None:
        self._session.close()


def _backoff(attempt: int) -> float:
    return min(0.5 * (2 ** (attempt - 1)), 5.0)


def _parse(resp: "requests.Response") -> Dict[str, Any]:
    try:
        data = resp.json()
    except ValueError:
        if resp.ok:
            return {"status": "success"}
        raise error_for_status(resp.status_code,
                               "Non-JSON response (HTTP %d)" % resp.status_code,
                               payload=resp.text[:500])
    if not resp.ok or (isinstance(data, dict) and data.get("status") == "error"):
        msg = data.get("msg") or data.get("message") or ("HTTP %d" % resp.status_code) \
            if isinstance(data, dict) else ("HTTP %d" % resp.status_code)
        code = data.get("error") or data.get("code") if isinstance(data, dict) else None
        raise error_for_status(resp.status_code, msg, payload=data, code=code)
    if not isinstance(data, dict):
        raise As2ExpertError("Unexpected response shape", status_code=resp.status_code,
                             payload=data)
    return data
