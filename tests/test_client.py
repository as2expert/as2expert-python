"""Unit tests for the AS2Expert Python client (HTTP mocked at the session level)."""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from as2expert import AS2ExpertClient, AuthError, ValidationError, verify_signature, sign_payload  # noqa: E402


class _Resp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.ok = 200 <= status_code < 300
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class _FakeSession:
    """Records requests and returns queued responses."""
    def __init__(self):
        self.headers = {}
        self.calls = []
        self._queue = []

    def queue(self, status_code, payload):
        self._queue.append(_Resp(status_code, payload))

    def post(self, url, json=None, timeout=None, verify=None, headers=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self._queue.pop(0)

    def close(self):
        pass


def _client():
    s = _FakeSession()
    c = AS2ExpertClient(token="tok", base_url="https://x/api/v1", session=s)
    return c, s


def test_requires_token():
    try:
        AS2ExpertClient(token="", base_url="https://x/api/v1")
        assert False
    except ValueError:
        pass


def test_environment_preset():
    c = AS2ExpertClient(token="t", environment="free")
    assert c.base_url == "https://free.as2expert.com/api/v1"


def test_send_message_base64_and_path():
    c, s = _client()
    s.queue(200, {"status": "success", "msg": "ok", "data": {"message_id": "M-1"}})
    out = c.messages.send(partner="140", subject="Order", file_name="o.edi",
                          file_content=b"UNB+...")
    assert out["message_id"] == "M-1"
    call = s.calls[0]
    assert call["url"].endswith("/api/v1/messages/send")
    assert call["json"]["partner"] == "140" and call["json"]["subject"] == "Order"
    assert call["json"]["file_content"] == base64.b64encode(b"UNB+...").decode()


def test_list_returns_data_array():
    c, s = _client()
    s.queue(200, {"status": "success", "data": [{"id": 1}, {"id": 2}], "total": 2})
    msgs = c.messages.list(limit=10)
    assert [m["id"] for m in msgs] == [1, 2]
    assert s.calls[0]["json"]["limit"] == 10


def test_download_decodes_base64():
    c, s = _client()
    s.queue(200, {"status": "success", "data": {"content_b64": base64.b64encode(b"HELLO").decode()}})
    assert c.messages.download(7) == b"HELLO"


def test_auth_error_mapping():
    c, s = _client()
    s.queue(401, {"status": "error", "msg": "bad token"})
    try:
        c.partners.list()
        assert False
    except AuthError as e:
        assert e.status_code == 401 and "bad token" in str(e)


def test_validation_error_with_fields():
    c, s = _client()
    s.queue(422, {"status": "error", "msg": "invalid", "fields": [{"path": "partner"}]})
    try:
        c.business_documents.create({"type": "purchase_order"})
        assert False
    except ValidationError as e:
        assert e.fields and e.fields[0]["path"] == "partner"


def test_edifact_convert_body():
    c, s = _client()
    s.queue(200, {"status": "success", "data": {"format": "json", "content": "{}"}})
    out = c.edifact.convert(edifact="UNB...", format="json")
    assert out["format"] == "json"
    assert s.calls[0]["json"] == {"format": "json", "sequence": 1, "edifact": "UNB..."}


def test_webhook_signature_roundtrip():
    sig = sign_payload("secret-0123456789abcdef", 1000, '{"a":1}')
    assert verify_signature("secret-0123456789abcdef", 1000, '{"a":1}', sig, now=1000)
    assert not verify_signature("secret-0123456789abcdef", 1000, '{"a":1}', sig, now=99999)  # skew
    assert not verify_signature("secret-0123456789abcdef", 1000, '{"a":2}', sig, now=1000)   # tamper


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = 0
    for fn in fns:
        try:
            fn(); print("ok  ", fn.__name__)
        except AssertionError as e:
            bad += 1; print("FAIL", fn.__name__, e)
    print("\n%d/%d passed" % (len(fns) - bad, len(fns)))
    sys.exit(1 if bad else 0)
