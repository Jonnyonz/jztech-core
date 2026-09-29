# jztech-core

Libreria de seguridad e infraestructura compartida para las apps de JZTech
(Tracker360, JZTravell, JZPass y el futuro ERP). Evita que cada app
reimplemente -y rompa- la misma seguridad. Ver el diseño completo en la
seccion 3.2 de `JZTech_Estado_y_Hoja_de_Ruta.md` del repo `JZTechSuite`.

## Contenido

- `jztech_core.passwords` — hash de claves con Argon2id, migracion desde bcrypt/Argon2-passlib.
- `jztech_core.sessions` — sesiones opacas en base (cookie HttpOnly+Secure+SameSite=Strict), revocables.
- `jztech_core.csrf` — token CSRF ligado al usuario de la sesion.
- `jztech_core.security_headers` — middleware unico de cabeceras de seguridad + CSP.
- `jztech_core.net` — IP real, confiando en `X-Forwarded-For` solo desde proxies de confianza.
- `jztech_core.deny_by_default` — helper de test que recorre todas las rutas de una app FastAPI y falla si alguna no tiene autenticacion ni esta marcada como publica.
- `jztech_core.migrations` — migraciones SQL versionadas contra una tabla `schema_version`.
- `jztech_core.logging_setup` — logging estructurado a stdout y manejador de errores generico (nunca expone `str(exc)` al cliente).
- `jztech_core.setup_flow` — comparacion segura del `SETUP_TOKEN` de configuracion inicial.

## Instalacion

Se distribuye como *wheel* adjunto a un release de GitHub, referenciado con
hash en el `requirements.txt` de cada app satelite (nunca por URL de git sin
hash):

```
jztech-core @ https://github.com/Jonnyonz/jztech-core/releases/download/v0.1.3/jztech_core-0.1.3-py3-none-any.whl --hash=sha256:82dee0100f06b072a54a166bf1ec93a66f8daf869cfb0b646a2177eebdd463ae
```

(el hash de cada release nuevo está en el `SHA256SUMS.txt` adjunto a ese release)

## Desarrollo

```bash
python -m venv .venv
. .venv/Scripts/activate  # o . .venv/bin/activate en Linux/Mac
pip install -e ".[dev]"
pytest
```

## Licencia

AGPLv3. Ver `LICENSE`. Los aportes requieren `Signed-off-by` (DCO), ver
`CONTRIBUTING.md`.
