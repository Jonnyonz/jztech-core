"""Flujo de configuracion inicial con SETUP_TOKEN (ver seccion 3.2: 'ya existe
en los tres [repos]; unificarlo').

Solo el primitivo de comparacion del token: si la app necesita setup (por
ejemplo, tabla de usuarios vacia) es logica especifica de cada repo, jztech_core
no asume el esquema de datos de cada app.
"""

from __future__ import annotations

import hmac


def verify_setup_token(configured_token: str, provided_token: str | None) -> bool:
    if not configured_token:
        return False
    return hmac.compare_digest(configured_token, (provided_token or "").strip())
