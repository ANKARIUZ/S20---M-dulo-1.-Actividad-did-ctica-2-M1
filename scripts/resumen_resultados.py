"""Imprime un resumen legible de los resultados guardados en resultados/.

Uso::

    python scripts/resumen_resultados.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))


def cargar_resultados(directorio: Path) -> dict:
    with (Path(directorio) / "resumen_experimentos.json").open(encoding="utf-8") as archivo:
        return json.load(archivo)


def main() -> int:
    datos = cargar_resultados(RAIZ / "resultados")
    print("=" * 78)
    print("  RESUMEN DE LOS EXPERIMENTOS DE MONTECARLO")
    print("=" * 78)

    for estrategia in ("aleatoria", "heuristica"):
        serie = datos["convergencia"][estrategia]
        print(f"\n[{estrategia.upper()}]  (N máximo = {serie['n_maximo']:,})")
        print(f"{'N':>9}{'media':>10}{'desv.':>10}{'error':>9}{'IC95 inf':>11}{'IC95 sup':>11}{'mín':>6}{'máx':>6}")
        for fila in serie["niveles"]:
            print(
                f"{fila['nivel']:>9,}{fila['media']:>10.2f}{fila['desviacion']:>10.2f}"
                f"{fila['error_estandar']:>9.3f}{fila['ic95_inferior']:>11.2f}"
                f"{fila['ic95_superior']:>11.2f}{fila['minimo']:>6}{fila['maximo']:>6}"
            )

    print("\n[UNIFORMIDAD DE LOS DADOS]")
    for n in sorted({fila["n_tiradas"] for fila in datos["uniformidad"]}):
        filas = [fila for fila in datos["uniformidad"] if fila["n_tiradas"] == n]
        frecuencias = "  ".join(f"{fila['frecuencia']:.4f}" for fila in filas)
        print(f"  N={n:>7,} tiradas -> {frecuencias}   chi2={filas[0]['chi2']:.3f}  desv.máx={filas[0]['desviacion_maxima']:.4f}")

    dos = datos["dos_jugadores"]
    print("\n[DOS JUGADORES]")
    print(
        f"  partidas={dos['n_partidas']:,}  victorias J1={dos['victorias_jugador_1']:,}  "
        f"victorias J2={dos['victorias_jugador_2']:,}  empates={dos['empates']:,}  "
        f"tasa J1={dos['tasa_victoria_jugador_1']:.4f}"
    )

    print("\n[PUNTAJE PROMEDIO POR CASILLA]")
    for fila in datos["categorias"]:
        if fila["clave"] == "_resumen":
            continue
        print(f"  {fila['categoria']:<28}{fila['puntaje_promedio']:>8.2f}")
    resumen = next(fila for fila in datos["categorias"] if fila["clave"] == "_resumen")
    print(f"  {'TOTAL POR PARTIDA':<28}{resumen['puntaje_promedio']:>8.2f}")
    print(f"\n  Puntaje medio final (heurística): {datos['convergencia']['heuristica']['estadistica_final']['media']:.2f}")
    print(f"  Puntaje medio final (aleatoria):  {datos['convergencia']['aleatoria']['estadistica_final']['media']:.2f}")
    print(f"  Duración total: {datos['metadatos']['duracion_total_segundos']} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
