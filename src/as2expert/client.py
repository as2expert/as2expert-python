"""The AS2Expert API client."""
from __future__ import annotations

from typing import Optional

import requests

from ._http import DEFAULT_TIMEOUT, Transport
from . import resources

#: Convenience presets; pass base_url explicitly to target any other host.
ENVIRONMENTS = {
    "free": "https://free.as2expert.com/api/v1",
    "b2b": "https://b2b.as2expert.com/api/v1",
}


class AS2ExpertClient:
    """Client for the AS2Expert REST API.

    Example::

        from as2expert import AS2ExpertClient
        client = AS2ExpertClient(token="...", base_url="https://free.as2expert.com/api/v1")
        for msg in client.messages.list(limit=20):
            print(msg["id"], msg.get("asunto"))
    """

    def __init__(self, token: str, *, base_url: Optional[str] = None,
                 environment: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT,
                 verify_tls: bool = True, max_retries: int = 2,
                 session: Optional[requests.Session] = None,
                 user_agent: Optional[str] = None):
        if base_url is None:
            if environment not in ENVIRONMENTS:
                raise ValueError(
                    "Provide base_url, or environment one of: %s"
                    % ", ".join(sorted(ENVIRONMENTS)))
            base_url = ENVIRONMENTS[environment]
        self._transport = Transport(token, base_url, timeout=timeout,
                                    verify_tls=verify_tls, max_retries=max_retries,
                                    session=session, user_agent=user_agent)
        self.messages = resources.Messages(self._transport)
        self.partners = resources.Partners(self._transport)
        self.certificates = resources.Certificates(self._transport)
        self.stations = resources.Stations(self._transport)
        self.webhooks = resources.Webhooks(self._transport)
        self.business_documents = resources.BusinessDocuments(self._transport)
        self.edifact = resources.Edifact(self._transport)
        self.dashboard = resources.Dashboard(self._transport)

    @property
    def base_url(self) -> str:
        return self._transport.base_url

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "AS2ExpertClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
