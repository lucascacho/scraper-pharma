"""Orquestación del chequeo: productos × farmacias."""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor

from .models import Estado, Producto, Resultado
from .stores.base import AdaptadorFarmacia


def _chequear_farmacia(
    adaptador: AdaptadorFarmacia,
    productos: list[Producto],
    verboso: bool,
) -> list[Resultado]:
    """Recorre todos los productos en una farmacia, de a uno.

    Se mantiene secuencial a propósito: paralelizar dentro de una misma tienda
    dispara los límites de rate y termina devolviendo errores en vez de datos.
    """
    resultados = []
    for producto in productos:
        resultado = adaptador.chequear(producto)
        resultados.append(resultado)
        if verboso:
            marca = {
                Estado.EN_STOCK: "✓",
                Estado.SIN_STOCK: "✗",
                Estado.NO_LISTADO: "·",
                Estado.ERROR: "!",
            }[resultado.estado]
            print(
                f"  {marca} [{adaptador.nombre}] {producto.nombre[:45]:<45} "
                f"{resultado.estado.value}"
                + (f" ({resultado.detalle})" if resultado.detalle else ""),
                file=sys.stderr,
            )
    return resultados


def ejecutar(
    productos: list[Producto],
    adaptadores: list[AdaptadorFarmacia],
    *,
    verboso: bool = False,
) -> list[Resultado]:
    """Chequea todos los productos en todas las farmacias.

    Las farmacias corren en paralelo (una hebra por tienda), los productos de
    cada farmacia en serie.
    """
    if not adaptadores:
        return []

    with ThreadPoolExecutor(max_workers=len(adaptadores)) as pool:
        tandas = pool.map(
            lambda a: _chequear_farmacia(a, productos, verboso), adaptadores
        )
        resultados = [r for tanda in tandas for r in tanda]

    # Ordena por producto (según el orden del CSV) y luego por farmacia.
    orden_producto = {id(p): i for i, p in enumerate(productos)}
    resultados.sort(key=lambda r: (orden_producto.get(id(r.producto), 0), r.farmacia))
    return resultados
