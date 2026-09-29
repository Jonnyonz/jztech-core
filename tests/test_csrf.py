import pytest
from starlette.exceptions import HTTPException
from starlette.requests import Request

from jztech_core.csrf import enforce_csrf, generate_csrf_token, verify_csrf_token


def test_generate_and_verify_roundtrip():
    token = generate_csrf_token("secreto", "usuario-1")
    assert verify_csrf_token("secreto", "usuario-1", token)
    assert not verify_csrf_token("secreto", "otro-usuario", token)
    assert not verify_csrf_token("otro-secreto", "usuario-1", token)


def _make_request(method: str, headers: dict[str, str] | None = None) -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": method,
        "headers": raw_headers,
        "path": "/",
        "query_string": b"",
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_enforce_csrf_allows_safe_methods_without_token():
    request = _make_request("GET")
    await enforce_csrf(request, "secreto", "usuario-1")


@pytest.mark.asyncio
async def test_enforce_csrf_rejects_unsafe_method_without_token():
    request = _make_request("POST")
    with pytest.raises(HTTPException) as exc_info:
        await enforce_csrf(request, "secreto", "usuario-1")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_enforce_csrf_accepts_valid_header_token():
    token = generate_csrf_token("secreto", "usuario-1")
    request = _make_request("POST", {"X-CSRF-Token": token})
    await enforce_csrf(request, "secreto", "usuario-1")
