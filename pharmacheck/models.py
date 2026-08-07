"""Tipos de datos compartidos por todo el chequeador de stock."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Estado(str, Enum):
    """Resultado del chequeo de un producto en una farmacia."""

    EN_STOCK = "EN_STOCK"
    SIN_STOCK = "SIN_STOCK"
    NO_LISTADO = "NO_LISTADO"
    ERROR = "ERROR"


class TipoMatch(str, Enum):
    """Cómo se identificó el producto en la farmacia."""

    EAN = "ean"                # coincidencia exacta de código de barras
    REFERENCIA = "referencia"  # coincidencia por código de referencia del catálogo
    NOMBRE = "nombre"          # fallback por texto: revisar manualmente
    NINGUNO = "-"

    @property
    def es_confiable(self) -> bool:
        return self in (TipoMatch.EAN, TipoMatch.REFERENCIA)


@dataclass
class Producto:
    """Un producto de tu catálogo a monitorear."""

    codigo: str          # tu código interno (opcional, sirve para cruzar con tu ERP)
    nombre: str          # nombre comercial, se usa para el fallback por texto
    ean: str = ""        # código de barras; si está, se usa para el match exacto
    alias: list[str] = field(default_factory=list)   # términos alternativos de búsqueda
    # Un mismo producto puede estar cargado con distintos códigos según la cadena
    # (p. ej. el GTIN del envase secundario), así que se aceptan alternativos.
    eans_alt: list[str] = field(default_factory=list)

    def todos_los_eans(self) -> list[str]:
        """EAN principal seguido de los alternativos, sin repetir."""
        codigos: list[str] = []
        for codigo in [self.ean, *self.eans_alt]:
            if codigo and codigo not in codigos:
                codigos.append(codigo)
        return codigos

    def terminos_busqueda(self) -> list[str]:
        """Términos a probar en el fallback por texto, en orden de preferencia."""
        vistos: list[str] = []
        for termino in [self.nombre, *self.alias]:
            termino = termino.strip()
            if termino and termino not in vistos:
                vistos.append(termino)
        return vistos


@dataclass
class Resultado:
    """Estado de un producto en una farmacia puntual."""

    producto: Producto
    farmacia: str
    estado: Estado
    tipo_match: TipoMatch = TipoMatch.NINGUNO
    confianza: float = 0.0
    nombre_encontrado: str = ""
    precio: float | None = None
    precio_lista: float | None = None
    stock: int | None = None
    sku: str = ""
    url: str = ""
    detalle: str = ""

    @property
    def revisar_manual(self) -> bool:
        """True cuando el match no es exacto y conviene una verificación humana."""
        return (
            self.estado in (Estado.EN_STOCK, Estado.SIN_STOCK)
            and not self.tipo_match.es_confiable
        )
