"""Lectura del catálogo propio (productos.csv)."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from .models import Producto

# Nombres de columna aceptados, para no obligar a un encabezado exacto.
_COLUMNAS = {
    "codigo": {"codigo", "código", "cod", "sku", "codigo_interno"},
    "nombre": {"nombre", "producto", "descripcion", "descripción", "detalle"},
    "ean": {"ean", "ean13", "gtin", "codigo_barras", "código_barras", "barcode"},
    "alias": {"alias", "sinonimos", "sinónimos", "alternativos"},
}


def _mapear_encabezados(campos: list[str]) -> dict[str, str]:
    mapa: dict[str, str] = {}
    for campo in campos or []:
        clave = (campo or "").strip().lower().lstrip("﻿")
        for destino, aceptados in _COLUMNAS.items():
            if clave in aceptados and destino not in mapa:
                mapa[destino] = campo
    return mapa


def _limpiar_ean(valor: str) -> str:
    """Deja sólo dígitos. Excel suele exportar el EAN como '7798389330018.0'."""
    digitos = re.sub(r"\D", "", valor or "")
    return digitos


def _leer_eans(valor: str) -> list[str]:
    """Separa varios códigos de barras escritos en la misma celda ('a | b')."""
    partes = re.split(r"[|/]", valor or "")
    codigos = [_limpiar_ean(p) for p in partes]
    return [c for c in codigos if c]


def cargar_productos(ruta: str | Path) -> list[Producto]:
    """Lee el CSV de productos. Requiere al menos la columna `nombre`."""
    ruta = Path(ruta)
    texto = ruta.read_text(encoding="utf-8-sig")
    # Autodetecta si el archivo usa coma o punto y coma (Excel en es-AR usa ';').
    try:
        dialecto = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=",;\t")
        delimitador = dialecto.delimiter
    except (csv.Error, IndexError):
        delimitador = ","

    lector = csv.DictReader(texto.splitlines(), delimiter=delimitador)
    mapa = _mapear_encabezados(lector.fieldnames or [])
    if "nombre" not in mapa:
        raise ValueError(
            f"{ruta}: falta la columna 'nombre'. "
            f"Encabezados encontrados: {lector.fieldnames}"
        )

    productos: list[Producto] = []
    for fila in lector:
        nombre = (fila.get(mapa["nombre"]) or "").strip()
        if not nombre:
            continue
        alias_bruto = (fila.get(mapa.get("alias", ""), "") or "").strip()
        eans = _leer_eans(fila.get(mapa.get("ean", ""), ""))
        productos.append(
            Producto(
                codigo=(fila.get(mapa.get("codigo", ""), "") or "").strip(),
                nombre=nombre,
                ean=eans[0] if eans else "",
                eans_alt=eans[1:],
                alias=[a.strip() for a in re.split(r"[|;]", alias_bruto) if a.strip()],
            )
        )

    return productos
