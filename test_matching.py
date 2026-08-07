#!/usr/bin/env python3
"""Pruebas del matcheo por nombre, que es la parte que puede equivocarse.

Correr con:  python3 test_matching.py
"""

from pharmacheck.catalogo import _leer_eans, _limpiar_ean
from pharmacheck.matching import puntuar, tokenizar
from pharmacheck.models import Producto

UMBRAL = 0.65

# (consulta, candidato, ¿debería aceptarse?)
CASOS = [
    # Mismo producto escrito distinto por cada farmacia
    ("Hepatalgina x20comp", "Hepatalgina x20 comprimidos", True),
    ("Buscapina x20 grageas", "Buscapina Antiespasmódico x 20 grageas", True),
    ("Enterogermina Plus Ampollas Bebibles x5 x5ml", "Enterogermina Plus 5 unid x 5 ml", True),
    ("Ibuprofeno 400mg x10 comp", "Ibuprofeno 400 x 10 Comprimidos", True),
    ("Hepatalgina Gotas x120ml", "Hepatalgina Gotas X 120 Ml", True),
    # Misma marca, presentación distinta -> NO es el mismo producto
    ("Hepatalgina x20comp", "Hepatalgina Gotas X 120 Ml", False),
    ("Ibuprofeno 400mg x10", "Ibuprofeno 600mg x20 comprimidos", False),
    ("Enterogermina Plus Ampollas Bebibles x5 x5ml", "Enterogermina 2000 Millones x 10 Ampollas", False),
    # Otra marca con misma dosis y formato -> el clásico falso positivo
    ("Novalgina 500mg x 20 comprimidos", "Paracetamol Raffo 500mg x20 comprimidos", False),
    ("Buscapina Perlas 50 capsulas", "Buscapina Fem x 50 comprimidos", False),
]

# Una consulta corta no puede declarar coincidencia perfecta con un nombre
# mucho más largo: el candidato describe cosas que la consulta no dice.
SIN_CONFIANZA_PLENA = [
    ("Enterogermina Plus x5", "Enterogermina Plus 5 unid x 5 ml"),
    ("Buscapina x20", "Buscapina Antiespasmódico Fem x 20 comprimidos recubiertos"),
]

# La cantidad debe sobrevivir a la tokenización: "x20" es 20, no 2 y 0.
TOKENS = [
    ("Hepatalgina x20comp", ["hepatalgina", "20", "comprimidos"]),
    ("Ibuprofeno 400mg x 10", ["ibuprofeno", "400", "mg", "10"]),
    ("Enterogermina Plus x5 x5ml", ["enterogermina", "plus", "5", "5", "ml"]),
]

# Excel suele arruinar el EAN al exportar; se normaliza a dígitos.
EANS = [
    ("7798389330018", "7798389330018"),
    ("7798389330018.0", "77983893300180"),
    ("  7798389330018 ", "7798389330018"),
    ("779-838-9330018", "7798389330018"),
    ("", ""),
]


def main() -> int:
    fallos = 0

    for texto, esperado in TOKENS:
        obtenido = tokenizar(texto)
        if obtenido != esperado:
            print(f"FALLA tokenizar({texto!r}) = {obtenido} != {esperado}")
            fallos += 1

    for consulta, candidato, aceptar in CASOS:
        puntaje = puntuar(consulta, candidato)
        if (puntaje >= UMBRAL) != aceptar:
            estado = "aceptó" if puntaje >= UMBRAL else "rechazó"
            print(f"FALLA {estado} ({puntaje:.2f}) {consulta!r} vs {candidato!r}")
            fallos += 1

    for consulta, candidato in SIN_CONFIANZA_PLENA:
        puntaje = puntuar(consulta, candidato)
        if puntaje >= 1.0:
            print(f"FALLA confianza plena indebida ({puntaje:.2f}) {consulta!r} vs {candidato!r}")
            fallos += 1

    for bruto, esperado in EANS:
        if _limpiar_ean(bruto) != esperado:
            print(f"FALLA _limpiar_ean({bruto!r}) = {_limpiar_ean(bruto)!r} != {esperado!r}")
            fallos += 1

    # Varios códigos de barras en una misma celda: el primero manda, el resto queda de respaldo.
    if _leer_eans("7798389330018 | 7795312109017") != ["7798389330018", "7795312109017"]:
        print("FALLA _leer_eans no separa múltiples EAN")
        fallos += 1

    producto = Producto(codigo="x", nombre="n", ean="111", eans_alt=["222", "111", ""])
    if producto.todos_los_eans() != ["111", "222"]:
        print(f"FALLA todos_los_eans() = {producto.todos_los_eans()}")
        fallos += 1

    total = len(TOKENS) + len(CASOS) + len(SIN_CONFIANZA_PLENA) + len(EANS) + 2
    print(f"{total - fallos}/{total} pruebas OK")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
