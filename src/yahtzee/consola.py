"""Utilidades de entrada y salida por consola.

Se aíslan aquí para que el resto del programa (juego y Montecarlo) no dependa
de ``input()`` ni de ``print()``: así el motor se puede probar automáticamente
sin intervención humana y se puede reutilizar desde una interfaz web el día de
mañana.
"""

from __future__ import annotations

from typing import Sequence

from .dados import formatear_tirada
from .puntuacion import CATEGORIAS_INFERIORES, CATEGORIAS_SUPERIORES, NOMBRES, descripcion
from .tabla import TablaPuntaje

ANCHO = 78


def linea(caracter: str = "-") -> str:
    return caracter * ANCHO


def titulo(texto: str) -> str:
    return f"\n{linea('=')}\n{texto.center(ANCHO)}\n{linea('=')}"


def mostrar_tirada(tirada: Sequence[int], lanzamientos_usados: int = 1) -> None:
    """Muestra los dados de forma grande y legible."""
    print(f"\n  Dados: {formatear_tirada(tirada)}   (lanzamientos usados: {lanzamientos_usados}/3)")
    conteo = {}
    for valor in tirada:
        conteo[valor] = conteo.get(valor, 0) + 1
    resumen = ", ".join(f"{valor}x{cantidad}" for valor, cantidad in sorted(conteo.items()))
    print(f"  Resumen: {resumen}\n")


def mostrar_tabla(tabla: TablaPuntaje, titulo_tabla: str | None = None) -> None:
    """Imprime el tablero de un jugador."""
    if titulo_tabla:
        print(f"\n{titulo_tabla}")
    print(f"{'Casilla':<28}{'Puntos':>8}")
    print(linea("-"))
    for etiqueta, valor in tabla.filas():
        texto = "-" if valor is None else str(valor)
        print(f"{etiqueta:<28}{texto:>8}")
    print(linea("-"))


def mostrar_categorias_disponibles(tabla: TablaPuntaje, tirada: Sequence[int]) -> dict[int, str]:
    """Lista las casillas libres con el puntaje que darían y devuelve el mapa.

    El mapa va de número de opción a nombre interno de la categoría, para que
    el jugador elija escribiendo un número.
    """
    libres = tabla.categorias_libres()
    opciones: dict[int, str] = {}
    from .puntuacion import puntuar

    print(f"\n{'#':<4}{'Casilla':<30}{'Puntos':>8}   Descripción")
    print(linea("-"))
    for indice, categoria in enumerate(libres, start=1):
        opciones[indice] = categoria
        puntos = puntuar(categoria, tirada)
        zona = "sup" if categoria in CATEGORIAS_SUPERIORES else "inf"
        print(f"{indice:<4}{NOMBRES[categoria] + ' (' + zona + ')':<30}{puntos:>8}   {descripcion(categoria)}")
    print(linea("-"))
    return opciones


def pedir_conservar(tirada: Sequence[int]) -> list[int]:
    """Pregunta qué dados conservar en el próximo lanzamiento.

    El jugador escribe los números de dado que quiere guardar, separados por
    espacios (por ejemplo ``1 3 4``).  Escribir ``0`` significa relanzar todo y
    ``t`` (todos) significa plantarse con la tirada actual.
    """
    while True:
        respuesta = input(
            "\n  ¿Qué dados conservas para el próximo lanzamiento?\n"
            "  (números de dado separados por espacio, '0' = relanzar todo, 't' = plantarse): "
        ).strip().lower()
        if respuesta in ("t", "todo", "todos"):
            return list(tirada)
        if respuesta in ("0", ""):
            return []
        try:
            indices = sorted({int(parte) for parte in respuesta.replace(",", " ").split()})
        except ValueError:
            print("  ⚠ Escribe números separados por espacios.")
            continue
        if any(indice < 1 or indice > len(tirada) for indice in indices):
            print(f"  ⚠ Los dados van del 1 al {len(tirada)}.")
            continue
        return [tirada[indice - 1] for indice in indices]


def pedir_categoria(opciones: dict[int, str]) -> str:
    """Pregunta en qué casilla anotar la tirada."""
    while True:
        respuesta = input("  ¿En qué casilla anotas? (número): ").strip()
        if not respuesta.isdigit() or int(respuesta) not in opciones:
            print("  ⚠ Opción no válida.")
            continue
        return opciones[int(respuesta)]


def pedir_entero(mensaje: str, minimo: int, maximo: int, defecto: int | None = None) -> int:
    """Pide un entero dentro de un rango, con validación."""
    while True:
        sugerencia = f" [{defecto}]" if defecto is not None else ""
        respuesta = input(f"{mensaje}{sugerencia}: ").strip()
        if not respuesta and defecto is not None:
            return defecto
        if respuesta.isdigit() and minimo <= int(respuesta) <= maximo:
            return int(respuesta)
        print(f"  ⚠ Debe ser un número entre {minimo} y {maximo}.")


def pausa(mensaje: str = "  Presiona Enter para continuar...") -> None:
    input(mensaje)


def explicar_categorias_inferiores() -> None:
    """Muestra la ayuda de las casillas de la zona inferior."""
    print("\nCasillas de la zona inferior:")
    for categoria in CATEGORIAS_INFERIORES:
        print(f"  - {NOMBRES[categoria]:<28} {descripcion(categoria)}")
