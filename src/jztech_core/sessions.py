"""Sesiones opacas en base (ver seccion 3.4: decision confirmada 2026-09-29).

Token aleatorio entregado al cliente en una cookie HttpOnly+Secure+SameSite=
Strict; solo se guarda su hash SHA-256 en la base, nunca el token en claro.
Revocable de verdad (delete de la fila), a diferencia de JWT.

Requiere un pool tipo asyncpg.Pool (duck-typed: .acquire() como context
manager async que da una conexion con .execute()/.fetchrow()/.fetch()).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

SESSION_COOKIE_NAME = "session_token"
DEFAULT_TTL = timedelta(days=7)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jztech_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS jztech_sessions_user_id_idx ON jztech_sessions (user_id);
"""


class _Pool(Protocol):
    def acquire(self) -> Any: ...


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(pool: _Pool, user_id: str, ttl: timedelta = DEFAULT_TTL) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + ttl
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO jztech_sessions (token_hash, user_id, expires_at) VALUES ($1, $2, $3)",
            _hash(token),
            user_id,
            expires_at,
        )
    return token


async def verify_session(pool: _Pool, token: str) -> str | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id FROM jztech_sessions WHERE token_hash = $1 AND expires_at > now()",
            _hash(token),
        )
    return row["user_id"] if row else None


async def revoke_session(pool: _Pool, token: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM jztech_sessions WHERE token_hash = $1", _hash(token))


async def revoke_all_sessions_for_user(pool: _Pool, user_id: str) -> None:
    """Usar en logout-de-todos-lados, cambio de clave o desactivacion de usuario."""
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM jztech_sessions WHERE user_id = $1", user_id)


def set_session_cookie(response: Any, token: str, ttl: timedelta = DEFAULT_TTL, secure: bool = True) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=int(ttl.total_seconds()),
    )


def clear_session_cookie(response: Any, secure: bool = True) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, httponly=True, secure=secure, samesite="strict")
