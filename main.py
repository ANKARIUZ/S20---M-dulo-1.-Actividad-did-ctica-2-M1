"""Punto de entrada del programa.

Uso
---
Menú interactivo (lo más cómodo para explorar el programa)::

    python main.py

Comandos directos::

    python main.py jugar                  # dos jugadores humanos
    python main.py jugar --contra-ia      # humano contra la IA
    python main.py simular --n 10000      # Montecarlo con 10.000 partidas
    python main.py experimentos           # todos los experimentos + gráficas
    python main.py reglas                 # muestra las reglas y el puntaje

El programa no necesita instalación: agrega ``src`` al ``sys.path`` y funciona
desde cualquier carpeta.
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from yahtzee import (  # noqa: E402  (importación después de ajustar sys.path)
    EstrategiaAleatoria,
    EstrategiaHeuristica,
    EstrategiaManual,
    Jugador,
    Partida,
    TablaPuntaje,
    crear_estrategia,
    simular_puntajes,
)
from yahtzee import consola  # noqa: E402
from yahtzee.dados import formatear_tirada  # noqa: E402
from yahtzee.puntuacion import (  # noqa: E402
    CATEGORIAS_INFERIORES,
    CATEGORIAS_SUPERIORES,
    META_ZONA_SUPERIOR,
    NOMBRES,
    PUNTOS_BONO,
    descripcion,
)
from yahtzee.juego import formatear_turno  # noqa: E402

DIRECTORIO_RESULTADOS = RAIZ / "resultados"


# ---------------------------------------------------------------------------
# Utilidades de presentación
# ---------------------------------------------------------------------------

def configurar_consola() -> None:
    """Fuerza UTF-8 para que las tildes y las ñ se vean bien en Windows."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):  # pragma: no cover
            pass


def mostrar_reglas() -> None:
    print(consola.titulo("REGLAS DEL YAHTZEE (2 JUGADORES, 5 DADOS)"))
    print(
        """
  Objetivo: conseguir más puntos que el rival al llenar las 13 casillas.

  Un turno:
    1. Lanzas los 5 dados.
    2. Puedes relanzar los dados que quieras, hasta 2 veces más
       (3 lanzamientos en total).
    3. Eliges una casilla libre y anotas el puntaje correspondiente.

  Zona superior (suma de los dados de esa cara):
"""
    )
    for categoria in CATEGORIAS_SUPERIORES:
        print(f"    - {NOMBRES[categoria]:<10} {descripcion(categoria)}")
    print(
        f"""
  Bono: si la zona superior suma {META_ZONA_SUPERIOR} puntos o más,
        ganas {PUNTOS_BONO} puntos extra.

  Zona inferior:
"""
    )
    for categoria in CATEGORIAS_INFERIORES:
        print(f"    - {NOMBRES[categoria]:<26} {descripcion(categoria)}")
    print(
        """
  La distribución de probabilidad de cada dado es uniforme: P(cara) = 1/6.
  El programa repite partidas miles de veces (Montecarlo) para estimar el
  puntaje esperado y mostrar la Teoría de los Grandes Números.
"""
    )


def narrar_turno(turno) -> None:
    """Imprime un turno cuando juegan dos estrategias automáticas."""
    nombre = f"Jugador {turno.jugador + 1}"
    print(formatear_turno(turno, nombre))


# ---------------------------------------------------------------------------
# Modos de juego
# ---------------------------------------------------------------------------

def jugar_humano_contra_humano() -> None:
    print(consola.titulo("PARTIDA: 2 JUGADORES HUMANOS"))
    nombres = []
    for indice in (1, 2):
        nombre = input(f"  Nombre del jugador {indice}: ").strip() or f"Jugador {indice}"
        nombres.append(nombre)

    jugadores = [
        Jugador(nombres[0], EstrategiaManual(), TablaPuntaje(nombres[0])),
        Jugador(nombres[1], EstrategiaManual(), TablaPuntaje(nombres[1])),
    ]
    partida = Partida(jugadores, random.Random(), registrar_turnos=True)

    for ronda in range(1, 14):
        for indice, jugador in enumerate(jugadores):
            print(consola.titulo(f"RONDA {ronda}/13 - TURNO DE {jugador.nombre.upper()}"))
            print(f"  Puntaje actual: {jugador.tabla.total()} puntos")
            turno = partida.jugar_turno(indice, ronda)
            print(
                f"\n  Anotaste {turno.puntos} puntos en {NOMBRES[turno.categoria]}."
                f"  Total: {jugador.tabla.total()}"
            )
            consola.pausa()

    _finalizar(partida)


def jugar_contra_ia() -> None:
    print(consola.titulo("PARTIDA: HUMANO CONTRA LA IA"))
    nombre = input("  Tu nombre: ").strip() or "Humano"
    jugadores = [
        Jugador(nombre, EstrategiaManual(), TablaPuntaje(nombre)),
        Jugador("IA", EstrategiaHeuristica(), TablaPuntaje("IA")),
    ]
    partida = Partida(jugadores, random.Random(), registrar_turnos=True)

    for ronda in range(1, 14):
        for indice, jugador in enumerate(jugadores):
            print(consola.titulo(f"RONDA {ronda}/13 - TURNO DE {jugador.nombre.upper()}"))
            print(f"  Puntaje actual: {jugador.tabla.total()} puntos")
            turno = partida.jugar_turno(indice, ronda)
            print(
                f"\n  {jugador.nombre} anota {turno.puntos} puntos en "
                f"{NOMBRES[turno.categoria]}  {formatear_tirada(turno.tirada)}"
            )
            if jugador.estrategia is not EstrategiaManual:
                consola.pausa("  Presiona Enter para continuar...")

    _finalizar(partida)


def jugar_ia_contra_ia(narrado: bool = False) -> None:
    print(consola.titulo("PARTIDA: IA CONTRA IA"))
    jugadores = [
        Jugador("IA 1", EstrategiaHeuristica(), TablaPuntaje("IA 1")),
        Jugador("IA 2", EstrategiaHeuristica(), TablaPuntaje("IA 2")),
    ]
    partida = Partida(jugadores, random.Random(), registrar_turnos=True)
    observador = narrar_turno if narrado else None
    resultado = partida.jugar(observador)
    if not narrado:
        for turno in resultado.turnos:
            narrar_turno(turno)
    _finalizar(partida)


def _finalizar(partida: Partida) -> None:
    print(consola.titulo("TABLA FINAL"))
    for jugador in partida.jugadores:
        consola.mostrar_tabla(jugador.tabla, f"  {jugador.nombre.upper()}")
    print(consola.titulo("MARCADOR"))
    for jugador in partida.jugadores:
        print(f"  {jugador.nombre:<22}{jugador.tabla.total():>6} puntos")
    ganadores = [jugador for jugador in partida.jugadores]
    mejor = max(jugador.tabla.total() for jugador in ganadores)
    empatados = [jugador for jugador in ganadores if jugador.tabla.total() == mejor]
    if len(empatados) == 1:
        print(f"\n  ¡Gana {empatados[0].nombre} con {mejor} puntos!")
    else:
        print("\n  Empate.")
    print()
    consola.pausa()


# ---------------------------------------------------------------------------
# Modos de simulación
# ---------------------------------------------------------------------------

def simular(n: int, estrategia: str) -> None:
    print(consola.titulo(f"MONTECARLO: {n:,d} PARTIDAS (estrategia: {estrategia})"))
    inicio = time.perf_counter()
    puntajes = simular_puntajes(n, estrategia, progreso=True)
    duracion = time.perf_counter() - inicio

    media = statistics.mean(puntajes)
    desviacion = statistics.stdev(puntajes) if len(puntajes) > 1 else 0.0
    error = desviacion / (len(puntajes) ** 0.5)
    print(
        f"""
  Resultados de la simulación
  ---------------------------
  Partidas jugadas .......... {n:,d}
  Puntaje promedio .......... {media:8.2f}
  Desviación estándar ....... {desviacion:8.2f}
  Error estándar ............ {error:8.3f}
  Intervalo de confianza 95%  [{media - 1.96 * error:.2f}, {media + 1.96 * error:.2f}]
  Puntaje mínimo ............ {min(puntajes):8d}
  Puntaje máximo ............ {max(puntajes):8d}
  Tiempo de cómputo ......... {duracion:8.2f} s
  Partidas por segundo ...... {n / duracion:8.1f}
  """
    )

    if n >= 100:
        print("  Primeras partidas:", puntajes[:10])
    print(
        "  Interpretación: al aumentar N el promedio se acerca a su valor\n"
        "  esperado y el intervalo de confianza se estrecha (Teoría de los\n"
        "  Grandes Números).\n"
    )


def experimentos(n_max: int) -> None:
    from yahtzee.montecarlo import ejecutar_todo

    niveles = [n for n in (100, 500, 1_000, 5_000, 10_000, 50_000, 100_000) if n <= n_max]
    if n_max not in niveles:
        niveles.append(n_max)
    print(consola.titulo("EXPERIMENTOS COMPLETOS DE MONTECARLO"))
    ejecutar_todo(DIRECTORIO_RESULTADOS, niveles=niveles, n_dos_jugadores=min(5_000, n_max), n_categorias=min(5_000, n_max))
    try:
        from yahtzee.graficas import generar_todas

        generar_todas(DIRECTORIO_RESULTADOS)
        print("  Gráficas generadas en resultados/")
    except ImportError as error:  # pragma: no cover
        print(f"  (No se pudieron generar las gráficas: {error})")


# ---------------------------------------------------------------------------
# Menú interactivo
# ---------------------------------------------------------------------------

def menu() -> None:
    opciones = {
        "1": ("Jugar 2 jugadores (humanos)", jugar_humano_contra_humano),
        "2": ("Jugar contra la IA", jugar_contra_ia),
        "3": ("Ver una partida IA vs IA narrada", lambda: jugar_ia_contra_ia(narrado=True)),
        "4": ("Simulación Montecarlo (N partidas)", _menu_simular),
        "5": ("Experimentos completos + gráficas", _menu_experimentos),
        "6": ("Ver reglas del juego", mostrar_reglas),
        "0": ("Salir", None),
    }
    while True:
        print(consola.titulo("YAHTZEE + MONTECARLO - MENÚ PRINCIPAL"))
        for clave, (texto, _) in opciones.items():
            print(f"   {clave}) {texto}")
        eleccion = input("\n  Elige una opción: ").strip()
        if eleccion == "0":
            print("\n  ¡Hasta pronto!\n")
            return
        accion = opciones.get(eleccion, (None, None))[1]
        if accion is None:
            print("  ⚠ Opción no válida.")
            continue
        try:
            accion()
        except KeyboardInterrupt:
            print("\n  Operación cancelada.")


def _menu_simular() -> None:
    n = consola.pedir_entero("  ¿Cuántas partidas simular?", 10, 1_000_000, 10_000)
    estrategia = input("  Estrategia [h]eurística / [a]leatoria [h]: ").strip().lower() or "h"
    simular(n, "aleatoria" if estrategia.startswith("a") else "heuristica")


def _menu_experimentos() -> None:
    n = consola.pedir_entero("  Máximo de partidas por experimento", 1_000, 200_000, 10_000)
    experimentos(n)


# ---------------------------------------------------------------------------
# Línea de comandos
# ---------------------------------------------------------------------------

def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yahtzee",
        description="Yahtzee clásico + simulación de Montecarlo (Teoría de los Grandes Números).",
    )
    subparsers = parser.add_subparsers(dest="comando")

    jugar = subparsers.add_parser("jugar", help="Jugar una partida")
    jugar.add_argument("--contra-ia", action="store_true", help="Jugar contra la estrategia heurística")
    jugar.add_argument("--auto", action="store_true", help="Ver una partida IA vs IA")

    simular_parser = subparsers.add_parser("simular", help="Simulación de Montecarlo")
    simular_parser.add_argument("--n", type=int, default=10_000, help="Número de partidas (por defecto 10.000)")
    simular_parser.add_argument(
        "--estrategia",
        choices=["heuristica", "aleatoria"],
        default="heuristica",
        help="Estrategia a usar",
    )

    experimentos_parser = subparsers.add_parser("experimentos", help="Correr todos los experimentos y generar gráficas")
    experimentos_parser.add_argument("--n-max", type=int, default=100_000, help="Máximo de partidas (por defecto 100.000)")

    subparsers.add_parser("reglas", help="Mostrar las reglas")
    return parser


def main(argv: list[str] | None = None) -> int:
    configurar_consola()
    parser = construir_parser()
    argumentos = parser.parse_args(argv)

    if argumentos.comando is None:
        menu()
        return 0

    if argumentos.comando == "jugar":
        if argumentos.auto:
            jugar_ia_contra_ia(narrado=True)
        elif argumentos.contra_ia:
            jugar_contra_ia()
        else:
            jugar_humano_contra_humano()
    elif argumentos.comando == "simular":
        simular(argumentos.n, argumentos.estrategia)
    elif argumentos.comando == "experimentos":
        experimentos(argumentos.n_max)
    elif argumentos.comando == "reglas":
        mostrar_reglas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
