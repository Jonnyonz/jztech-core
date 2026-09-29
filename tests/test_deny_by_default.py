import pytest
from fastapi import APIRouter, Depends, FastAPI

from jztech_core.deny_by_default import assert_all_routes_protected


async def get_current_user():
    return {"id": 1, "rol": "admin"}


def require_role(roles):
    # Mismo patron que las apps: una funcion nueva por ruta que depende de la de sesion.
    async def role_checker(user: dict = Depends(get_current_user)):
        return user

    return role_checker


def _app_with(route_setup):
    app = FastAPI()
    route_setup(app)
    return app


def test_direct_dependency_counts_as_protected():
    def setup(app):
        @app.get("/privado")
        async def privado(user=Depends(get_current_user)):
            return {}

    assert_all_routes_protected(_app_with(setup), public_paths=[], auth_dependency=get_current_user)


def test_nested_role_dependency_counts_as_protected():
    def setup(app):
        @app.get("/admin")
        async def admin(user=Depends(require_role(["admin"]))):
            return {}

    assert_all_routes_protected(_app_with(setup), public_paths=[], auth_dependency=get_current_user)


def test_router_level_dependency_counts_as_protected():
    def setup(app):
        router = APIRouter(dependencies=[Depends(get_current_user)])

        @router.get("/via-router")
        async def via_router():
            return {}

        app.include_router(router)

    assert_all_routes_protected(_app_with(setup), public_paths=[], auth_dependency=get_current_user)


def test_open_route_fails():
    def setup(app):
        @app.get("/abierta")
        async def abierta():
            return {}

    with pytest.raises(AssertionError, match="/abierta"):
        assert_all_routes_protected(_app_with(setup), public_paths=[], auth_dependency=get_current_user)


def test_explicit_public_route_passes():
    def setup(app):
        @app.get("/login")
        async def login():
            return {}

    # Las rutas de documentacion de FastAPI tambien son rutas sin sesion: se listan igual.
    public = ["/login", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"]
    assert_all_routes_protected(_app_with(setup), public_paths=public, auth_dependency=get_current_user)
