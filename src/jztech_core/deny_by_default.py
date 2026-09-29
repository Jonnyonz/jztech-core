"""Denegar por defecto, con prueba automatica (ver seccion 3.3).

assert_all_routes_protected() esta pensado para usarse en un test de pytest de
cada repo, recorriendo app.routes: es lo que hubiera atrapado los endpoints
sin autenticacion de la Fase 1.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable


def assert_all_routes_protected(app: Any, public_paths: Iterable[str], auth_dependency: Callable[..., Any]) -> None:
    """Falla (AssertionError) si alguna ruta de app.routes no esta en
    public_paths ni depende de auth_dependency (dependencia de FastAPI usada
    para exigir sesion). Ignora rutas sin atributo `path` (montajes estaticos,
    etc.) y las que no tengan `.dependant` (no son endpoints de FastAPI)."""
    public = set(public_paths)
    unprotected: list[str] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        if path is None or path in public:
            continue
        dependant = getattr(route, "dependant", None)
        if dependant is None:
            continue
        deps = getattr(dependant, "dependencies", [])
        call_names = {d.call for d in deps if getattr(d, "call", None) is not None}
        if auth_dependency not in call_names:
            unprotected.append(path)
    if unprotected:
        raise AssertionError(
            "Rutas sin autenticacion ni marca de publica explicita: " + ", ".join(sorted(set(unprotected)))
        )
