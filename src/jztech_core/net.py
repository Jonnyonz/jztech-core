"""IP real solo desde proxies de confianza (ver seccion 3.2 / 3.5 de la hoja de
ruta: hoy duplicado en Tracker360, JZTravell y JZPass)."""

from __future__ import annotations

import ipaddress
from typing import Iterable, Union

from starlette.requests import Request

_Network = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]


def parse_networks(spec: str) -> list[_Network]:
    """Parsea 'IP/CIDR,IP/CIDR,...' (formato de TRUSTED_PROXIES en cada .env)."""
    return [ipaddress.ip_network(n.strip(), strict=False) for n in spec.split(",") if n.strip()]


def _is_trusted(value: str, trusted_proxies: Iterable[_Network]) -> bool:
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(addr in net for net in trusted_proxies)


def real_ip(request: Request, trusted_proxies: Iterable[_Network]) -> str:
    """IP del cliente, confiando en X-Forwarded-For solo si la conexion TCP viene
    de una red en trusted_proxies. Si no, devuelve la IP de la conexion tal cual
    (nunca confia en el header desde un origen no confiable).

    Camina la cadena de X-Forwarded-For de derecha a izquierda (el salto mas
    cercano es el ultimo que agrego el proxy mas cercano) devolviendo el primer
    valor que no sea, el mismo, un proxy de confianza. Esto soporta cadenas de
    varios proxies de confianza en serie (p. ej. Caddy -> otro proxy interno),
    a diferencia de tomar ciegamente el primer valor de la lista.
    """
    peer = request.client.host if request.client else "0.0.0.0"
    if not _is_trusted(peer, trusted_proxies):
        return peer

    forwarded = [p.strip() for p in (request.headers.get("x-forwarded-for") or "").split(",") if p.strip()]
    for hop in reversed(forwarded):
        if not _is_trusted(hop, trusted_proxies):
            return hop
    return forwarded[0] if forwarded else peer
