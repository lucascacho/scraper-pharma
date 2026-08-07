"""Registro de adaptadores y carga de la configuración de farmacias."""

from __future__ import annotations

import json
from pathlib import Path

from .base import AdaptadorFarmacia, ErrorFarmacia
from .vtex import AdaptadorVTEX

# Para sumar una plataforma nueva: crear la subclase y registrarla acá.
ADAPTADORES: dict[str, type[AdaptadorFarmacia]] = {
    "vtex": AdaptadorVTEX,
}


def crear_adaptador(config: dict, **defaults) -> AdaptadorFarmacia:
    """Instancia el adaptador que corresponde a una entrada de farmacias.json."""
    tipo = config.get("tipo", "vtex").lower()
    if tipo not in ADAPTADORES:
        raise ValueError(
            f"tipo de farmacia desconocido: {tipo!r} "
            f"(disponibles: {', '.join(sorted(ADAPTADORES))})"
        )

    opciones = {k: v for k, v in config.items() if k not in ("tipo", "activa")}
    opciones.setdefault("nombre", config.get("base_url", tipo))
    for clave, valor in defaults.items():
        if valor is not None:
            opciones[clave] = valor

    return ADAPTADORES[tipo](**opciones)


def cargar_farmacias(ruta: str | Path, solo: list[str] | None = None, **defaults) -> list[AdaptadorFarmacia]:
    """Lee farmacias.json y devuelve los adaptadores activos.

    `solo` filtra por nombre (case-insensitive, coincidencia parcial).
    """
    configs = json.loads(Path(ruta).read_text(encoding="utf-8"))
    adaptadores = []

    for config in configs:
        if not config.get("activa", True):
            continue
        if solo:
            nombre = config.get("nombre", "").lower()
            if not any(filtro.lower() in nombre for filtro in solo):
                continue
        adaptadores.append(crear_adaptador(config, **defaults))

    return adaptadores


__all__ = [
    "ADAPTADORES",
    "AdaptadorFarmacia",
    "AdaptadorVTEX",
    "ErrorFarmacia",
    "cargar_farmacias",
    "crear_adaptador",
]
