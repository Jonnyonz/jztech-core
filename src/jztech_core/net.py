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


def real_ip(request: Request, trusted_proxies: Iterable[_Network]) -> str:
    """IP del cliente, confiando en X-Forwarded-For solo si la conexion TCP viene
    de una red en trusted_proxies. Si no, devuelve la IP de la conexion tal cual
    (nunca confia en el header desde un origen no confiable)."""
    client_ip = request.client.host if request.client else "0.0.0.0"
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return client_ip

    if not any(addr in net for net in trusted_proxies):
        return client_ip

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return client_ip

    first = forwarded.split(",")[0].strip()
    try:
        ipaddress.ip_address(first)
    except ValueError:
        return client_ip
    return first
