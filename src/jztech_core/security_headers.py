"""Cabeceras de seguridad + CSP como middleware unico (ver seccion 3.2)."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

DEFAULT_CSP = "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega cabeceras de seguridad estandar y CSP a toda respuesta.

    csp=None desactiva la cabecera CSP (por si una app necesita definir la suya
    con mas detalle); hsts=False la desactiva (util en desarrollo sin HTTPS).
    """

    def __init__(self, app: ASGIApp, csp: str | None = DEFAULT_CSP, hsts: bool = True) -> None:
        super().__init__(app)
        self.csp = csp
        self.hsts = hsts

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if self.csp:
            response.headers["Content-Security-Policy"] = self.csp
        if self.hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response
