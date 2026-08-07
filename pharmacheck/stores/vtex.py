"""Adaptador para farmacias montadas sobre VTEX.

VTEX expone un catálogo público en `/api/catalog_system/pub/products/search`
que devuelve precio y stock en JSON, así que no hace falta parsear HTML ni
levantar un navegador. El mismo adaptador sirve para todas las cadenas VTEX;
sólo cambia el dominio.

Estrategia de identificación, de más a menos confiable:
  1. `fq=alternateIds_Ean:<ean>`   -> match exacto por código de barras
  2. `fq=alternateIds_RefId:<ean>` -> algunas cadenas cargan el EAN como RefId
  3. `ft=<nombre>`                 -> búsqueda por texto, se puntúa y se marca
                                      como "revisar" porque puede equivocarse
"""

from __future__ import annotations

import time

from ..matching import puntuar
from ..models import Estado, Producto, Resultado, TipoMatch
from .base import AdaptadorFarmacia, ErrorFarmacia

RUTA_BUSQUEDA = "/api/catalog_system/pub/products/search"


class AdaptadorVTEX(AdaptadorFarmacia):
    """Consulta catálogo y stock de una tienda VTEX."""

    def __init__(self, *args, sales_channel: str | None = None, max_resultados: int = 20, **kwargs):
        super().__init__(*args, **kwargs)
        self.sales_channel = sales_channel
        self.max_resultados = max_resultados

    # -- API pública ------------------------------------------------------------

    def chequear(self, producto: Producto) -> Resultado:
        try:
            for ean in producto.todos_los_eans():
                encontrado = self._buscar_exacto(ean)
                if encontrado:
                    prod, tipo = encontrado
                    return self._armar_resultado(producto, prod, tipo, 1.0)

            encontrado = self._buscar_por_texto(producto)
            if encontrado:
                prod, tipo, confianza = encontrado
                return self._armar_resultado(producto, prod, tipo, confianza)

            detalle = "sin coincidencias por EAN ni por nombre" if producto.ean else "sin coincidencias por nombre"
            return self._resultado_no_listado(producto, detalle)

        except ErrorFarmacia as exc:
            return self._resultado_error(producto, str(exc))

    # -- búsquedas --------------------------------------------------------------

    def _buscar(self, params: dict) -> list[dict]:
        if self.sales_channel:
            params = {**params, "sc": self.sales_channel}
        datos = self._get_json(self.base_url + RUTA_BUSQUEDA, params)
        time.sleep(self.demora)  # cortesía con la tienda: evita el rate limit
        return datos if isinstance(datos, list) else []

    def _buscar_exacto(self, ean: str) -> tuple[dict, TipoMatch] | None:
        """Busca por código de barras, primero como EAN y luego como RefId."""
        for filtro, tipo in (
            (f"alternateIds_Ean:{ean}", TipoMatch.EAN),
            (f"alternateIds_RefId:{ean}", TipoMatch.REFERENCIA),
        ):
            productos = self._buscar({"fq": filtro})
            if productos:
                return productos[0], tipo
        return None

    def _buscar_por_texto(self, producto: Producto) -> tuple[dict, TipoMatch, float] | None:
        """Fallback: full-text search y elección del mejor candidato por puntaje."""
        mejor: dict | None = None
        mejor_puntaje = 0.0

        for termino in producto.terminos_busqueda():
            productos = self._buscar(
                {"ft": termino, "_from": 0, "_to": self.max_resultados - 1}
            )
            for candidato in productos:
                # Si el EAN aparece entre los SKUs, dejamos de adivinar: es exacto.
                # Pasa cuando la tienda no indexó el EAN pero sí lo cargó en el SKU.
                if self._tiene_ean(candidato, producto.todos_los_eans()):
                    return candidato, TipoMatch.EAN, 1.0
                puntaje = puntuar(termino, candidato.get("productName", ""))
                if puntaje > mejor_puntaje:
                    mejor, mejor_puntaje = candidato, puntaje
            if mejor_puntaje >= 0.95:
                break

        if mejor is not None and mejor_puntaje >= self.umbral_nombre:
            return mejor, TipoMatch.NOMBRE, mejor_puntaje
        return None

    # -- lectura del stock ------------------------------------------------------

    @staticmethod
    def _tiene_ean(producto_vtex: dict, eans: list[str]) -> bool:
        if not eans:
            return False
        return any(item.get("ean") in eans for item in producto_vtex.get("items", []))

    @staticmethod
    def _skus_relevantes(producto_vtex: dict, eans: list[str]) -> list[dict]:
        """SKUs a considerar: los que matchean algún EAN, o todos si ninguno matchea."""
        items = producto_vtex.get("items", []) or []
        if eans:
            exactos = [i for i in items if i.get("ean") in eans]
            if exactos:
                return exactos
        return items

    def _armar_resultado(
        self,
        producto: Producto,
        producto_vtex: dict,
        tipo: TipoMatch,
        confianza: float,
    ) -> Resultado:
        mejor_oferta: dict | None = None
        mejor_item: dict | None = None
        stock_total = 0
        hay_stock = False

        for item in self._skus_relevantes(producto_vtex, producto.todos_los_eans()):
            for vendedor in item.get("sellers", []) or []:
                oferta = vendedor.get("commertialOffer") or {}
                cantidad = oferta.get("AvailableQuantity") or 0
                disponible = bool(oferta.get("IsAvailable")) and cantidad > 0
                stock_total += cantidad
                # Preferimos mostrar el precio de una oferta con stock real.
                if disponible and not hay_stock:
                    mejor_oferta, mejor_item, hay_stock = oferta, item, True
                elif mejor_oferta is None:
                    mejor_oferta, mejor_item = oferta, item

        oferta = mejor_oferta or {}
        item = mejor_item or {}

        return Resultado(
            producto=producto,
            farmacia=self.nombre,
            estado=Estado.EN_STOCK if hay_stock else Estado.SIN_STOCK,
            tipo_match=tipo,
            confianza=round(confianza, 3),
            nombre_encontrado=producto_vtex.get("productName", ""),
            precio=oferta.get("Price"),
            precio_lista=oferta.get("ListPrice"),
            stock=stock_total,
            sku=str(item.get("itemId", "")),
            url=producto_vtex.get("link") or self._url_producto(producto_vtex),
        )

    def _url_producto(self, producto_vtex: dict) -> str:
        slug = producto_vtex.get("linkText")
        return f"{self.base_url}/{slug}/p" if slug else ""
