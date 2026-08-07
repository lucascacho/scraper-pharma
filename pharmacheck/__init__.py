"""pharmacheck — chequeo de stock de productos propios en farmacias online."""

from .catalogo import cargar_productos
from .models import Estado, Producto, Resultado, TipoMatch
from .runner import ejecutar
from .stores import cargar_farmacias, crear_adaptador

__all__ = [
    "Estado",
    "Producto",
    "Resultado",
    "TipoMatch",
    "cargar_farmacias",
    "cargar_productos",
    "crear_adaptador",
    "ejecutar",
]
