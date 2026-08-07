#!/usr/bin/env python3
"""Chequea si tus productos figuran y tienen stock en las farmacias online.

Uso típico:
    python3 check_stock.py
    python3 check_stock.py --solo FarmaPlus --verbose
    python3 check_stock.py --productos mi_catalogo.csv --salida reportes/
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from pharmacheck.catalogo import cargar_productos
from pharmacheck.report import escribir_csv, escribir_matriz, resumen_consola
from pharmacheck.runner import ejecutar
from pharmacheck.stores import cargar_farmacias

RAIZ = Path(__file__).resolve().parent


def parsear_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Chequeo de existencia y stock de productos en farmacias online.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--productos", default=str(RAIZ / "productos.csv"),
                   help="CSV con tus productos (columnas: codigo, nombre, ean, alias)")
    p.add_argument("--farmacias", default=str(RAIZ / "farmacias.json"),
                   help="JSON con las farmacias a consultar")
    p.add_argument("--salida", default=str(RAIZ / "reportes"),
                   help="Carpeta donde se escriben los CSV")
    p.add_argument("--solo", nargs="+", metavar="FARMACIA",
                   help="Consultar sólo estas farmacias (coincidencia parcial por nombre)")
    p.add_argument("--umbral", type=float, default=0.65, metavar="0..1",
                   help="Confianza mínima para aceptar un match por nombre")
    p.add_argument("--demora", type=float, default=0.4, metavar="SEG",
                   help="Pausa entre pedidos a una misma farmacia")
    p.add_argument("--sep", default=";", metavar="CHAR",
                   help="Separador del CSV de salida (';' abre bien en Excel es-AR)")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Mostrar el avance producto por producto")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parsear_args(argv)

    try:
        productos = cargar_productos(args.productos)
    except (OSError, ValueError) as exc:
        print(f"Error leyendo productos: {exc}", file=sys.stderr)
        return 1

    try:
        adaptadores = cargar_farmacias(
            args.farmacias,
            solo=args.solo,
            umbral_nombre=args.umbral,
            demora=args.demora,
        )
    except (OSError, ValueError) as exc:
        print(f"Error leyendo farmacias: {exc}", file=sys.stderr)
        return 1

    if not productos:
        print("El catálogo no tiene productos.", file=sys.stderr)
        return 1
    if not adaptadores:
        print("No hay farmacias activas que consultar.", file=sys.stderr)
        return 1

    print(
        f"Chequeando {len(productos)} producto(s) en {len(adaptadores)} farmacia(s): "
        f"{', '.join(a.nombre for a in adaptadores)}",
        file=sys.stderr,
    )

    resultados = ejecutar(productos, adaptadores, verboso=args.verbose)

    sello = datetime.now().strftime("%Y%m%d-%H%M")
    salida = Path(args.salida)
    detalle = escribir_csv(resultados, salida / f"stock-{sello}.csv", args.sep)
    matriz = escribir_matriz(resultados, salida / f"matriz-{sello}.csv", args.sep)

    print(resumen_consola(resultados))
    print(f"\nDetalle: {detalle}\nMatriz:  {matriz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
