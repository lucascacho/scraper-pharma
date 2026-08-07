"""Salida del chequeo: CSV detallado, matriz pivote y resumen en consola."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import Estado, Resultado

ENCABEZADOS = [
    "codigo",
    "producto",
    "ean",
    "farmacia",
    "estado",
    "tipo_match",
    "confianza",
    "revisar",
    "nombre_encontrado",
    "precio",
    "precio_lista",
    "stock",
    "sku",
    "url",
    "detalle",
]


def _fila(resultado: Resultado) -> list:
    return [
        resultado.producto.codigo,
        resultado.producto.nombre,
        resultado.producto.ean,
        resultado.farmacia,
        resultado.estado.value,
        resultado.tipo_match.value,
        f"{resultado.confianza:.2f}" if resultado.confianza else "",
        "SI" if resultado.revisar_manual else "",
        resultado.nombre_encontrado,
        "" if resultado.precio is None else f"{resultado.precio:.2f}",
        "" if resultado.precio_lista is None else f"{resultado.precio_lista:.2f}",
        "" if resultado.stock is None else resultado.stock,
        resultado.sku,
        resultado.url,
        resultado.detalle,
    ]


def escribir_csv(resultados: list[Resultado], ruta: str | Path, separador: str = ";") -> Path:
    """CSV detallado: una fila por producto × farmacia."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig para que Excel respete los acentos al abrir el archivo.
    with ruta.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=separador)
        escritor.writerow(ENCABEZADOS)
        escritor.writerows(_fila(r) for r in resultados)
    return ruta


def escribir_matriz(resultados: list[Resultado], ruta: str | Path, separador: str = ";") -> Path:
    """CSV pivote: productos en filas, farmacias en columnas. Para leer de un vistazo."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    farmacias, productos = [], []
    for r in resultados:
        if r.farmacia not in farmacias:
            farmacias.append(r.farmacia)
        clave = (r.producto.codigo, r.producto.nombre, r.producto.ean)
        if clave not in productos:
            productos.append(clave)

    celdas = {
        (r.producto.codigo, r.producto.nombre, r.producto.ean, r.farmacia): r
        for r in resultados
    }

    with ruta.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=separador)
        escritor.writerow(["codigo", "producto", "ean", *farmacias])
        for codigo, nombre, ean in productos:
            fila = [codigo, nombre, ean]
            for farmacia in farmacias:
                r = celdas.get((codigo, nombre, ean, farmacia))
                if r is None:
                    fila.append("")
                elif r.estado is Estado.EN_STOCK:
                    fila.append("EN STOCK" + (" (?)" if r.revisar_manual else ""))
                elif r.estado is Estado.SIN_STOCK:
                    fila.append("SIN STOCK" + (" (?)" if r.revisar_manual else ""))
                else:
                    fila.append(r.estado.value)
            escritor.writerow(fila)
    return ruta


def resumen_consola(resultados: list[Resultado]) -> str:
    """Resumen legible por farmacia + advertencias de matches dudosos."""
    if not resultados:
        return "Sin resultados."

    por_farmacia: dict[str, dict[Estado, int]] = {}
    for r in resultados:
        por_farmacia.setdefault(r.farmacia, {}).setdefault(r.estado, 0)
        por_farmacia[r.farmacia][r.estado] += 1

    ancho = max(len(f) for f in por_farmacia)
    lineas = [
        "",
        f"{'FARMACIA'.ljust(ancho)}  {'EN STOCK':>9} {'SIN STOCK':>10} {'NO LISTADO':>11} {'ERROR':>6}",
        "-" * (ancho + 42),
    ]
    for farmacia in sorted(por_farmacia):
        conteo = por_farmacia[farmacia]
        lineas.append(
            f"{farmacia.ljust(ancho)}  "
            f"{conteo.get(Estado.EN_STOCK, 0):>9} "
            f"{conteo.get(Estado.SIN_STOCK, 0):>10} "
            f"{conteo.get(Estado.NO_LISTADO, 0):>11} "
            f"{conteo.get(Estado.ERROR, 0):>6}"
        )

    dudosos = [r for r in resultados if r.revisar_manual]
    if dudosos:
        lineas += ["", f"⚠  {len(dudosos)} match(es) por nombre — verificar:"]
        for r in dudosos[:10]:
            lineas.append(
                f"   [{r.farmacia}] «{r.producto.nombre}» → «{r.nombre_encontrado}» "
                f"(confianza {r.confianza:.2f})"
            )
        if len(dudosos) > 10:
            lineas.append(f"   ... y {len(dudosos) - 10} más (ver columna 'revisar' en el CSV)")

    errores = [r for r in resultados if r.estado is Estado.ERROR]
    if errores:
        lineas += ["", f"✖  {len(errores)} error(es) de consulta:"]
        for r in errores[:5]:
            lineas.append(f"   [{r.farmacia}] {r.producto.nombre}: {r.detalle}")

    return "\n".join(lineas)
