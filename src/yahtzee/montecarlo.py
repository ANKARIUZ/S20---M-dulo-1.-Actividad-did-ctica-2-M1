"""Motor de simulación de Montecarlo.

La idea central del método es sencilla:

> Para estimar una cantidad desconocida, se repite el experimento aleatorio
> muchas veces y se promedian los resultados.

En este proyecto el "experimento" es una partida completa de Yahtzee.  Si se
juegan ``N`` partidas y se anota el puntaje de cada una, el promedio

    X̄_N = (X_1 + X_2 + ... + X_N) / N

es un **estimador de Montecarlo** del puntaje esperado por partida.  La
Teoría de los Grandes Números garantiza que ``X̄_N`` se acerca al valor
verdadero a medida que ``N`` crece, y el Teorema Central del Límite permite
construir el intervalo de confianza del 95 %:

    X̄_N ± 1.96 · s / √N

Este módulo implementa los experimentos y guarda los resultados en CSV/JSON
para que el documento y las gráficas se generen siempre a partir de datos
reales (reproducibles con la misma semilla).
"""

from __future__ import annotations

import csv
import json
import math
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from .dados import CARAS_POR_DADO, PROBABILIDAD_CARA, lanzar_dados
from .estrategias import Estrategia, crear_estrategia
from .juego import jugar_partida
from .puntuacion import NOMBRES, TODAS_LAS_CATEGORIAS

#: Valor crítico de la normal estándar para un intervalo de confianza del 95 %.
Z_95 = 1.959963984540054

#: Semilla por defecto: fija los resultados para que la entrega sea reproducible.
SEMILLA_DEFECTO = 20262026

#: Niveles de N que se usan en el experimento de convergencia.
NIVELES_CONVERGENCIA: tuple[int, ...] = (100, 500, 1_000, 5_000, 10_000, 50_000, 100_000)


# ---------------------------------------------------------------------------
# Estadística descriptiva
# ---------------------------------------------------------------------------

@dataclass
class Estadistica:
    """Resumen estadístico de una muestra de puntajes."""

    n: int
    media: float
    desviacion: float
    error_estandar: float
    ic95_inferior: float
    ic95_superior: float
    minimo: int
    maximo: int

    @classmethod
    def calcular(cls, datos: Sequence[float]) -> "Estadistica":
        n = len(datos)
        if n == 0:
            raise ValueError("La muestra está vacía")
        media = sum(datos) / n
        if n > 1:
            varianza = sum((x - media) ** 2 for x in datos) / (n - 1)
            desviacion = math.sqrt(varianza)
            error = desviacion / math.sqrt(n)
        else:
            desviacion = 0.0
            error = 0.0
        return cls(
            n=n,
            media=media,
            desviacion=desviacion,
            error_estandar=error,
            ic95_inferior=media - Z_95 * error,
            ic95_superior=media + Z_95 * error,
            minimo=min(datos),
            maximo=max(datos),
        )

    def como_dict(self) -> dict[str, float]:
        return {campo: round(valor, 6) if isinstance(valor, float) else valor for campo, valor in asdict(self).items()}


def media_acumulada(datos: Sequence[float]) -> list[float]:
    """Promedio de los primeros ``k`` valores, para cada ``k``.

    Es la curva que se usa para mostrar la convergencia (Teoría de los
    Grandes Números): empieza "loca" y se va estabilizando.
    """
    acumulado = 0.0
    resultado: list[float] = []
    for indice, valor in enumerate(datos, start=1):
        acumulado += valor
        resultado.append(acumulado / indice)
    return resultado


def chi_cuadrado_uniformidad(conteos: Sequence[int]) -> float:
    """Estadístico chi-cuadrado para probar si el dado es equilibrado.

    Grados de libertad = 5; el valor crítico al 5 % es 11,07.  Si el
    estadístico es menor, no hay evidencia para rechazar que el dado sea
    uniforme.
    """
    total = sum(conteos)
    esperado = total / CARAS_POR_DADO
    return sum((observado - esperado) ** 2 / esperado for observado in conteos)


CHI2_CRITICO_5_GL = 11.070


# ---------------------------------------------------------------------------
# Simulación de partidas
# ---------------------------------------------------------------------------

def simular_puntajes(
    n_partidas: int,
    estrategia: str = "heuristica",
    semilla: int = SEMILLA_DEFECTO,
    bono_yahtzee_adicional: int = 0,
    progreso: bool = False,
) -> list[int]:
    """Juega ``n_partidas`` partidas y devuelve el puntaje de cada una.

    Cada partida es de **un solo jugador**.  Se usa un único generador
    aleatorio con semilla fija, de modo que dos ejecuciones con la misma
    semilla producen exactamente los mismos números.
    """
    rng = random.Random(semilla)
    marco = time.perf_counter()
    puntajes: list[int] = []
    for indice in range(1, n_partidas + 1):
        resultado = jugar_partida([crear_estrategia(estrategia, rng)], rng, ["Jugador"], bono_yahtzee_adicional)
        puntajes.append(resultado.puntajes[0])
        if progreso and indice % max(1, n_partidas // 10) == 0:
            transcurrido = time.perf_counter() - marco
            print(f"    {indice:>7,d} / {n_partidas:,d} partidas  ({transcurrido:6.1f} s)", flush=True)
    return puntajes


def simular_partidas_dos_jugadores(
    n_partidas: int,
    estrategia: str = "heuristica",
    semilla: int = SEMILLA_DEFECTO,
    bono_yahtzee_adicional: int = 0,
) -> list[tuple[int, int]]:
    """Devuelve los puntajes ``(jugador_1, jugador_2)`` de cada partida."""
    rng = random.Random(semilla)
    resultados: list[tuple[int, int]] = []
    for _ in range(n_partidas):
        partida = jugar_partida(
            [crear_estrategia(estrategia, rng), crear_estrategia(estrategia, rng)],
            rng,
            ["Jugador 1", "Jugador 2"],
            bono_yahtzee_adicional,
        )
        resultados.append((partida.puntajes[0], partida.puntajes[1]))
    return resultados


# ---------------------------------------------------------------------------
# Experimentos
# ---------------------------------------------------------------------------

@dataclass
class ResultadosExperimentos:
    """Todo lo que produjo una corrida de experimentos."""

    semilla: int
    convergencia: dict[str, dict] = field(default_factory=dict)
    uniformidad: list[dict] = field(default_factory=list)
    dos_jugadores: dict = field(default_factory=dict)
    categorias: list[dict] = field(default_factory=list)
    metadatos: dict = field(default_factory=dict)

    def guardar_json(self, ruta: Path) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(
                {
                    "semilla": self.semilla,
                    "convergencia": self.convergencia,
                    "uniformidad": self.uniformidad,
                    "dos_jugadores": self.dos_jugadores,
                    "categorias": self.categorias,
                    "metadatos": self.metadatos,
                },
                archivo,
                indent=2,
                ensure_ascii=False,
            )


def experimento_uniformidad(niveles: Sequence[int], semilla: int = SEMILLA_DEFECTO) -> list[dict]:
    """Comprueba que los dados son uniformes lanzándolos ``N`` veces.

    Genera ``N`` tiradas de cinco dados (es decir, ``5N`` lanzamientos) y
    calcula la frecuencia relativa de cada cara.  A medida que ``N`` crece,
    las frecuencias deben acercarse a 1/6 ≈ 0,1667 y el estadístico
    chi-cuadrado debe quedar por debajo del valor crítico.
    """
    rng = random.Random(semilla)
    filas: list[dict] = []
    maximo = max(niveles)
    conteo = [0] * CARAS_POR_DADO
    lanzamientos = 0
    niveles_ordenados = sorted(set(niveles))

    siguiente = 0
    while lanzamientos < maximo * 5:
        tirada = lanzar_dados(5, rng)
        for valor in tirada:
            conteo[valor - 1] += 1
        lanzamientos += 5

        while siguiente < len(niveles_ordenados) and lanzamientos >= niveles_ordenados[siguiente] * 5:
            n = niveles_ordenados[siguiente]
            total = float(lanzamientos)
            frecuencias = [cantidad / total for cantidad in conteo]
            desviacion_maxima = max(abs(frecuencia - PROBABILIDAD_CARA) for frecuencia in frecuencias)
            for cara in range(1, CARAS_POR_DADO + 1):
                filas.append(
                    {
                        "n_tiradas": n,
                        "cara": cara,
                        "frecuencia": round(frecuencias[cara - 1], 6),
                        "teorica": round(PROBABILIDAD_CARA, 6),
                        "desviacion": round(frecuencias[cara - 1] - PROBABILIDAD_CARA, 6),
                        "desviacion_maxima": round(desviacion_maxima, 6),
                        "chi2": round(chi_cuadrado_uniformidad(conteo), 4),
                    }
                )
            siguiente += 1
    return filas


def experimento_convergencia(
    niveles: Sequence[int],
    estrategias: Sequence[str] = ("aleatoria", "heuristica"),
    semilla: int = SEMILLA_DEFECTO,
    bono_yahtzee_adicional: int = 0,
    progreso: bool = True,
) -> dict[str, dict]:
    """Estudia cómo se estabiliza el puntaje promedio al crecer ``N``.

    Para no desperdiciar cómputo se juega **una sola vez** el mayor número de
    partidas y luego se toman "prefijos" de esa muestra (las primeras 100,
    500, 1.000...).  Es válido porque el estimador solo usa los primeros
    valores, y es equivalente a hacer simulaciones separadas.
    """
    niveles = sorted(set(niveles))
    n_maximo = max(niveles)
    salida: dict[str, dict] = {}

    for estrategia in estrategias:
        if progreso:
            print(f"  Simulando {n_maximo:,d} partidas con estrategia '{estrategia}'...", flush=True)
        inicio = time.perf_counter()
        puntajes = simular_puntajes(n_maximo, estrategia, semilla, bono_yahtzee_adicional)
        duracion = time.perf_counter() - inicio

        tabla = []
        for nivel in niveles:
            muestra = puntajes[:nivel]
            estadistica = Estadistica.calcular(muestra)
            tabla.append(estadistica.como_dict() | {"nivel": nivel})

        # Curva de convergencia: media acumulada en ~200 puntos (escala log).
        curva_x: list[int] = []
        curva_y: list[float] = []
        paso = max(1, n_maximo // 200)
        acumulado = 0.0
        for indice, valor in enumerate(puntajes, start=1):
            acumulado += valor
            if indice % paso == 0 or indice == 1 or indice == n_maximo:
                curva_x.append(indice)
                curva_y.append(acumulado / indice)

        salida[estrategia] = {
            "n_maximo": n_maximo,
            "duracion_segundos": round(duracion, 2),
            "niveles": tabla,
            "curva_x": curva_x,
            "curva_y": [round(valor, 4) for valor in curva_y],
            "estadistica_final": Estadistica.calcular(puntajes).como_dict(),
            "puntajes_muestra": puntajes[:2000],
        }
        if progreso:
            print(
                f"    media = {Estadistica.calcular(puntajes).media:.2f} puntos "
                f"(error estándar {Estadistica.calcular(puntajes).error_estandar:.3f}) "
                f"en {duracion:.1f} s",
                flush=True,
            )
    return salida


def experimento_dos_jugadores(
    n_partidas: int,
    semilla: int = SEMILLA_DEFECTO,
    bono_yahtzee_adicional: int = 0,
) -> dict:
    """Partidas de dos jugadores con la misma estrategia.

    Si ambos jugadores usan la misma estrategia, el juego es **simétrico**:
    ninguno tiene ventaja.  Por lo tanto la probabilidad de ganar debe ser
    1/2 y la frecuencia observada debe converger a 0,5 (otra manifestación de
    la Teoría de los Grandes Números).
    """
    resultados = simular_partidas_dos_jugadores(n_partidas, "heuristica", semilla, bono_yahtzee_adicional)
    victorias_1 = sum(1 for a, b in resultados if a > b)
    victorias_2 = sum(1 for a, b in resultados if b > a)
    empates = n_partidas - victorias_1 - victorias_2
    diferencias = [a - b for a, b in resultados]
    estadistica = Estadistica.calcular(diferencias)
    return {
        "n_partidas": n_partidas,
        "victorias_jugador_1": victorias_1,
        "victorias_jugador_2": victorias_2,
        "empates": empates,
        "tasa_victoria_jugador_1": victorias_1 / n_partidas,
        "media_jugador_1": sum(a for a, _ in resultados) / n_partidas,
        "media_jugador_2": sum(b for _, b in resultados) / n_partidas,
        "diferencia_media": estadistica.media,
        "diferencia_error_estandar": estadistica.error_estandar,
        "curva_x": list(range(1, n_partidas + 1)),
        "curva_tasa": _tasa_acumulada([1.0 if a > b else 0.0 for a, b in resultados]),
    }


def experimento_distribucion(
    n_partidas: int = 20_000,
    semilla: int = SEMILLA_DEFECTO,
    ancho_rango: int = 10,
) -> list[dict]:
    """Histograma del puntaje por partida, listo para graficar."""
    puntajes = simular_puntajes(n_partidas, "heuristica", semilla)
    inicio = (min(puntajes) // ancho_rango) * ancho_rango
    fin = (max(puntajes) // ancho_rango) * ancho_rango + ancho_rango
    conteos = [0] * ((fin - inicio) // ancho_rango)
    for valor in puntajes:
        conteos[(valor - inicio) // ancho_rango] += 1
    filas = []
    for indice, conteo in enumerate(conteos):
        izquierda = inicio + indice * ancho_rango
        filas.append(
            {
                "izquierda": izquierda,
                "centro": izquierda + ancho_rango / 2,
                "ancho": ancho_rango,
                "conteo": conteo,
            }
        )
    return filas


def _tasa_acumulada(valores: Sequence[float]) -> list[float]:
    acumulado = 0.0
    salida = []
    for indice, valor in enumerate(valores, start=1):
        acumulado += valor
        salida.append(round(acumulado / indice, 6))
    return salida


def experimento_categorias(
    n_partidas: int = 10_000,
    semilla: int = SEMILLA_DEFECTO,
    bono_yahtzee_adicional: int = 0,
) -> list[dict]:
    """Puntaje promedio obtenido en cada casilla y frecuencia de cada logro."""
    rng = random.Random(semilla)
    suma = {categoria: 0 for categoria in TODAS_LAS_CATEGORIAS}
    ceros = {categoria: 0 for categoria in TODAS_LAS_CATEGORIAS}
    bonos = 0
    yahtzees = 0
    puntaje_total = 0

    for _ in range(n_partidas):
        partida = jugar_partida(
            [crear_estrategia("heuristica", rng)], rng, ["Jugador"], bono_yahtzee_adicional, registrar_turnos=True
        )
        tabla = None  # se reconstruye a partir de los turnos
        puntos_por_categoria = {categoria: 0 for categoria in TODAS_LAS_CATEGORIAS}
        for turno in partida.turnos:
            puntos_por_categoria[turno.categoria] = turno.puntos
            if turno.categoria == "yahtzee" and turno.puntos > 0:
                yahtzees += 1
        for categoria, puntos in puntos_por_categoria.items():
            suma[categoria] += puntos
            if puntos == 0:
                ceros[categoria] += 1
        puntaje_total += partida.puntajes[0]

        # El bono se obtiene si la zona superior llega a 63.
        superior = sum(puntos_por_categoria[categoria] for categoria in TODAS_LAS_CATEGORIAS[:6])
        if superior >= 63:
            bonos += 1

    filas = []
    for categoria in TODAS_LAS_CATEGORIAS:
        filas.append(
            {
                "categoria": NOMBRES[categoria],
                "clave": categoria,
                "puntaje_promedio": round(suma[categoria] / n_partidas, 4),
                "frecuencia_cero": round(ceros[categoria] / n_partidas, 4),
                "aporte_al_total": round(suma[categoria] / n_partidas, 4),
            }
        )
    filas.append(
        {
            "categoria": "Resumen",
            "clave": "_resumen",
            "puntaje_promedio": round(puntaje_total / n_partidas, 4),
            "frecuencia_cero": round(1 - bonos / n_partidas, 4),
            "aporte_al_total": round(yahtzees / n_partidas, 4),
        }
    )
    return filas


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

def guardar_csv(filas: Iterable[dict], ruta: Path, campos: Sequence[str] | None = None) -> None:
    """Guarda una lista de diccionarios como CSV."""
    filas = list(filas)
    if not filas:
        return
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if campos is None:
        campos = list(filas[0].keys())
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({campo: fila.get(campo, "") for campo in campos})


def ejecutar_todo(
    directorio: Path,
    niveles: Sequence[int] = NIVELES_CONVERGENCIA,
    semilla: int = SEMILLA_DEFECTO,
    n_dos_jugadores: int = 5_000,
    n_categorias: int = 5_000,
    progreso: bool = True,
) -> ResultadosExperimentos:
    """Corre todos los experimentos y guarda CSV + JSON en ``directorio``."""
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)
    inicio = time.perf_counter()

    if progreso:
        print("\n[1/4] Experimento de convergencia (Teoría de los Grandes Números)")
    convergencia = experimento_convergencia(niveles, ("aleatoria", "heuristica"), semilla, progreso=progreso)

    if progreso:
        print("\n[2/4] Experimento de uniformidad de los dados")
    uniformidad = experimento_uniformidad(niveles, semilla)

    if progreso:
        print("\n[3/4] Experimento de dos jugadores (juego simétrico)")
    dos_jugadores = experimento_dos_jugadores(n_dos_jugadores, semilla)

    if progreso:
        print("\n[4/4] Experimento de puntaje por casilla")
    categorias = experimento_categorias(n_categorias, semilla)

    if progreso:
        print("\n[5/5] Experimento de distribución del puntaje")
    distribucion = experimento_distribucion(min(20_000, max(niveles)), semilla)

    resultados = ResultadosExperimentos(
        semilla=semilla,
        convergencia=convergencia,
        uniformidad=uniformidad,
        dos_jugadores=dos_jugadores,
        categorias=categorias,
        metadatos={
            "duracion_total_segundos": round(time.perf_counter() - inicio, 2),
            "niveles": list(niveles),
            "n_dos_jugadores": n_dos_jugadores,
            "n_categorias": n_categorias,
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
    )

    # CSV de conveniencia para abrir en Excel.
    filas_convergencia = []
    for estrategia, datos in convergencia.items():
        for fila in datos["niveles"]:
            filas_convergencia.append({"estrategia": estrategia} | fila)
    guardar_csv(filas_convergencia, directorio / "convergencia.csv")
    guardar_csv(uniformidad, directorio / "uniformidad_dados.csv")
    guardar_csv(categorias, directorio / "puntaje_por_casilla.csv")
    guardar_csv(distribucion, directorio / "distribucion_puntajes.csv")
    resultados.guardar_json(directorio / "resumen_experimentos.json")

    if progreso:
        print(f"\nResultados guardados en: {directorio}")
    return resultados
