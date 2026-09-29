from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from jztech_core.security_headers import SecurityHeadersMiddleware


async def _endpoint(request):
    return PlainTextResponse("ok")


def _make_app(**middleware_kwargs):
    app = Starlette(routes=[Route("/", _endpoint)])
    app.add_middleware(SecurityHeadersMiddleware, **middleware_kwargs)
    return app


def test_default_headers_present():
    client = TestClient(_make_app())
    resp = client.get("/")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert "content-security-policy" in resp.headers


def test_csp_can_be_disabled():
    client = TestClient(_make_app(csp=None))
    resp = client.get("/")
    assert "content-security-policy" not in resp.headers


def test_permissions_policy_default_denies_geolocation():
    client = TestClient(_make_app())
    resp = client.get("/")
    assert resp.headers["permissions-policy"] == "geolocation=(), microphone=(), camera=()"


def test_permissions_policy_can_allow_geolocation():
    client = TestClient(_make_app(permissions_policy="geolocation=(self), camera=()"))
    resp = client.get("/")
    assert resp.headers["permissions-policy"] == "geolocation=(self), camera=()"


def test_permissions_policy_can_be_disabled():
    client = TestClient(_make_app(permissions_policy=None))
    resp = client.get("/")
    assert "permissions-policy" not in resp.headers
