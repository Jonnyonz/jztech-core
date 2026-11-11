from starlette.applications import Starlette
from starlette.testclient import TestClient

import jztech_core
from jztech_core.ui import montar_ui, suite_css


def test_montar_ui_sirve_el_css_con_cache_inmutable():
    app = Starlette()
    href = montar_ui(app)
    assert href == f"/jz/suite.css?v={jztech_core.__version__}"

    r = TestClient(app).get("/jz/suite.css")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/css")
    assert "immutable" in r.headers["cache-control"]
    assert r.text == suite_css()


def test_suite_css_trae_tokens_claro_oscuro_y_componentes():
    css = suite_css()
    assert ":root {" in css and '[data-theme="dark"]' in css
    for token in ("--ac:", "--ok:", "--dg:", "--wn:", "--ink:", "--f:", "--m:"):
        assert token in css
    # alias del tema anterior (JS con estilos en linea) y componentes compartidos
    for regla in ("--accent: var(--ac)", "--bg-page: var(--bg)", ".btn {", ".btn-p {", ".badge {", ".b-ok, .badge-success"):
        assert regla in css


def test_prefijo_personalizado():
    app = Starlette()
    href = montar_ui(app, prefijo="/estaticos/")
    assert href.startswith("/estaticos/suite.css?v=")
    assert TestClient(app).get("/estaticos/suite.css").status_code == 200
