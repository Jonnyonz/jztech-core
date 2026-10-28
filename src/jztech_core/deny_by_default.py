"""Denegar por defecto, con prueba automatica (ver seccion 3.3).

assert_all_routes_protected() esta pensado para usarse en un test de pytest de
cada repo, recorriendo app.routes: es lo que hubiera atrapado los endpoints
sin autenticacion de la Fase 1.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable


def _depends_on(dependant: Any, target: Callable[..., Any]) -> bool:
    """True si target aparece en el arbol de dependencias, a cualquier nivel.
    Hace falta recorrerlo entero: un chequeo de rol tipo require_role(...)
    devuelve una funcion distinta por ruta que a su vez depende de la de sesion."""
    for dep in getattr(dependant, "dependencies", []):
        if getattr(dep, "call", None) is target or _depends_on(dep, target):
            return True
    return False


def _effective_routes(routes: Iterable[Any]) -> Iterable[tuple[str, Any]]:
    """(path, dependant) de cada ruta, entrando en los routers incluidos.
    FastAPI >= 0.141 ya no copia en app.routes las rutas de include_router(): las
    envuelve en un _IncludedRouter sin path, y arma a pedido (effective_candidates)
    el path y el dependant efectivos, con el prefijo y las dependencias del include.
    Sin recorrerlos, el chequeo solo veia las rutas definidas sobre la app."""
    for route in routes:
        candidatos = getattr(route, "effective_candidates", None)
        if callable(candidatos):
            yield from _effective_routes(candidatos())
            continue
        path = getattr(route, "path", None)
        if path is not None:
            yield path, getattr(route, "dependant", None)


def assert_all_routes_protected(app: Any, public_paths: Iterable[str], auth_dependency: Callable[..., Any]) -> None:
    """Falla (AssertionError) si alguna ruta de la app (incluidas las de los
    routers incluidos) no esta en public_paths ni depende, directa o
    indirectamente, de auth_dependency (dependencia de FastAPI usada para exigir
    sesion). Las dependencias de router, de include_router() y de app cuentan.
    Ignora rutas sin atributo `path` (montajes estaticos, etc.) y las que no
    tengan `.dependant` (no son endpoints de FastAPI)."""
    public = set(public_paths)
    unprotected: list[str] = []
    for path, dependant in _effective_routes(app.routes):
        if path in public or dependant is None:
            continue
        if not _depends_on(dependant, auth_dependency):
            unprotected.append(path)
    if unprotected:
        raise AssertionError(
            "Rutas sin autenticacion ni marca de publica explicita: " + ", ".join(sorted(set(unprotected)))
        )
