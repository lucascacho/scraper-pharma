"""Normalización y comparación de nombres de productos farmacéuticos.

El fallback por texto es la parte frágil del scraping: dos productos pueden
llamarse casi igual y diferir en la dosis o en la cantidad de unidades
("Ibuprofeno 400mg x10" vs "Ibuprofeno 600mg x20"). Por eso el puntaje penaliza
fuerte cuando los tokens numéricos no coinciden.
"""

from __future__ import annotations

import re
import unicodedata

# Palabras que no aportan a la identificación y ensucian el puntaje.
_VACIAS = {
    "de", "del", "la", "el", "los", "las", "y", "con", "para", "en", "por",
    "a", "al", "un", "una", "sin",
}

# Formas equivalentes que las farmacias escriben de manera distinta.
_SINONIMOS = {
    "comp": "comprimidos", "comprimido": "comprimidos", "comps": "comprimidos",
    "cap": "capsulas", "capsula": "capsulas", "caps": "capsulas",
    "amp": "ampollas", "ampolla": "ampollas",
    "unid": "unidades", "unidad": "unidades", "un": "unidades", "u": "unidades",
    "grs": "g", "gr": "g", "gramos": "g",
    "mgs": "mg",
    "mls": "ml", "cc": "ml",
    "sobre": "sobres",
}

_NUMERICO = re.compile(r"^\d+(?:[.,]\d+)?[a-z]*$")


def normalizar(texto: str) -> str:
    """Baja a minúsculas, saca acentos y unifica separadores."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    # "x5", "x 5" y "x20comp" indican cantidad: se descarta la x y se conserva
    # el número completo (partirlo daría "2" + "0" en vez de "20").
    texto = re.sub(r"\bx\s*(?=\d)", " ", texto)
    texto = re.sub(r"[^a-z0-9.,]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def tokenizar(texto: str) -> list[str]:
    """Devuelve los tokens significativos, con unidades separadas del número."""
    tokens: list[str] = []
    for bruto in normalizar(texto).split():
        # "400mg" -> "400" + "mg" para que la dosis compare aunque cambie el formato
        partido = re.fullmatch(r"(\d+(?:[.,]\d+)?)([a-z]+)", bruto)
        piezas = list(partido.groups()) if partido else [bruto]
        for pieza in piezas:
            pieza = pieza.rstrip(".,")
            pieza = _SINONIMOS.get(pieza, pieza)
            if pieza and pieza not in _VACIAS:
                tokens.append(pieza)
    return tokens


def _numericos(tokens: list[str]) -> set[str]:
    return {t.replace(",", ".").lstrip("0") or "0" for t in tokens if _NUMERICO.match(t)}


def puntuar(consulta: str, candidato: str) -> float:
    """Puntaje 0..1 de qué tan bien el candidato representa a la consulta.

    Mide cuántos tokens de la consulta aparecen en el candidato y castiga
    las diferencias de dosis o cantidad, que en farmacia cambian el producto.
    """
    tokens_consulta = tokenizar(consulta)
    tokens_candidato = tokenizar(candidato)
    if not tokens_consulta or not tokens_candidato:
        return 0.0

    set_candidato = set(tokens_candidato)
    cubiertos = sum(1 for t in tokens_consulta if t in set_candidato)
    puntaje = cubiertos / len(tokens_consulta)

    # El primer token suele ser la marca: si falta, casi seguro no es el producto.
    if tokens_consulta[0] not in set_candidato:
        puntaje *= 0.5

    nums_consulta = _numericos(tokens_consulta)
    nums_candidato = _numericos(tokens_candidato)
    if nums_consulta:
        faltantes = nums_consulta - nums_candidato
        if faltantes:
            puntaje *= 0.4 if len(faltantes) == len(nums_consulta) else 0.6

    # Un candidato mucho más largo describe algo que la consulta no dice: puede ser
    # otra presentación o un combo. También evita que una consulta muy corta
    # ("Buscapina x20") se declare coincidencia perfecta de cualquier cosa.
    exceso = len(tokens_candidato) / len(tokens_consulta)
    if exceso > 1.5:
        puntaje *= max(0.7, 1.5 / exceso)

    return round(min(puntaje, 1.0), 3)


def mejor_candidato(consulta: str, candidatos: list[tuple[str, object]]) -> tuple[object | None, float]:
    """Elige el candidato de mayor puntaje. Recibe pares (nombre, objeto)."""
    mejor: object | None = None
    mejor_puntaje = 0.0
    for nombre, objeto in candidatos:
        puntaje = puntuar(consulta, nombre)
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = objeto, puntaje
    return mejor, mejor_puntaje
