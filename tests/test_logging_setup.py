import json
import logging
import sys

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from jztech_core.logging_setup import JsonFormatter, install_generic_error_handler


async def _falla(request):
    raise RuntimeError("detalle interno: password=super-secreta")


def _app(**kwargs):
    app = Starlette(routes=[Route("/falla", _falla)])
    install_generic_error_handler(app, "test_app", **kwargs)
    return app


def test_generic_handler_hides_detail_and_logs_it(caplog):
    client = TestClient(_app(), raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="test_app"):
        resp = client.get("/falla")
    assert resp.status_code == 500
    assert resp.json() == {"msg": "Error interno del servidor."}
    assert "super-secreta" not in resp.text
    # El detalle si queda en el log del servidor, con traceback.
    assert any(r.exc_info and "super-secreta" in str(r.exc_info[1]) for r in caplog.records)


def test_generic_handler_field_is_configurable():
    client = TestClient(_app(field="detail"), raise_server_exceptions=False)
    resp = client.get("/falla")
    assert resp.json() == {"detail": "Error interno del servidor."}


def test_json_formatter_includes_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.getLogger("x").makeRecord("x", logging.ERROR, __file__, 1, "fallo %s", ("a",), exc_info=sys.exc_info())
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == "ERROR"
    assert payload["msg"] == "fallo a"
    assert "ValueError: boom" in payload["exc"]
