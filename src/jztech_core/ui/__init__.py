"""Sistema visual comun de JZTech Suite: sirve `suite.css` (tokens claro/oscuro, botones, badges) desde el core.

Uso en la app (FastAPI o Starlette)::

    from jztech_core.ui import montar_ui
    SUITE_CSS = montar_ui(app)          # -> "/jz/suite.css?v=0.2.0"

y en el HTML, antes del <style> propio::

    <link rel="stylesheet" href="/jz/suite.css?v=0.2.0">

La ruta es publica (CSS sin datos): agregarla a `public_paths` del test de denegar por defecto.
El `?v=` cambia con cada version del core, por eso la respuesta se puede cachear como inmutable.
"""
from importlib import resources

from starlette.responses import Response

CACHE_CONTROL = "public, max-age=31536000, immutable"


def suite_css() -> str:
    """Contenido de suite.css tal como viene en el paquete."""
    return resources.files(__package__).joinpath("suite.css").read_text(encoding="utf-8")


def montar_ui(app, prefijo: str = "/jz") -> str:
    """Agrega `GET {prefijo}/suite.css` a la app y devuelve el href versionado para el <link>."""
    from jztech_core import __version__

    css = suite_css()
    ruta = f"{prefijo.rstrip('/')}/suite.css"

    async def _suite(request):
        return Response(css, media_type="text/css; charset=utf-8", headers={"Cache-Control": CACHE_CONTROL})

    app.add_route(ruta, _suite, methods=["GET"], name="jztech_suite_css")
    return f"{ruta}?v={__version__}"
