"""Resource namespaces. Each method maps to one AS2Expert REST endpoint and
returns the response ``data`` payload (a dict, or a list for collections)."""
from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Union

from ._http import Transport


def _b64(content: Union[str, bytes]) -> str:
    if isinstance(content, bytes):
        return base64.b64encode(content).decode("ascii")
    return content   # assume already base64


class _Resource:
    def __init__(self, transport: Transport):
        self._t = transport

    def _data(self, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        return self._t.post(path, body).get("data")


class Messages(_Resource):
    def list(self, *, station: Optional[Any] = None, folder: Optional[Any] = None,
             limit: Optional[int] = None) -> List[Dict[str, Any]]:
        body: Dict[str, Any] = {}
        if station is not None:
            body["station"] = station
        if folder is not None:
            body["folder"] = folder
        if limit is not None:
            body["limit"] = limit
        return self._data("/messages", body) or []

    def folders(self, *, station: Optional[Any] = None) -> List[Dict[str, Any]]:
        """List a station's folders (id, name, parent_id, count, icono, …)."""
        body = {"station": station} if station is not None else {}
        return self._data("/messages/folders", body) or []

    def get(self, message_id: Any) -> Dict[str, Any]:
        return self._data("/messages/detail", {"id": message_id})

    def download(self, message_id: Any) -> bytes:
        """Return the raw message payload bytes (decoded from base64)."""
        data = self._data("/messages/download", {"id": message_id}) or {}
        b64 = data.get("content_b64") or data.get("contenido_base64") or ""
        return base64.b64decode(b64) if b64 else b""

    def send(self, *, partner: Any, subject: str, file_name: str,
             file_content: Union[str, bytes]) -> Dict[str, Any]:
        return self._data("/messages/send", {
            "partner": partner, "subject": subject,
            "file_name": file_name, "file_content": _b64(file_content),
        })

    def mark_read(self, message_id: Any) -> Dict[str, Any]:
        return self._data("/messages/mark-read", {"id": message_id})

    def mark_unread(self, message_id: Any) -> Dict[str, Any]:
        return self._data("/messages/mark-unread", {"id": message_id})

    def move(self, message_id: Any, folder: Any) -> Dict[str, Any]:
        return self._data("/messages/move", {"id": message_id, "folder": folder})

    def delete(self, message_id: Any) -> Dict[str, Any]:
        return self._data("/messages/delete", {"id": message_id})

    def changes(self, **params: Any) -> Any:
        return self._data("/messages/changes", params)

    def files(self, message_id: Any) -> Any:
        return self._data("/messages/files", {"id": message_id})

    def file_download(self, message_id: Any, file_id: Any) -> bytes:
        data = self._data("/messages/file-download",
                          {"id": message_id, "file_id": file_id}) or {}
        b64 = data.get("content_b64") or data.get("contenido_base64") or ""
        return base64.b64decode(b64) if b64 else b""

    def export(self, **params: Any) -> Any:
        return self._data("/messages/export", params)


class Partners(_Resource):
    def list(self, *, station: Optional[Any] = None) -> List[Dict[str, Any]]:
        body = {"station": station} if station is not None else {}
        return self._data("/partners", body) or []

    def get(self, partner_id: Any) -> Dict[str, Any]:
        return self._data("/partners/detail", {"id": partner_id})

    def create(self, **fields: Any) -> Dict[str, Any]:
        return self._data("/partners/create", fields)

    def update(self, partner_id: Any, **fields: Any) -> Dict[str, Any]:
        return self._data("/partners/update", {"id": partner_id, **fields})

    def delete(self, partner_id: Any) -> Dict[str, Any]:
        return self._data("/partners/delete", {"id": partner_id})


class Certificates(_Resource):
    def list(self) -> List[Dict[str, Any]]:
        return self._data("/certificates", {}) or []

    def get(self, certificate_id: Any) -> Dict[str, Any]:
        return self._data("/certificates/detail", {"id": certificate_id})

    def create(self, **fields: Any) -> Dict[str, Any]:
        return self._data("/certificates/create", fields)


class Stations(_Resource):
    def list(self, *, id: Optional[Any] = None) -> List[Dict[str, Any]]:
        body = {"id": id} if id is not None else {}
        return self._data("/stations", body) or []

    def get(self, station_id: Any) -> Dict[str, Any]:
        return self._data("/stations/detail", {"id": station_id})

    def stats(self, station_id: Any) -> Dict[str, Any]:
        return self._data("/stations/stats", {"id": station_id})

    def create(self, **fields: Any) -> Dict[str, Any]:
        return self._data("/stations/create", fields)

    def update(self, station_id: Any, **fields: Any) -> Dict[str, Any]:
        return self._data("/stations/update", {"id": station_id, **fields})

    def delete(self, station_id: Any) -> Dict[str, Any]:
        return self._data("/stations/delete", {"id": station_id})


class Webhooks(_Resource):
    def configure(self, **fields: Any) -> Dict[str, Any]:
        return self._data("/webhooks/configure", fields)

    def get(self, **params: Any) -> Any:
        return self._data("/webhooks/get", params)

    def test(self, **params: Any) -> Any:
        return self._data("/webhooks/test", params)

    def logs(self, **params: Any) -> Any:
        return self._data("/webhooks/logs", params)


class BusinessDocuments(_Resource):
    def create(self, document: Dict[str, Any], *,
               idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        # Idempotency-Key travels as a header for BD create.
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        resp = self._t.post("/business-documents", document) if headers is None else \
            _post_with_headers(self._t, "/business-documents", document, headers)
        return resp.get("data", resp)

    def get(self, bd_ref: str) -> Dict[str, Any]:
        return self._data("/business-documents/detail", {"business_document_id": bd_ref})

    def diagnostics(self, **params: Any) -> Any:
        return self._data("/business-documents/diagnostics", params)


class Edifact(_Resource):
    def analyze(self, edifact: str) -> Dict[str, Any]:
        return self._data("/edifact/analyze", {"edifact": edifact})

    validate = analyze  # alias endpoint

    def convert(self, *, edifact: Optional[str] = None, analysis_id: Optional[str] = None,
                format: str = "json", sequence: int = 1) -> Dict[str, Any]:
        body: Dict[str, Any] = {"format": format, "sequence": sequence}
        if edifact is not None:
            body["edifact"] = edifact
        if analysis_id is not None:
            body["analysis_id"] = analysis_id
        return self._data("/edifact/convert", body)

    def acknowledge(self, edifact: str, *, kind: str = "contrl",
                    acknowledged: bool = True,
                    errors: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        return self._data("/edifact/acknowledge", {
            "edifact": edifact, "kind": kind, "acknowledged": acknowledged,
            "errors": errors or [],
        })

    def skeleton(self, *, message_type: Optional[str] = None, release: Optional[str] = None,
                 compiled_id: Optional[str] = None, compose: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {"compose": compose}
        if compiled_id is not None:
            body["compiled_id"] = compiled_id
        else:
            body["message_type"] = message_type
            body["release"] = release
        return self._data("/edifact/skeleton", body)


class Dashboard(_Resource):
    def kpis(self) -> Dict[str, Any]:
        return self._data("/dashboard/kpis", {})


def _post_with_headers(t: Transport, path: str, body: Dict[str, Any],
                       headers: Dict[str, str]) -> Dict[str, Any]:
    url = t.base_url + "/" + path.lstrip("/")
    resp = t._session.post(url, json=body, timeout=t.timeout, verify=t.verify_tls,
                           headers=headers)
    from ._http import _parse
    return _parse(resp)
