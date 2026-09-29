# jztech-core

Librería de seguridad e infraestructura compartida por las apps de **JZTech Suite**
(JZTravell, JZPass, Tracker360 y el futuro ERP). Existe para que cada app no reimplemente, y
rompa, la misma seguridad: hash de claves, sesiones, CSRF, cabeceras, IP real, denegar por
defecto, migraciones y logging.

Pocas dependencias (`argon2-cffi` y `starlette`), sin framework propio: se integra en apps
FastAPI/Starlette existentes módulo por módulo.

- [Módulos](#módulos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Compatibilidad](#compatibilidad)
- [Desarrollo](#desarrollo)
- [Publicar una versión](#publicar-una-versión)
- [Licencia](#licencia)

---

## Módulos

| Módulo | Qué resuelve |
|---|---|
| `passwords` | Hash de claves con **Argon2id** (parámetros por entorno) y migración transparente desde bcrypt o Argon2 de passlib. |
| `sessions` | **Sesiones opacas en base**: token aleatorio en cookie `HttpOnly`+`Secure`+`SameSite=Strict`; en la base solo el hash SHA-256. Revocables. |
| `csrf` | Token CSRF firmado con HMAC y **atado al usuario** de la sesión. |
| `security_headers` | Middleware único de cabeceras: CSP, `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`, HSTS. |
| `net` | **IP real** del cliente: `X-Forwarded-For` solo se acepta si la conexión viene de un proxy de confianza. |
| `deny_by_default` | Helper de test: recorre todas las rutas de una app FastAPI y falla si alguna no exige sesión ni está marcada como pública. |
| `migrations` | Migraciones SQL versionadas (`<versión>_nombre.sql`) contra una tabla `schema_version`. |
| `logging_setup` | Logs JSON a stdout y manejador de errores genérico (el detalle nunca llega al cliente). |
| `setup_flow` | Comparación en tiempo constante del `SETUP_TOKEN` de configuración inicial. |

---

## Instalación

Se distribuye como *wheel* adjunto a cada release de GitHub, referenciado **con hash** en el
`requirements.txt` de la app (nunca por URL de git sin hash):

```
jztech-core @ https://github.com/Jonnyonz/jztech-core/releases/download/v0.1.5/jztech_core-0.1.5-py3-none-any.whl --hash=sha256:86fe7da6ce7ffaf77c6111592faead17f9a778012161594cab9651c09961f715
```

El hash de cada versión está en el `SHA256SUMS.txt` adjunto a su release.

> Una línea con hash activa el modo `--require-hashes` de pip para **todo** el archivo: el
> `requirements.txt` de la app tiene que tener hashes en todas sus dependencias. Lo más simple
> es mantener un `requirements.in` y generar el lockfile con
> `pip-compile --generate-hashes`, **siempre en Linux** (en Windows se resuelven dependencias
> propias de Windows y el build de Docker falla).

---

## Uso

### Claves

```python
from jztech_core.passwords import hash_password, verify_password, verify_legacy_password, needs_rehash

stored = hash_password("clave")                 # "$argon2id$..."
ok = verify_password("clave", stored)

# Migración: si el hash guardado es bcrypt (o Argon2 de passlib), validarlo con
# verify_legacy_password y, si es correcto, guardar hash_password(clave) en su lugar.
if not stored.startswith("$argon2") or needs_rehash(stored):
    ...
```

Parámetros por entorno: `ARGON2_TIME_COST` (2), `ARGON2_MEMORY_COST_KIB` (19456 = 19 MiB),
`ARGON2_PARALLELISM` (1), el mínimo recomendado por OWASP. En equipos con muy poca RAM se
puede bajar la memoria. Para validar hashes bcrypt la app tiene que tener `bcrypt` instalado.

### Sesiones

```python
from jztech_core import sessions

# Una vez, al crear el esquema:
await conn.execute(sessions.CREATE_TABLE_SQL)          # tabla jztech_sessions

token = await sessions.create_session(pool, user_id)   # TTL por defecto: 7 días
sessions.set_session_cookie(response, token)
user_id = await sessions.verify_session(pool, token)   # None si no existe o venció
await sessions.revoke_session(pool, token)             # logout
await sessions.revoke_all_sessions_for_user(pool, user_id)   # cambio de clave, baja
```

`pool` es un `asyncpg.Pool` (o cualquier objeto con la misma interfaz).

### CSRF

```python
from jztech_core.csrf import generate_csrf_token, enforce_csrf

token = generate_csrf_token(SECRET, user_id)    # entregarlo al frontend
await enforce_csrf(request, SECRET, user_id)    # 403 si un POST/PUT/PATCH/DELETE no lo trae
```

El frontend lo manda en la cabecera `X-CSRF-Token` (o en el campo `csrf_token` de un
formulario). Como está atado al usuario, un token de otra sesión no sirve.

### Cabeceras de seguridad

```python
from jztech_core.security_headers import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    csp="default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'",
    permissions_policy="geolocation=(self), microphone=(), camera=()",  # si la app usa GPS
    hsts=True,   # solo se envía si la app ve la conexión como https
)
```

Por defecto: CSP estricta y `Permissions-Policy` con geolocalización, micrófono y cámara
bloqueados. `csp=None` o `permissions_policy=None` desactivan esa cabecera. Agregarlo después
de los otros middlewares para que quede por fuera y cubra también sus respuestas de error.

### IP real

```python
from jztech_core.net import parse_networks, real_ip

TRUSTED = parse_networks(os.getenv("TRUSTED_PROXIES", "127.0.0.1/32,::1/128"))
ip = real_ip(request, TRUSTED)
```

Si la conexión no viene de un proxy de confianza, devuelve la IP de la conexión e ignora el
encabezado. Si viene de uno, recorre `X-Forwarded-For` de derecha a izquierda y devuelve el
primer salto que no sea un proxy de confianza (soporta varios proxies en serie).

### Denegar por defecto (en los tests de la app)

```python
from jztech_core.deny_by_default import assert_all_routes_protected
from app.main import app
from app.database import get_current_user

def test_todas_las_rutas_exigen_sesion():
    assert_all_routes_protected(
        app,
        public_paths=["/api/login", "/api/setup/status", "/openapi.json", "/docs", "/redoc"],
        auth_dependency=get_current_user,
    )
```

Cuenta como protegida toda ruta que dependa de `auth_dependency` a cualquier nivel (también a
través de un chequeo de rol que dependa de ella, o de dependencias de router). La lista de
públicas es por path.

### Migraciones

```python
from jztech_core.migrations import apply_migrations

applied = await apply_migrations(pool, "migrations/")   # 001_inicial.sql, 002_indices.sql, ...
```

Cada archivo se aplica una sola vez, en orden numérico y en su propia transacción. Si una
falla, el error se propaga y la app no arranca (nunca se silencia).

### Logging y errores

```python
from jztech_core.logging_setup import configure_logging, install_generic_error_handler

configure_logging()                               # JSON a stdout
install_generic_error_handler(app, "mi_app")      # 500 con {"msg": "Error interno..."}; el detalle, al log
# field="detail" si el frontend lee el formato de FastAPI: {"detail": "..."}
```

### Configuración inicial

```python
from jztech_core.setup_flow import verify_setup_token

if not verify_setup_token(os.getenv("SETUP_TOKEN", ""), data.token):
    raise HTTPException(403)
```

Con `SETUP_TOKEN` vacío siempre devuelve `False` (la configuración inicial queda deshabilitada).

---

## Compatibilidad

| | Probado |
|---|---|
| Python | 3.11, 3.12, 3.13 (CI) |
| Starlette | 0.27.0 (con FastAPI 0.104.1) y 1.7.0 (con FastAPI 0.141.1) |

El piso de Starlette es 0.27 porque lo usa JZTravell. Cualquier API de Starlette nueva que se
use en la librería tiene que probarse contra esa versión.

---

## Desarrollo

```bash
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

---

## Publicar una versión

1. Subir la versión en `pyproject.toml` y en `src/jztech_core/__init__.py`.
2. Commit, tag `vX.Y.Z` y push del tag: el workflow `release.yml` construye el wheel y lo
   publica con su `SHA256SUMS.txt`.
3. Bajar el wheel y verificar su SHA-256 contra `SHA256SUMS.txt`.
4. Actualizar la línea de [Instalación](#instalación) de este README.
5. En cada app: cambiar la URL en su `requirements.in` y regenerar el lockfile en Linux con
   `pip-compile --generate-hashes --upgrade-package jztech-core`.

---

## Licencia

AGPLv3. Ver `LICENSE`. Los aportes requieren `Signed-off-by` (DCO), ver `CONTRIBUTING.md`.
