"""Ejecuta todos los experimentos de Montecarlo y genera las gráficas.

Uso::

    python scripts/ejecutar_experimentos.py
    python scripts/ejecutar_experimentos.py --n-max 50000

Los resultados quedan en ``resultados/`` como CSV, JSON y PNG.  Con la misma
semilla el proceso es reproducible: dos ejecuciones producen los mismos
números.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from yahtzee.montecarlo import NIVELES_CONVERGENCIA, ejecutar_todo  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Experimentos de Montecarlo para el Yahtzee")
    parser.add_argument("--n-max", type=int, default=100_000, help="Máximo de partidas por experimento")
    parser.add_argument("--semilla", type=int, default=20262026, help="Semilla del generador aleatorio")
    parser.add_argument("--sin-graficas", action="store_true", help="No generar las gráficas")
    argumentos = parser.parse_args()

    niveles = [n for n in NIVELES_CONVERGENCIA if n <= argumentos.n_max]
    if argumentos.n_max not in niveles:
        niveles.append(argumentos.n_max)

    inicio = time.perf_counter()
    print("=" * 78)
    print(f"  EXPERIMENTOS DE MONTECARLO - Yahtzee  (semilla {argumentos.semilla})")
    print(f"  Niveles de N: {niveles}")
    print("=" * 78)

    resultados = ejecutar_todo(
        RAIZ / "resultados",
        niveles=niveles,
        semilla=argumentos.semilla,
        n_dos_jugadores=min(5_000, argumentos.n_max),
        n_categorias=min(5_000, argumentos.n_max),
    )

    if not argumentos.sin_graficas:
        try:
            from yahtzee.graficas import generar_todas

            print("\nGenerando gráficas...")
            generar_todas(RAIZ / "resultados", resultados)
        except ImportError as error:
            print(f"No se pudieron generar las gráficas: {error}")

    print(f"\nListo. Duración total: {time.perf_counter() - inicio:.1f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
