"""Yahtzee Montecarlo: simulación del juego clásico y estudio de la
Teoría de los Grandes Números mediante el método de Montecarlo.

Uso rápido::

    from yahtzee import Partida, Jugador, EstrategiaHeuristica, simular_puntajes

    puntajes = simular_puntajes(10_000, "heuristica")
"""

from .dados import (
    CARAS_POR_DADO,
    DADOS_POR_TIRADA,
    LANZAMIENTOS_POR_TURNO,
    PROBABILIDAD_CARA,
    contar_caras,
    lanzar_dado,
    lanzar_dados,
    relanzar,
)
from .puntuacion import (
    CATEGORIAS_INFERIORES,
    CATEGORIAS_SUPERIORES,
    META_ZONA_SUPERIOR,
    NOMBRES,
    PUNTOS_BONO,
    TODAS_LAS_CATEGORIAS,
    puntuar,
)
from .tabla import TablaPuntaje
from .estrategias import (
    Estrategia,
    EstrategiaAleatoria,
    EstrategiaHeuristica,
    EstrategiaManual,
    crear_estrategia,
)
from .juego import Jugador, Partida, ResultadoPartida, Turno, jugar_partida
from .montecarlo import (
    Estadistica,
    NIVELES_CONVERGENCIA,
    SEMILLA_DEFECTO,
    ejecutar_todo,
    experimento_categorias,
    experimento_convergencia,
    experimento_dos_jugadores,
    experimento_uniformidad,
    media_acumulada,
    simular_puntajes,
)

__version__ = "1.0.0"

__all__ = [
    "CARAS_POR_DADO",
    "DADOS_POR_TIRADA",
    "LANZAMIENTOS_POR_TURNO",
    "PROBABILIDAD_CARA",
    "contar_caras",
    "lanzar_dado",
    "lanzar_dados",
    "relanzar",
    "CATEGORIAS_INFERIORES",
    "CATEGORIAS_SUPERIORES",
    "META_ZONA_SUPERIOR",
    "NOMBRES",
    "PUNTOS_BONO",
    "TODAS_LAS_CATEGORIAS",
    "puntuar",
    "TablaPuntaje",
    "Estrategia",
    "EstrategiaAleatoria",
    "EstrategiaHeuristica",
    "EstrategiaManual",
    "crear_estrategia",
    "Jugador",
    "Partida",
    "ResultadoPartida",
    "Turno",
    "jugar_partida",
    "Estadistica",
    "NIVELES_CONVERGENCIA",
    "SEMILLA_DEFECTO",
    "ejecutar_todo",
    "experimento_categorias",
    "experimento_convergencia",
    "experimento_dos_jugadores",
    "experimento_uniformidad",
    "media_acumulada",
    "simular_puntajes",
]
