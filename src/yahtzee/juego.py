"""Motor del juego: turnos y partidas.

Un turno de Yahtzee sigue siempre la misma secuencia:

1. Se lanzan los cinco dados.
2. Hasta dos veces más: el jugador decide qué dados conservar y se relanzan
   los demás (máximo tres lanzamientos en total).
3. El jugador elige una casilla libre y anota el puntaje que corresponda.

Una partida de dos jugadores tiene trece rondas; en cada ronda cada jugador
juega un turno.  Gana quien tenga más puntos al final.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Sequence

from .dados import DADOS_POR_TIRADA, LANZAMIENTOS_POR_TURNO, lanzar_dados, relanzar
from .estrategias import Estrategia
from .puntuacion import NOMBRES
from .tabla import TablaPuntaje


@dataclass
class Jugador:
    """Un participante: nombre, estrategia y tabla de puntaje."""

    nombre: str
    estrategia: Estrategia
    tabla: TablaPuntaje = field(default_factory=TablaPuntaje)

    def __post_init__(self) -> None:
        self.tabla.nombre = self.nombre


@dataclass(frozen=True)
class Turno:
    """Registro de un turno jugado (útil para depurar y para el informe)."""

    ronda: int
    jugador: int
    tirada: tuple[int, ...]
    lanzamientos: int
    categoria: str
    puntos: int


@dataclass
class ResultadoPartida:
    """Resultado completo de una partida."""

    nombres: tuple[str, ...]
    puntajes: tuple[int, ...]
    yahtzees: tuple[int, ...]
    turnos: tuple[Turno, ...] = ()

    @property
    def ganador(self) -> int | None:
        """Índice del ganador, o ``None`` si hubo empate."""
        mejor = max(self.puntajes)
        indices = [i for i, puntos in enumerate(self.puntajes) if puntos == mejor]
        return indices[0] if len(indices) == 1 else None

    def resumen(self) -> str:
        """Texto con el marcador final de la partida."""
        lineas = []
        for nombre, puntos, yahtzees in zip(self.nombres, self.puntajes, self.yahtzees):
            extra = f"  (Yahtzees: {yahtzees})" if yahtzees else ""
            lineas.append(f"  {nombre:<22}{puntos:>6} puntos{extra}")
        if self.ganador is None:
            lineas.append("  Resultado: EMPATE")
        else:
            lineas.append(f"  Resultado: gana {self.nombres[self.ganador]}")
        return "\n".join(lineas)


# Tipo del observador opcional que se invoca al final de cada turno.
Observador = Callable[[Turno], None]


class Partida:
    """Una partida de Yahtzee con dos o más jugadores.

    Parameters
    ----------
    jugadores:
        Lista de ``Jugador``; el juego clásico usa dos.
    rng:
        Generador pseudoaleatorio (semilla fija = resultados reproducibles).
    bono_yahtzee_adicional:
        Puntos extra por Yahtzees adicionales (0 = regla desactivada).
    registrar_turnos:
        Si es ``True`` se guarda el detalle de cada turno.  En Montecarlo se
        deja en ``False`` para ahorrar memoria.
    """

    def __init__(
        self,
        jugadores: Sequence[Jugador],
        rng: random.Random | None = None,
        bono_yahtzee_adicional: int = 0,
        registrar_turnos: bool = False,
    ) -> None:
        if len(jugadores) < 1:
            raise ValueError("Se necesita al menos un jugador")
        self.jugadores = list(jugadores)
        self.rng = rng or random.Random()
        self.bono_yahtzee_adicional = bono_yahtzee_adicional
        self.registrar_turnos = registrar_turnos
        self._turnos: list[Turno] = []
        for jugador in self.jugadores:
            jugador.tabla.bono_yahtzee_adicional = bono_yahtzee_adicional

    # -- Turno -------------------------------------------------------------

    def jugar_turno(self, indice: int, ronda: int) -> Turno:
        """Juega un turno completo del jugador ``indice``."""
        jugador = self.jugadores[indice]
        tabla = jugador.tabla
        estrategia = jugador.estrategia

        tirada = lanzar_dados(DADOS_POR_TIRADA, self.rng)
        lanzamientos = 1

        while lanzamientos < LANZAMIENTOS_POR_TURNO:
            restantes = LANZAMIENTOS_POR_TURNO - lanzamientos
            conservar = estrategia.elegir_conservar(tirada, restantes, tabla)
            if len(conservar) >= DADOS_POR_TIRADA:
                break  # el jugador se planta
            tirada = relanzar(tirada, conservar, self.rng)
            lanzamientos += 1

        categoria = estrategia.elegir_categoria(tirada, tabla)
        puntos = tabla.anotar(categoria, tirada)

        turno = Turno(ronda, indice, tuple(tirada), lanzamientos, categoria, puntos)
        if self.registrar_turnos:
            self._turnos.append(turno)
        return turno

    # -- Partida -----------------------------------------------------------

    def jugar(self, observador: Observador | None = None) -> ResultadoPartida:
        """Juega la partida completa y devuelve el resultado."""
        for ronda in range(1, len(self.jugadores[0].tabla.puntos) + 1):
            for indice in range(len(self.jugadores)):
                turno = self.jugar_turno(indice, ronda)
                if observador is not None:
                    observador(turno)

        resultado = ResultadoPartida(
            nombres=tuple(jugador.nombre for jugador in self.jugadores),
            puntajes=tuple(jugador.tabla.total() for jugador in self.jugadores),
            yahtzees=tuple(jugador.tabla.yahtzees for jugador in self.jugadores),
            turnos=tuple(self._turnos),
        )
        return resultado


def jugar_partida(
    estrategias: Sequence[Estrategia],
    rng: random.Random,
    nombres: Sequence[str] | None = None,
    bono_yahtzee_adicional: int = 0,
    registrar_turnos: bool = False,
) -> ResultadoPartida:
    """Atajo para jugar una partida a partir de una lista de estrategias."""
    if nombres is None:
        nombres = [f"Jugador {i + 1}" for i in range(len(estrategias))]
    jugadores = [
        Jugador(nombre, estrategia, TablaPuntaje(nombre))
        for nombre, estrategia in zip(nombres, estrategias)
    ]
    return Partida(jugadores, rng, bono_yahtzee_adicional, registrar_turnos).jugar()


def formatear_turno(turno: Turno, nombre: str) -> str:
    """Línea de texto que describe un turno."""
    from .dados import formatear_tirada

    return (
        f"  {nombre:<18} {formatear_tirada(turno.tirada)}  "
        f"-> {NOMBRES[turno.categoria]:<26} {turno.puntos:>3} pts "
        f"({turno.lanzamientos} lanzamiento{'s' if turno.lanzamientos > 1 else ''})"
    )
