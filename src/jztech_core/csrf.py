"""CSRF ligado al usuario de la sesion, validado en POST/PUT/PATCH/DELETE
(ver seccion 3.2). Doble submit sin estado: el token es un HMAC del user_id
con la clave de la app, asi que no necesita guardarse en la base."""

from __future__ import annotations

import hashlib
import hmac

from starlette.exceptions import HTTPException
from starlette.requests import Request

CSRF_HEADER = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def generate_csrf_token(secret_key: str, user_id: str) -> str:
    return hmac.new(secret_key.encode("utf-8"), user_id.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_csrf_token(secret_key: str, user_id: str, token: str | None) -> bool:
    expected = generate_csrf_token(secret_key, user_id)
    return hmac.compare_digest(expected, token or "")


async def enforce_csrf(request: Request, secret_key: str, user_id: str) -> None:
    """Levanta HTTPException 403 si el metodo es inseguro y falta o no coincide
    el CSRF. Llamar despues de autenticar al usuario (user_id de la sesion)."""
    if request.method not in UNSAFE_METHODS:
        return
    token = request.headers.get(CSRF_HEADER)
    if not token and request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        form = await request.form()
        token = form.get(CSRF_FORM_FIELD)
    if not verify_csrf_token(secret_key, user_id, token):
        raise HTTPException(status_code=403, detail="CSRF invalido.")
