# as2expert (Python)

Official Python client for the **AS2Expert** REST API — send and receive AS2/EDI
messages, manage trading partners, certificates and stations, drive Business
Documents, and validate/convert **EDIFACT**.

- Synchronous, `requests`-based, no heavy dependencies.
- Typed errors, automatic retries on `429`/`5xx`, HMAC webhook verification.
- Configurable host: point it at `free`, `b2b`, or any self-hosted deployment.

```bash
pip install as2expert
```

## Quick start

```python
from as2expert import AS2ExpertClient

client = AS2ExpertClient(token="YOUR_API_TOKEN", environment="free")
# or an explicit host:
# client = AS2ExpertClient(token="...", base_url="https://your-host/api/v1")

# Send an EDI file to a partner
client.messages.send(
    partner="140",
    subject="Order 4711",
    file_name="order.edi",
    file_content=open("order.edi", "rb").read(),   # bytes or str; base64 is handled
)

# List and download inbound messages
for msg in client.messages.list(limit=20):
    print(msg["id"], msg.get("asunto"))
    data = client.messages.download(msg["id"])     # -> bytes
```

Every method maps to one POST call (the API is POST-only). Collection methods
(`.list()`) return the `data` array; item and action methods return the `data`
object.

## Authentication

Create an API token in the AS2Expert portal (API section) and pass it as `token`.
The client sends it as `Authorization: Bearer <token>`. Tokens carry scopes
(`read`, `write`); a read-only token will get a `403` on writes, surfaced as
`AuthError`.

## Resources

| Namespace | Highlights |
|-----------|-----------|
| `client.messages` | `list`, `get`, `download`, `send`, `mark_read`/`mark_unread`, `move`, `delete`, `changes`, `files`, `export` |
| `client.partners` | `list`, `get`, `create` |
| `client.certificates` | `list`, `get`, `create` |
| `client.stations` | `list`, `get`, `stats`, `create` |
| `client.webhooks` | `configure`, `get`, `test`, `logs` |
| `client.business_documents` | `create` (with `Idempotency-Key`), `get`, `diagnostics` |
| `client.edifact` | `analyze`, `validate`, `convert`, `acknowledge`, `skeleton` |
| `client.dashboard` | `kpis` |

### EDIFACT

```python
# Parse + validate + translate an interchange to JSON (or "xml"/"text")
out = client.edifact.convert(edifact=raw_edi, format="json")
print(out["filename"], out["content"])

# Build a functional acknowledgement (CONTRL / APERAK)
ack = client.edifact.acknowledge(raw_edi)
print(ack["kind"], ack["control_reference"])
```

## Errors

All failures raise a subclass of `As2ExpertError`, each carrying `status_code`,
`message`, and optional `code`/`payload`:

| Exception | When |
|-----------|------|
| `AuthError` | `401` / `403` |
| `ValidationError` | `400` / `422` (see `.fields`) |
| `NotFoundError` | `404` |
| `RateLimitError` | `429` (see `.retry_after`) |
| `ServerError` | `5xx` |
| `TransportError` | network/timeout, no HTTP status |

```python
from as2expert import As2ExpertError, ValidationError

try:
    client.business_documents.create(doc)
except ValidationError as e:
    print("bad document:", e.fields)
except As2ExpertError as e:
    print(e.status_code, e)
```

## Webhooks

AS2Expert signs deliveries with HMAC-SHA256 over `"<timestamp>.<body>"`, sent in
`X-AS2Expert-Timestamp` and `X-AS2Expert-Signature: sha256=<hex>`. Verify before
trusting a payload:

```python
from as2expert import verify_signature

ok = verify_signature(
    secret=WEBHOOK_SECRET,
    timestamp=request.headers["X-AS2Expert-Timestamp"],
    body=request.get_data(as_text=True),   # the exact raw body
    signature=request.headers["X-AS2Expert-Signature"],
)
if not ok:
    abort(400)
```

## Configuration

`AS2ExpertClient(token, *, base_url=None, environment=None, timeout=30,
verify_tls=True, max_retries=2, session=None, user_agent=None)`

- Pass **either** `environment` (`"free"` / `"b2b"`) **or** `base_url`.
- `session` lets you inject a preconfigured `requests.Session` (proxies, custom TLS).
- The client is a context manager: `with AS2ExpertClient(...) as client: ...`.

## Development

```bash
python3 tests/test_client.py     # mocked unit tests (no network)
```

## License

Apache-2.0 — see [LICENSE](LICENSE).
