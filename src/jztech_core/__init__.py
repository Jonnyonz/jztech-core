"""jztech_core: seguridad e infraestructura compartida para las apps de JZTech.

Ver JZTech_Estado_y_Hoja_de_Ruta.md, seccion 3.2, para el diseño y el plan de
migracion de cada repo satelite.
"""

from jztech_core.passwords import hash_password, needs_rehash, verify_legacy_password, verify_password
from jztech_core.net import parse_networks, real_ip
from jztech_core.security_headers import SecurityHeadersMiddleware
from jztech_core.sessions import (
    clear_session_cookie,
    create_session,
    revoke_all_sessions_for_user,
    revoke_session,
    set_session_cookie,
    verify_session,
)
from jztech_core.csrf import enforce_csrf, generate_csrf_token, verify_csrf_token
from jztech_core.deny_by_default import assert_all_routes_protected
from jztech_core.migrations import apply_migrations
from jztech_core.logging_setup import configure_logging, install_generic_error_handler
from jztech_core.setup_flow import verify_setup_token

__version__ = "0.1.5"

__all__ = [
    "hash_password",
    "verify_password",
    "verify_legacy_password",
    "needs_rehash",
    "parse_networks",
    "real_ip",
    "SecurityHeadersMiddleware",
    "create_session",
    "verify_session",
    "revoke_session",
    "revoke_all_sessions_for_user",
    "set_session_cookie",
    "clear_session_cookie",
    "generate_csrf_token",
    "verify_csrf_token",
    "enforce_csrf",
    "assert_all_routes_protected",
    "apply_migrations",
    "configure_logging",
    "install_generic_error_handler",
    "verify_setup_token",
]
