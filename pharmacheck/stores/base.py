"""Contrato común a todas las farmacias.

Cada farmacia se implementa como un adaptador. Hoy todas las soportadas corren
sobre VTEX y comparten un único adaptador; sumar una tienda de otra plataforma
sólo requiere una subclase nueva registrada en `stores/__init__.py`.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from urllib.parse import quote, urlencode

import requests

from ..models import Estado, Producto, Resultado

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class ErrorFarmacia(Exception):
    """La tienda no pudo responder (red, bloqueo, formato inesperado)."""


class AdaptadorFarmacia(ABC):
    """Base de todos los adaptadores de farmacia."""

    def __init__(
        self,
        nombre: str,
        base_url: str,
        *,
        umbral_nombre: float = 0.65,
        demora: float = 0.4,
        timeout: float = 20.0,
        reintentos: int = 3,
        **_extra,
    ) -> None:
        self.nombre = nombre
        self.base_url = base_url.rstrip("/")
        self.umbral_nombre = umbral_nombre
        self.demora = demora
        self.timeout = timeout
        self.reintentos = reintentos
        self.sesion = requests.Session()
        self.sesion.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "es-AR,es;q=0.9",
            }
        )

    @abstractmethod
    def chequear(self, producto: Producto) -> Resultado:
        """Devuelve el estado del producto en esta farmacia."""

    # -- utilidades compartidas -------------------------------------------------

    def _get_json(self, url: str, params: dict | None = None):
        """GET con reintentos y backoff ante 429 / 5xx.

        Los parámetros se codifican a mano porque `requests` convierte los
        espacios en `+` y el WAF de varias tiendas VTEX rechaza esa forma con
        "Bad Request! Scripts are not allowed!". Con `%20` responden normal.
        """
        if params:
            url = f"{url}?{urlencode(params, quote_via=quote)}"

        ultimo_error = ""
        for intento in range(self.reintentos):
            if intento:
                time.sleep(min(2**intento, 8))
            try:
                resp = self.sesion.get(url, timeout=self.timeout)
            except requests.RequestException as exc:
                ultimo_error = f"red: {exc.__class__.__name__}"
                continue

            # VTEX devuelve 206 (Partial Content) en las búsquedas paginadas.
            if resp.status_code in (200, 206):
                try:
                    return resp.json()
                except ValueError:
                    raise ErrorFarmacia("la respuesta no es JSON (¿bloqueo o captcha?)")
            if resp.status_code == 404:
                return None
            if resp.status_code in (429, 500, 502, 503, 504):
                ultimo_error = f"HTTP {resp.status_code}"
                continue
            # Incluimos el cuerpo: las tiendas explican el rechazo ahí.
            raise ErrorFarmacia(f"HTTP {resp.status_code}: {resp.text[:80].strip()}")

        raise ErrorFarmacia(ultimo_error or "sin respuesta")

    def _resultado_error(self, producto: Producto, detalle: str) -> Resultado:
        return Resultado(
            producto=producto,
            farmacia=self.nombre,
            estado=Estado.ERROR,
            detalle=detalle,
        )

    def _resultado_no_listado(self, producto: Producto, detalle: str = "") -> Resultado:
        return Resultado(
            producto=producto,
            farmacia=self.nombre,
            estado=Estado.NO_LISTADO,
            detalle=detalle,
        )
