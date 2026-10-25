"""Tabla de puntaje de un jugador.

Cada jugador tiene una tabla con trece casillas.  Una casilla empieza vacía
(``None``) y, cuando se anota, guarda un entero.  La tabla sabe calcular por sí
misma la suma de la zona superior, el bono y el total, de modo que el motor del
juego nunca tiene que repetir esas cuentas.
"""

from __future__ import annotations

from typing import Sequence

from .puntuacion import (
    BONO_YAHTZEE_ADICIONAL_DEFECTO,
    CATEGORIAS_INFERIORES,
    CATEGORIAS_SUPERIORES,
    META_ZONA_SUPERIOR,
    NOMBRES,
    PUNTOS_BONO,
    TODAS_LAS_CATEGORIAS,
    puntuar,
)

#: Puntos que, de forma realista, puede aportar una casilla superior libre.
#: Se usa para decidir si el bono de 35 puntos sigue siendo alcanzable.
UMBRAL_PUNTOS_POR_CASILLA = 12.0


class TablaPuntaje:
    """Estado de las trece casillas de un jugador.

    Parameters
    ----------
    nombre:
        Nombre del jugador (solo para mostrar).
    bono_yahtzee_adicional:
        Puntos extra por cada Yahtzee conseguido *después* del primero.
        En el reglamento clásico son 100 puntos; se deja configurable y por
        defecto en 0 para que el tablero coincida con el juego de referencia.
    """

    __slots__ = ("nombre", "puntos", "bono_yahtzee_adicional", "yahtzees", "yahtzees_extra")

    def __init__(self, nombre: str = "Jugador", bono_yahtzee_adicional: int = BONO_YAHTZEE_ADICIONAL_DEFECTO) -> None:
        self.nombre = nombre
        self.puntos: dict[str, int | None] = {categoria: None for categoria in TODAS_LAS_CATEGORIAS}
        self.bono_yahtzee_adicional = bono_yahtzee_adicional
        self.yahtzees = 0
        self.yahtzees_extra = 0

    # -- Consultas ---------------------------------------------------------

    def categorias_libres(self) -> list[str]:
        """Casillas que todavía no se han usado, en el orden del tablero."""
        return [categoria for categoria in TODAS_LAS_CATEGORIAS if self.puntos[categoria] is None]

    def completa(self) -> bool:
        """¿Ya se anotaron las trece casillas?"""
        return all(valor is not None for valor in self.puntos.values())

    def suma_superior(self) -> int:
        """Suma de los puntos anotados en la zona superior."""
        return sum(self.puntos[categoria] or 0 for categoria in CATEGORIAS_SUPERIORES)

    def bono(self) -> int:
        """Bono de 35 puntos si la zona superior alcanza los 63 puntos."""
        return PUNTOS_BONO if self.suma_superior() >= META_ZONA_SUPERIOR else 0

    def total(self) -> int:
        """Puntaje total del jugador (superior + bono + inferior + extras)."""
        return (
            sum(valor or 0 for valor in self.puntos.values())
            + self.bono()
            + self.yahtzees_extra * self.bono_yahtzee_adicional
        )

    def faltan_para_bono(self) -> int:
        """Cuántos puntos le faltan a la zona superior para lograr el bono."""
        return max(0, META_ZONA_SUPERIOR - self.suma_superior())

    def bono_alcanzable(self) -> bool:
        """¿Todavía es realista alcanzar el bono de 35 puntos?

        Se estima que una casilla superior libre puede aportar hasta unos 12
        puntos "razonables" (cuatro dados iguales o cinco del mismo valor).
        Si lo que falta supera esa cota, el bono se da por perdido y la
        estrategia deja de sacrificar puntos por perseguirlo.
        """
        libres = sum(1 for categoria in CATEGORIAS_SUPERIORES if self.puntos[categoria] is None)
        return self.faltan_para_bono() <= UMBRAL_PUNTOS_POR_CASILLA * libres

    # -- Acciones ----------------------------------------------------------

    def anotar(self, categoria: str, tirada: Sequence[int]) -> int:
        """Anota la tirada en la casilla indicada y devuelve los puntos."""
        if categoria not in self.puntos:
            raise ValueError(f"Categoría desconocida: {categoria!r}")
        if self.puntos[categoria] is not None:
            raise ValueError(f"La casilla {NOMBRES[categoria]} ya está ocupada")

        puntos = puntuar(categoria, tirada)
        self.puntos[categoria] = puntos

        if categoria == "yahtzee" and puntos > 0:
            self.yahtzees += 1
        # Bono por Yahtzees adicionales (regla opcional).
        if self.bono_yahtzee_adicional and self.yahtzees >= 1 and categoria != "yahtzee":
            from .puntuacion import es_yahtzee

            if es_yahtzee(tirada):
                self.yahtzees_extra += 1
        return puntos

    # -- Presentación ------------------------------------------------------

    def filas(self) -> list[tuple[str, int | None]]:
        """Filas del tablero tal como se muestran al jugador."""
        filas: list[tuple[str, int | None]] = [(NOMBRES[c], self.puntos[c]) for c in CATEGORIAS_SUPERIORES]
        filas.append(("Suma", self.suma_superior()))
        filas.append(("Bono", self.bono()))
        filas.extend((NOMBRES[c], self.puntos[c]) for c in CATEGORIAS_INFERIORES)
        filas.append(("Puntuación total", self.total()))
        return filas

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"TablaPuntaje({self.nombre!r}, total={self.total()})"
