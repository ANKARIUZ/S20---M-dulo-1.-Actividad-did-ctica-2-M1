"""Modelo de los dados y de la tirada.

Un dado convencional de seis caras se representa simplemente con un entero de
1 a 6.  Una tirada de Yahtzee es, por tanto, una tupla de cinco enteros, por
ejemplo ``(3, 1, 5, 5, 2)``.

Se trabaja con tuplas inmutables (y no con objetos) por tres razones:

1. Son más rápidas: la simulación de Montecarlo lanza millones de dados.
2. Son *hashables*, lo que permite usarlas como llave de caché.
3. Obligan a no modificar una tirada "por accidente": cada relanzamiento
   devuelve una tirada nueva, lo que evita errores lógicos difíciles de
   encontrar.

La distribución de probabilidad de cada dado es **uniforme discreta**:

    P(X = x) = 1/6  para todo x en {1, 2, 3, 4, 5, 6}

y los cinco dados son independientes entre sí.
"""

from __future__ import annotations

import random
from typing import Sequence

#: Número de caras de un dado convencional.
CARAS_POR_DADO = 6

#: Número de dados que se lanzan en cada turno de Yahtzee.
DADOS_POR_TIRADA = 5

#: Número máximo de lanzamientos permitidos dentro de un turno.
LANZAMIENTOS_POR_TURNO = 3

VALORES_POSIBLES = (1, 2, 3, 4, 5, 6)

#: Probabilidad teórica de obtener una cara cualquiera (distribución uniforme).
PROBABILIDAD_CARA = 1.0 / CARAS_POR_DADO


def lanzar_dado(rng: random.Random) -> int:
    """Devuelve el resultado de lanzar un único dado de seis caras."""
    return rng.randint(1, CARAS_POR_DADO)


def lanzar_dados(cantidad: int = DADOS_POR_TIRADA, rng: random.Random | None = None) -> tuple[int, ...]:
    """Lanza ``cantidad`` dados y devuelve la tirada como una tupla.

    Parameters
    ----------
    cantidad:
        Cuántos dados lanzar (5 en el juego normal).
    rng:
        Generador de números pseudoaleatorios.  Si se omite se usa el
        generador global de Python.  Pasar una instancia de ``random.Random``
        con semilla fija es lo que hace **reproducible** la simulación.
    """
    if rng is None:
        return tuple(random.randint(1, CARAS_POR_DADO) for _ in range(cantidad))
    return tuple(rng.randint(1, CARAS_POR_DADO) for _ in range(cantidad))


def relanzar(tirada: Sequence[int], conservar: Sequence[int], rng: random.Random) -> tuple[int, ...]:
    """Vuelve a lanzar los dados que no se conservan.

    ``conservar`` contiene los *valores* de los dados que el jugador decide
    mantener.  Como el orden de los dados no influye en el puntaje, la tirada
    resultante es simplemente ``conservar + dados nuevos``.
    """
    faltantes = DADOS_POR_TIRADA - len(conservar)
    if faltantes < 0:
        raise ValueError("No se pueden conservar más dados de los que hay en la tirada")
    return tuple(conservar) + lanzar_dados(faltantes, rng)


def contar_caras(tirada: Sequence[int]) -> tuple[int, int, int, int, int, int]:
    """Cuenta cuántas veces aparece cada cara.

    Devuelve una tupla de seis posiciones donde la posición ``i`` corresponde
    a la cara ``i + 1``.  Por ejemplo, para la tirada ``(3, 3, 3, 5, 5)`` el
    resultado es ``(0, 0, 3, 0, 2, 0)``.
    """
    unos = doses = treses = cuatros = cincos = seises = 0
    for valor in tirada:
        if valor == 1:
            unos += 1
        elif valor == 2:
            doses += 1
        elif valor == 3:
            treses += 1
        elif valor == 4:
            cuatros += 1
        elif valor == 5:
            cincos += 1
        else:
            seises += 1
    return (unos, doses, treses, cuatros, cincos, seises)


def frecuencia_relativa(tiradas: Sequence[Sequence[int]]) -> list[float]:
    """Frecuencia observada de cada cara en un conjunto de tiradas.

    Es el estimador de Montecarlo de la probabilidad de cada cara:
    ``frecuencia(cara) = apariciones(cara) / total_de_dados``.
    """
    conteo = [0] * CARAS_POR_DADO
    total = 0
    for tirada in tiradas:
        for valor in tirada:
            conteo[valor - 1] += 1
            total += 1
    if total == 0:
        return [0.0] * CARAS_POR_DADO
    return [c / total for c in conteo]


def formatear_tirada(tirada: Sequence[int], sep: str = " ") -> str:
    """Devuelve la tirada en un formato legible: ``[3] [1] [5] [5] [2]``."""
    return sep.join(f"[{valor}]" for valor in tirada)
