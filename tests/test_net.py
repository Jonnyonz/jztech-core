from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from jztech_core.net import parse_networks, real_ip


def test_parse_networks():
    nets = parse_networks("127.0.0.1/32, ::1/128 ,172.16.0.0/12")
    assert len(nets) == 3


def _make_app():
    trusted = parse_networks("127.0.0.1/32,::1/128")

    async def endpoint(request: Request) -> PlainTextResponse:
        return PlainTextResponse(real_ip(request, trusted))

    return Starlette(routes=[Route("/", endpoint)])


def test_real_ip_ignores_forwarded_for_from_untrusted_origin():
    app = _make_app()
    client = TestClient(app, client=("203.0.113.9", 12345))
    resp = client.get("/", headers={"x-forwarded-for": "10.0.0.1"})
    assert resp.text == "203.0.113.9"


def test_real_ip_trusts_forwarded_for_from_trusted_proxy():
    app = _make_app()
    client = TestClient(app, client=("127.0.0.1", 12345))
    resp = client.get("/", headers={"x-forwarded-for": "203.0.113.9, 10.0.0.1"})
    assert resp.text == "203.0.113.9"
