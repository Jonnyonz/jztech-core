"""Hash de claves con Argon2id (ver JZTech_Estado_y_Hoja_de_Ruta.md, seccion 3.4).

Parametros configurables por entorno; el punto de partida es el minimo
recomendado por OWASP (19 MiB, t=2, p=1). Es intensivo en memoria: ajustar en
equipos chicos con ARGON2_MEMORY_COST_KIB.
"""

from __future__ import annotations

import os

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

_ph = PasswordHasher(
    time_cost=int(os.environ.get("ARGON2_TIME_COST", "2")),
    memory_cost=int(os.environ.get("ARGON2_MEMORY_COST_KIB", "19456")),
    parallelism=int(os.environ.get("ARGON2_PARALLELISM", "1")),
)


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        _ph.verify(stored_hash, password)
    except (VerifyMismatchError, InvalidHash):
        return False
    return True


def needs_rehash(stored_hash: str) -> bool:
    return _ph.check_needs_rehash(stored_hash)


def verify_legacy_password(password: str, stored_hash: str) -> bool:
    """Verifica contra hashes de esquemas viejos (bcrypt, o Argon2 via passlib),
    para el flujo de migracion: si esto da True, rehashear con hash_password()
    y guardar el resultado. No fuerza reset masivo de claves.

    Requiere el paquete `bcrypt` instalado en la app que llama si hay hashes
    bcrypt en su base (no es una dependencia de jztech_core).
    """
    if stored_hash.startswith("$argon2"):
        # Formato Argon2 (via argon2-cffi o via passlib): mismo formato PHC,
        # PasswordHasher.verify lo entiende igual.
        return verify_password(password, stored_hash)
    if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
        import bcrypt

        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    return False
