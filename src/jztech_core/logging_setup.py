"""Logs estructurados a stdout y manejo de errores generico hacia el cliente
(ver regla 6 de la hoja de ruta: nunca devolver str(e) al cliente)."""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def install_generic_error_handler(app: Any, logger_name: str = "app") -> None:
    """Registra un exception handler que loguea el detalle completo (con
    traceback) en el servidor y devuelve siempre un mensaje generico al
    cliente. Nunca expone str(exc) en la respuesta HTTP."""
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    logger = logging.getLogger(logger_name)

    @app.exception_handler(Exception)
    async def _generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no manejado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"msg": "Error interno del servidor."})
