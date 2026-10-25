"""Reglas de puntuación del Yahtzee clásico (13 casillas).

El tablero se divide en dos zonas:

* **Zona superior**: Unos, Doses, Treses, Cuatros, Cincos y Seises.  Se suma
  el valor de los dados que coinciden con la cara de la casilla.
* **Zona inferior**: Tres iguales, Cuatro de la misma clase, Casa llena,
  Pequeño recto, Grande y recto, Oportunidad y Yahtzee.

Si la zona superior suma **63 puntos o más** se obtienen **35 puntos de bono**.

Todas las funciones de este módulo son puras: reciben una tirada y devuelven
un número, sin modificar nada.  Esa pureza es la que permite probarlas con
pruebas unitarias y reutilizarlas tanto en el juego interactivo como en el
motor de Montecarlo.
"""

from __future__ import annotations

from typing import Callable, Sequence

from .dados import contar_caras

# ---------------------------------------------------------------------------
# Catálogo de casillas
# ---------------------------------------------------------------------------

CATEGORIAS_SUPERIORES: tuple[str, ...] = (
    "unos",
    "doses",
    "treses",
    "cuatros",
    "cincos",
    "seises",
)

CATEGORIAS_INFERIORES: tuple[str, ...] = (
    "tres_iguales",
    "cuatro_iguales",
    "casa_llena",
    "pequeno_recto",
    "grande_recto",
    "oportunidad",
    "yahtzee",
)

TODAS_LAS_CATEGORIAS: tuple[str, ...] = CATEGORIAS_SUPERIORES + CATEGORIAS_INFERIORES

#: Nombres para mostrar en pantalla (iguales a los del tablero de referencia).
NOMBRES: dict[str, str] = {
    "unos": "Unos",
    "doses": "Dos",
    "treses": "Tres",
    "cuatros": "Cuatro",
    "cincos": "Cinco",
    "seises": "Seises",
    "tres_iguales": "Tres iguales",
    "cuatro_iguales": "Cuatro de la misma clase",
    "casa_llena": "Casa llena",
    "pequeno_recto": "Pequeño recto",
    "grande_recto": "Grande y recto",
    "oportunidad": "Oportunidad",
    "yahtzee": "Yahtzee",
}

#: Puntos fijos de las casillas que no dependen de la suma de los dados.
PUNTOS_FIJOS: dict[str, int] = {
    "casa_llena": 25,
    "pequeno_recto": 30,
    "grande_recto": 40,
    "yahtzee": 50,
}

#: Puntos necesarios en la zona superior para ganar el bono.
META_ZONA_SUPERIOR = 63

#: Puntos que otorga el bono de la zona superior.
PUNTOS_BONO = 35

#: Valor que se suma por cada Yahtzee adicional (regla opcional, 0 = desactivada).
BONO_YAHTZEE_ADICIONAL_DEFECTO = 0

# ---------------------------------------------------------------------------
# Combinaciones
# ---------------------------------------------------------------------------

_ESCALERAS_CORTAS = (
    frozenset({1, 2, 3, 4}),
    frozenset({2, 3, 4, 5}),
    frozenset({3, 4, 5, 6}),
)
_ESCALERAS_LARGAS = (
    frozenset({1, 2, 3, 4, 5}),
    frozenset({2, 3, 4, 5, 6}),
)


def es_yahtzee(tirada: Sequence[int]) -> bool:
    """¿Los cinco dados muestran la misma cara?"""
    return len(set(tirada)) == 1


def es_casa_llena(tirada: Sequence[int]) -> bool:
    """¿Hay tres dados de una cara y dos de otra?

    Un Yahtzee (cinco iguales) también cuenta como casa llena, tal como se
    permite en el reglamento clásico.
    """
    conteo = contar_caras(tirada)
    if 5 in conteo:
        return True
    return sorted(conteo, reverse=True)[:2] == [3, 2]


def es_pequeno_recto(tirada: Sequence[int]) -> bool:
    """¿Hay al menos cuatro números consecutivos entre los cinco dados?"""
    caras = set(tirada)
    return any(escalera <= caras for escalera in _ESCALERAS_CORTAS)


def es_grande_recto(tirada: Sequence[int]) -> bool:
    """¿Hay cinco números consecutivos (1-2-3-4-5 ó 2-3-4-5-6)?"""
    caras = set(tirada)
    return any(escalera <= caras for escalera in _ESCALERAS_LARGAS)


def cuantos_iguales(tirada: Sequence[int]) -> int:
    """Tamaño del grupo más grande de dados repetidos."""
    return max(contar_caras(tirada))


# ---------------------------------------------------------------------------
# Cálculo del puntaje
# ---------------------------------------------------------------------------

def puntuar(categoria: str, tirada: Sequence[int]) -> int:
    """Puntaje que se obtiene al anotar esta tirada en esta casilla.

    La función devuelve **0** cuando la combinación no se cumple (en Yahtzee
    la casilla se quema y se anotan cero puntos), nunca ``None``: así el
    llamador siempre suma un número.
    """
    if categoria in CATEGORIAS_SUPERIORES:
        cara = CATEGORIAS_SUPERIORES.index(categoria) + 1
        return sum(valor for valor in tirada if valor == cara)

    if categoria == "tres_iguales":
        return sum(tirada) if cuantos_iguales(tirada) >= 3 else 0

    if categoria == "cuatro_iguales":
        return sum(tirada) if cuantos_iguales(tirada) >= 4 else 0

    if categoria == "casa_llena":
        return PUNTOS_FIJOS["casa_llena"] if es_casa_llena(tirada) else 0

    if categoria == "pequeno_recto":
        return PUNTOS_FIJOS["pequeno_recto"] if es_pequeno_recto(tirada) else 0

    if categoria == "grande_recto":
        return PUNTOS_FIJOS["grande_recto"] if es_grande_recto(tirada) else 0

    if categoria == "oportunidad":
        return sum(tirada)

    if categoria == "yahtzee":
        return PUNTOS_FIJOS["yahtzee"] if es_yahtzee(tirada) else 0

    raise ValueError(f"Categoría desconocida: {categoria!r}")


def se_cumple(categoria: str, tirada: Sequence[int]) -> bool:
    """Indica si la combinación de la casilla se logra con esta tirada.

    Es distinto de ``puntuar(...) > 0``: en las casillas superiores y en
    Oportunidad se puede anotar 0 puntos aunque la jugada sea "válida".
    """
    if categoria in CATEGORIAS_SUPERIORES or categoria == "oportunidad":
        return True
    return puntuar(categoria, tirada) > 0


#: Tabla de funciones de validación, útil para pruebas y para la interfaz.
VALIDADORES: dict[str, Callable[[Sequence[int]], bool]] = {
    "tres_iguales": lambda t: cuantos_iguales(t) >= 3,
    "cuatro_iguales": lambda t: cuantos_iguales(t) >= 4,
    "casa_llena": es_casa_llena,
    "pequeno_recto": es_pequeno_recto,
    "grande_recto": es_grande_recto,
    "oportunidad": lambda t: True,
    "yahtzee": es_yahtzee,
}


def descripcion(categoria: str) -> str:
    """Texto corto que explica cómo se puntúa una casilla."""
    if categoria in CATEGORIAS_SUPERIORES:
        cara = CATEGORIAS_SUPERIORES.index(categoria) + 1
        return f"Suma de los dados con valor {cara}"
    return {
        "tres_iguales": "Suma de los 5 dados (mínimo tres iguales)",
        "cuatro_iguales": "Suma de los 5 dados (mínimo cuatro iguales)",
        "casa_llena": "25 puntos fijos (tres iguales + dos iguales)",
        "pequeno_recto": "30 puntos fijos (cuatro consecutivos)",
        "grande_recto": "40 puntos fijos (cinco consecutivos)",
        "oportunidad": "Suma de los 5 dados, sin condición",
        "yahtzee": "50 puntos fijos (cinco iguales)",
    }[categoria]
