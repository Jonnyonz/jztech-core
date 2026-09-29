"""Migraciones SQL versionadas (ver seccion 3.2). Sin `except: pass` (regla 6
de la hoja de ruta): cualquier fallo de una migracion se propaga tal cual y
frena el arranque de la app, no se silencia."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class _Pool(Protocol):
    def acquire(self) -> Any: ...


CREATE_VERSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def apply_migrations(pool: _Pool, migrations_dir: str | Path) -> list[int]:
    """Aplica los archivos '<version>_*.sql' de migrations_dir en orden
    numerico, uno por transaccion, que todavia no figuren en schema_version.
    Devuelve la lista de versiones recien aplicadas."""
    directory = Path(migrations_dir)
    files = sorted(directory.glob("*.sql"), key=lambda p: int(p.name.split("_", 1)[0]))

    newly_applied: list[int] = []
    async with pool.acquire() as conn:
        await conn.execute(CREATE_VERSION_TABLE_SQL)
        applied_rows = await conn.fetch("SELECT version FROM schema_version")
        applied = {row["version"] for row in applied_rows}

        for sql_file in files:
            version = int(sql_file.name.split("_", 1)[0])
            if version in applied:
                continue
            sql = sql_file.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute("INSERT INTO schema_version (version) VALUES ($1)", version)
            newly_applied.append(version)

    return newly_applied
