"""Generación de las gráficas del informe.

Se usa **Pillow** en lugar de matplotlib para que el proyecto funcione incluso
en equipos sin acceso a PyPI (que es el caso del equipo donde se desarrolló).
Pillow viene incluido en la mayoría de instalaciones de Python y, si falta,
basta con ``pip install pillow``.

Todas las figuras se construyen a partir de los datos reales que deja el
experimento en ``resultados/resumen_experimentos.json``; nunca se inventan
números.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Paleta y tipografía
# ---------------------------------------------------------------------------

AZUL = (26, 82, 138)
AZUL_CLARO = (91, 155, 213)
NARANJA = (214, 108, 24)
VERDE = (39, 145, 85)
ROJO = (176, 42, 42)
GRIS = (110, 118, 128)
GRIS_CLARO = (226, 230, 235)
GRIS_MUY_CLARO = (243, 245, 248)
NEGRO = (30, 34, 40)
BLANCO = (255, 255, 255)

_RUTAS_FUENTES = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
_RUTAS_FUENTES_NEGRITA = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

_CACHE_FUENTES: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def fuente(tamano: int, negrita: bool = False) -> ImageFont.FreeTypeFont:
    """Devuelve una fuente TrueType; si no hay ninguna, cae en la de Pillow."""
    clave = (tamano, negrita)
    if clave in _CACHE_FUENTES:
        return _CACHE_FUENTES[clave]
    for ruta in _RUTAS_FUENTES_NEGRITA if negrita else _RUTAS_FUENTES:
        try:
            seleccionada = ImageFont.truetype(ruta, tamano)
            _CACHE_FUENTES[clave] = seleccionada
            return seleccionada
        except OSError:
            continue
    por_defecto = ImageFont.load_default(size=tamano)
    _CACHE_FUENTES[clave] = por_defecto  # type: ignore[assignment]
    return por_defecto  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Lienzo con ejes
# ---------------------------------------------------------------------------

class Lienzo:
    """Lienzo blanco con un sistema de ejes cartesianos."""

    def __init__(self, titulo: str, subtitulo: str = "", ancho: int = 1600, alto: int = 880) -> None:
        self.ancho = ancho
        self.alto = alto
        self.img = Image.new("RGB", (ancho, alto), BLANCO)
        self.dibujo = ImageDraw.Draw(self.img)
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.izquierda = 150
        self.derecha = 240
        self.arriba = 160
        self.abajo = 130
        self._xmin = 0.0
        self._xmax = 1.0
        self._ymin = 0.0
        self._ymax = 1.0
        self._log_x = False
        self._log_y = False
        self._leyenda: list[tuple[str, tuple[int, int, int], str]] = []
        self._dibujar_encabezado()

    # -- geometría ---------------------------------------------------------

    @property
    def area(self) -> tuple[int, int, int, int]:
        return (self.izquierda, self.arriba, self.ancho - self.derecha, self.alto - self.abajo)

    def limites(
        self,
        xmin: float,
        xmax: float,
        ymin: float,
        ymax: float,
        log_x: bool = False,
        log_y: bool = False,
    ) -> None:
        self._xmin, self._xmax = xmin, xmax
        self._ymin, self._ymax = ymin, ymax
        self._log_x, self._log_y = log_x, log_y

    def _u(self, valor: float, minimo: float, maximo: float, log: bool) -> float:
        if log:
            valor, minimo, maximo = math.log10(max(valor, 1e-12)), math.log10(max(minimo, 1e-12)), math.log10(max(maximo, 1e-12))
        if maximo == minimo:
            return 0.0
        return (valor - minimo) / (maximo - minimo)

    def px(self, x: float, y: float) -> tuple[float, float]:
        x0, y0, x1, y1 = self.area
        u = self._u(x, self._xmin, self._xmax, self._log_x)
        v = self._u(y, self._ymin, self._ymax, self._log_y)
        return (x0 + u * (x1 - x0), y1 - v * (y1 - y0))

    # -- texto -------------------------------------------------------------

    def _dibujar_encabezado(self) -> None:
        self.dibujo.text((self.ancho / 2, 48), self.titulo, font=fuente(38, True), fill=NEGRO, anchor="mm")
        if self.subtitulo:
            self.dibujo.text((self.ancho / 2, 98), self.subtitulo, font=fuente(24), fill=GRIS, anchor="mm")

    def texto_vertical(self, centro: tuple[float, float], texto: str, tamano: int = 24) -> None:
        f = fuente(tamano)
        caja = self.dibujo.textbbox((0, 0), texto, font=f)
        ancho, alto = caja[2] - caja[0], caja[3] - caja[1]
        capa = Image.new("RGBA", (ancho + 12, alto + 12), (0, 0, 0, 0))
        ImageDraw.Draw(capa).text((6, 6), texto, font=f, fill=NEGRO)
        capa = capa.rotate(90, expand=True)
        self.img.paste(capa, (int(centro[0] - capa.width / 2), int(centro[1] - capa.height / 2)), capa)

    # -- ejes --------------------------------------------------------------

    def ejes(
        self,
        xticks: Sequence[float],
        yticks: Sequence[float],
        etiqueta_x: str,
        etiqueta_y: str,
        etiquetas_x: Sequence[str] | None = None,
        formato_y: str = "{:.0f}",
        tamano_tick: int = 21,
    ) -> None:
        x0, y0, x1, y1 = self.area
        # Malla horizontal
        for valor in yticks:
            _, py = self.px(self._xmin, valor)
            self.dibujo.line([(x0, py), (x1, py)], fill=GRIS_CLARO, width=2)
            self.dibujo.text((x0 - 18, py), formato_y.format(valor), font=fuente(tamano_tick), fill=GRIS, anchor="rm")
        # Malla vertical
        for indice, valor in enumerate(xticks):
            px, _ = self.px(valor, self._ymin)
            self.dibujo.line([(px, y1), (px, y1 + 10)], fill=GRIS, width=2)
            etiqueta = etiquetas_x[indice] if etiquetas_x else f"{valor:g}"
            self.dibujo.text((px, y1 + 22), etiqueta, font=fuente(tamano_tick), fill=GRIS, anchor="ma")
        # Marco
        self.dibujo.line([(x0, y0), (x0, y1)], fill=GRIS, width=3)
        self.dibujo.line([(x0, y1), (x1, y1)], fill=GRIS, width=3)
        # Títulos de los ejes
        self.dibujo.text(((x0 + x1) / 2, y1 + 82), etiqueta_x, font=fuente(24, True), fill=NEGRO, anchor="mm")
        self.texto_vertical((52, (y0 + y1) / 2), etiqueta_y, 24)

    # -- primitivas de datos ----------------------------------------------

    def curva(
        self,
        xs: Sequence[float],
        ys: Sequence[float],
        color: tuple[int, int, int],
        grosor: int = 5,
        etiqueta: str | None = None,
        puntos: bool = False,
        estilo: str = "solido",
    ) -> None:
        pares = [self.px(x, y) for x, y in zip(xs, ys)]
        if len(pares) >= 2:
            self.dibujo.line(pares, fill=color, width=grosor, joint="curve")
        if puntos:
            for (x, y) in pares:
                self.dibujo.ellipse([x - 6, y - 6, x + 6, y + 6], fill=color)
        if etiqueta:
            self._leyenda.append((etiqueta, color, estilo))

    def hline(
        self,
        y: float,
        color: tuple[int, int, int],
        grosor: int = 3,
        etiqueta: str | None = None,
        lado: str = "derecha",
    ) -> None:
        x0, _, x1, _ = self.area
        _, py = self.px(self._xmin, y)
        # línea discontinua
        x = x0
        while x < x1:
            self.dibujo.line([(x, py), (min(x + 16, x1), py)], fill=color, width=grosor)
            x += 28
        if etiqueta:
            if lado == "izquierda":
                self.dibujo.text((x0 + 10, py - 16), etiqueta, font=fuente(21, True), fill=color, anchor="ls")
            else:
                self.dibujo.text((x1 - 8, py - 16), etiqueta, font=fuente(21, True), fill=color, anchor="rs")

    def errorbar(
        self,
        xs: Sequence[float],
        ys: Sequence[float],
        errores: Sequence[float],
        color: tuple[int, int, int],
        etiqueta: str | None = None,
        grosor: int = 4,
    ) -> None:
        for x, y, error in zip(xs, ys, errores):
            px, py = self.px(x, y)
            _, py_bajo = self.px(x, y - error)
            _, py_alto = self.px(x, y + error)
            self.dibujo.line([(px, py_bajo), (px, py_alto)], fill=color, width=grosor)
            self.dibujo.line([(px - 9, py_alto), (px + 9, py_alto)], fill=color, width=grosor)
            self.dibujo.line([(px - 9, py_bajo), (px + 9, py_bajo)], fill=color, width=grosor)
            self.dibujo.ellipse([px - 7, py - 7, px + 7, py + 7], fill=color)
        if etiqueta:
            self._leyenda.append((etiqueta, color, "punto"))

    def barra(
        self,
        x_izq: float,
        x_der: float,
        altura: float,
        color: tuple[int, int, int],
        base: float | None = None,
        borde: tuple[int, int, int] | None = None,
    ) -> None:
        base = self._ymin if base is None else base
        ix, iy = self.px(x_izq, base)
        fx, fy = self.px(x_der, altura)
        self.dibujo.rectangle([ix, fy, fx, iy], fill=color, outline=borde or color, width=2)

    def anotar(
        self,
        x: float,
        y: float,
        texto: str,
        color: tuple[int, int, int] = NEGRO,
        tamano: int = 22,
        anclaje: str = "mm",
        fondo: tuple[int, int, int] | None = None,
    ) -> None:
        px, py = self.px(x, y)
        f = fuente(tamano, True)
        if fondo is not None:
            caja = self.dibujo.textbbox((px, py), texto, font=f, anchor=anclaje)
            self.dibujo.rectangle([caja[0] - 8, caja[1] - 5, caja[2] + 8, caja[3] + 5], fill=fondo)
        self.dibujo.text((px, py), texto, font=f, fill=color, anchor=anclaje)

    def leyenda(self, posicion: str = "superior derecha") -> None:
        if not self._leyenda:
            return
        f = fuente(22)
        alto_linea = 38
        ancho_caja = 0
        for texto, _, _ in self._leyenda:
            caja = self.dibujo.textbbox((0, 0), texto, font=f)
            ancho_caja = max(ancho_caja, caja[2] - caja[0])
        ancho_caja += 90
        alto_caja = alto_linea * len(self._leyenda) + 26
        x0, y0, x1, y1 = self.area
        if "superior" in posicion:
            x, y = x1 - ancho_caja - 24, y0 + 18
        else:
            x, y = x0 + 30, y1 - alto_caja - 24
        self.dibujo.rounded_rectangle(
            [x, y, x + ancho_caja, y + alto_caja], radius=12, fill=(255, 255, 255), outline=GRIS_CLARO, width=2
        )
        for indice, (texto, color, estilo) in enumerate(self._leyenda):
            cy = y + 20 + indice * alto_linea + alto_linea / 2
            if estilo == "punto":
                self.dibujo.ellipse([x + 18, cy - 8, x + 34, cy + 8], fill=color)
            else:
                self.dibujo.line([(x + 16, cy), (x + 52, cy)], fill=color, width=6)
            self.dibujo.text((x + 64, cy), texto, font=f, fill=NEGRO, anchor="lm")

    def guardar(self, ruta: Path) -> Path:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(ruta, format="PNG", optimize=True)
        return ruta


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

def cargar_resultados(directorio: Path, resultados: dict | None = None) -> dict:
    """Carga el JSON de resultados (o usa el diccionario que se le pase)."""
    if resultados is not None:
        return resultados
    ruta = Path(directorio) / "resumen_experimentos.json"
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta}. Ejecuta primero: python scripts/ejecutar_experimentos.py"
        )
    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def _separar_miles(valor: float) -> str:
    return f"{int(valor):,}".replace(",", ".")


def _etiqueta_n(n: float) -> str:
    if n >= 1000:
        return f"{n / 1000:g}k"
    return f"{n:g}"


def _paso_agradable(valor: float, objetivo: int = 5) -> float:
    """Devuelve un paso "redondo" (1, 2, 2.5, 5, 10...) para los ejes."""
    if valor <= 0:
        return 1.0
    bruto = valor / objetivo
    magnitud = 10 ** math.floor(math.log10(bruto))
    for multiplo in (1, 2, 2.5, 5, 10):
        if bruto <= multiplo * magnitud:
            return multiplo * magnitud
    return 10 * magnitud


def _ticks_agradables(maximo: float, objetivo: int = 5) -> list[float]:
    """Lista de marcas de eje terminadas en cifras redondas."""
    paso = _paso_agradable(maximo, objetivo)
    cantidad = int(maximo / paso) + 1
    return [indice * paso for indice in range(cantidad + 1)]


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

def figura_convergencia(datos: dict, directorio: Path) -> Path:
    """Media acumulada del puntaje: la evidencia visual de los Grandes Números."""
    lienzo = Lienzo(
        "Convergencia del puntaje promedio (Teoría de los Grandes Números)",
        "Cada partida es un experimento aleatorio; el promedio se estabiliza al crecer N",
    )
    convergencia = datos["convergencia"]
    final_heuristica = convergencia["heuristica"]["estadistica_final"]["media"]

    ys_todas = []
    for nombre, color in (("aleatoria", GRIS), ("heuristica", AZUL)):
        serie = convergencia[nombre]
        ys_todas.extend(serie["curva_y"])
        lienzo._leyenda.append((f"Estrategia {nombre}", color, "solido"))

    ymin = 0
    ymax = max(ys_todas) * 1.12
    n_maximo = max(convergencia["heuristica"]["curva_x"])
    lienzo.limites(1, n_maximo, ymin, ymax, log_x=True)

    ticks = [n for n in (1, 10, 100, 1_000, 10_000, 100_000) if n <= n_maximo]
    lienzo.ejes(ticks, [0, 50, 100, 150, 200, 250], "Número de partidas simuladas (N)", "Puntaje promedio", _etiquetas(ticks))

    for nombre, color in (("aleatoria", GRIS), ("heuristica", AZUL)):
        serie = convergencia[nombre]
        lienzo.curva(serie["curva_x"], serie["curva_y"], color, 5)

    lienzo.hline(final_heuristica, NARANJA, 3, f"media final ≈ {final_heuristica:.1f}")
    lienzo.anotar(
        n_maximo,
        convergencia["aleatoria"]["estadistica_final"]["media"],
        f"  {convergencia['aleatoria']['estadistica_final']['media']:.1f}",
        GRIS,
        24,
        "lm",
        BLANCO,
    )
    lienzo.leyenda("inferior derecha")
    return lienzo.guardar(Path(directorio) / "fig01_convergencia_media.png")


def max_cx(datos: dict) -> int:
    return max(datos["convergencia"]["heuristica"]["curva_x"])


def _etiquetas(ticks: Sequence[int]) -> list[str]:
    return [_etiqueta_n(t) for t in ticks]


def figura_uniformidad(datos: dict, directorio: Path) -> Path:
    """Frecuencia observada de cada cara frente a la probabilidad teórica 1/6."""
    filas = datos["uniformidad"]
    niveles = sorted({fila["n_tiradas"] for fila in filas})
    n_pequeno, n_grande = niveles[0], niveles[-1]

    def frecuencias(n: int) -> list[float]:
        return [fila["frecuencia"] for fila in filas if fila["n_tiradas"] == n]

    pequeno, grande = frecuencias(n_pequeno), frecuencias(n_grande)

    lienzo = Lienzo(
        "Uniformidad de los dados: la frecuencia converge a 1/6",
        f"Comparación entre N = {_separar_miles(n_pequeno)} y N = {_separar_miles(n_grande)} tiradas de 5 dados",
    )
    lienzo.limites(0, 6, 0.10, 0.24)
    lienzo.ejes([1, 2, 3, 4, 5, 6], [0.10, 0.14, 0.18, 0.22], "Cara del dado", "Frecuencia relativa", formato_y="{:.2f}")

    for indice in range(6):
        centro = indice + 1
        lienzo.barra(centro - 0.38, centro - 0.04, pequeno[indice], GRIS_CLARO, borde=GRIS)
        lienzo.barra(centro + 0.04, centro + 0.38, grande[indice], AZUL)
        lienzo.anotar(centro - 0.21, pequeno[indice] + 0.004, f"{pequeno[indice]:.3f}", GRIS, 18)
        lienzo.anotar(centro + 0.21, grande[indice] + 0.004, f"{grande[indice]:.3f}", AZUL, 18)

    lienzo.hline(1 / 6, NARANJA, 3)
    lienzo._leyenda = [
        (f"N = {_separar_miles(n_pequeno)}", GRIS_CLARO, "solido"),
        (f"N = {_separar_miles(n_grande)}", AZUL, "solido"),
        ("Teórica 1/6 ≈ 0,1667", NARANJA, "solido"),
    ]
    lienzo.leyenda("superior derecha")
    return lienzo.guardar(Path(directorio) / "fig02_uniformidad_dados.png")


def figura_intervalos(datos: dict, directorio: Path) -> Path:
    """El intervalo de confianza se estrecha como 1/√N."""
    lienzo = Lienzo(
        "Precisión del estimador: el intervalo de confianza se estrecha",
        "Estrategia heurística. Media ± 1,96 · s/√N para distintos tamaños de muestra",
    )
    convergencia = datos["convergencia"]
    serie = convergencia["heuristica"]["niveles"]
    xs = [fila["nivel"] for fila in serie]
    ys = [fila["media"] for fila in serie]
    errores = [fila["ic95_superior"] - fila["media"] for fila in serie]
    xmax = max(xs)

    lienzo.limites(60, xmax * 1.7, 200, 220, log_x=True)
    ticks = [n for n in (100, 1_000, 10_000, 100_000) if n <= xmax]
    lienzo.ejes(ticks, [200, 205, 210, 215, 220], "Número de partidas (N)", "Puntaje promedio estimado", _etiquetas(ticks))

    lienzo.errorbar(xs, ys, errores, AZUL, "Media e intervalo de confianza del 95 %")

    ultimo = serie[-1]
    lienzo.anotar(
        ultimo["nivel"],
        ultimo["media"] + 2.4,
        f"N = {_separar_miles(ultimo['nivel'])}\n±{ultimo['ic95_superior'] - ultimo['media']:.2f} puntos",
        AZUL,
        21,
        "mm",
        BLANCO,
    )
    lienzo.leyenda("superior izquierda")
    return lienzo.guardar(Path(directorio) / "fig03_intervalos_confianza.png")


def _histograma(directorio: Path, datos: dict) -> tuple[list[int], float, float]:
    """Cuenta de puntajes por rango: devuelve (conteos, inicio, ancho).

    Si el experimento dejó el archivo ``distribucion_puntajes.csv`` se usa esa
    muestra (miles de partidas); si no, se recurre a la muestra guardada en el
    JSON.
    """
    ruta = Path(directorio) / "distribucion_puntajes.csv"
    if ruta.exists():
        import csv

        with ruta.open(encoding="utf-8") as archivo:
            filas = list(csv.DictReader(archivo))
        conteos = [int(fila["conteo"]) for fila in filas]
        return conteos, float(filas[0]["izquierda"]), float(filas[0]["ancho"])

    muestra = datos["convergencia"]["heuristica"]["puntajes_muestra"]
    ancho = 10
    inicio = (min(muestra) // ancho) * ancho
    conteos = [0] * (((max(muestra) // ancho) * ancho - inicio) // ancho + 1)
    for valor in muestra:
        conteos[(valor // ancho * ancho - inicio) // ancho] += 1
    return conteos, float(inicio), float(ancho)


def figura_distribucion(datos: dict, directorio: Path) -> Path:
    """Forma de la distribución del puntaje por partida."""
    conteos, inicio, ancho = _histograma(directorio, datos)
    media = datos["convergencia"]["heuristica"]["estadistica_final"]["media"]
    n_total = datos["convergencia"]["heuristica"]["estadistica_final"]["n"]

    lienzo = Lienzo(
        "Distribución del puntaje por partida (estrategia heurística)",
        "La forma de campana es la que sostiene el Teorema Central del Límite",
    )
    maximo = max(conteos)
    limite_x = inicio + len(conteos) * ancho
    ticks_y = _ticks_agradables(maximo * 1.12, 5)
    lienzo.limites(inicio, limite_x, 0, ticks_y[-1])
    ticks = list(range(int(inicio), int(limite_x) + 1, 25))
    lienzo.ejes(ticks, ticks_y, "Puntaje obtenido", "Frecuencia absoluta")

    for indice, conteo in enumerate(conteos):
        x_izq = inicio + indice * ancho
        lienzo.barra(x_izq + 1, x_izq + ancho - 1, conteo, AZUL_CLARO, borde=AZUL)

    px, _ = lienzo.px(media, 0)
    for y in range(int(lienzo.area[1]), int(lienzo.area[3]), 22):
        lienzo.dibujo.line([(px, y), (px, y + 11)], fill=NARANJA, width=4)
    lienzo.anotar(
        media,
        ticks_y[-1] * 0.965,
        f"media = {media:.1f}",
        NARANJA,
        22,
        "mb",
        BLANCO,
    )
    lienzo.anotar(
        inicio + (limite_x - inicio) * 0.02,
        ticks_y[-1] * 0.86,
        f"N = {_separar_miles(n_total)} partidas simuladas",
        GRIS,
        21,
        "lm",
        BLANCO,
    )
    return lienzo.guardar(Path(directorio) / "fig04_distribucion_puntajes.png")


def figura_dos_jugadores(datos: dict, directorio: Path) -> Path:
    """En un juego simétrico, la tasa de victorias tiende a 0,5."""
    info = datos["dos_jugadores"]
    curva = info["curva_tasa"]
    desde = min(10, len(curva))
    xs = list(range(desde, len(curva) + 1))
    ys = curva[desde - 1 :]
    lienzo = Lienzo(
        "Dos jugadores con la misma estrategia: la tasa de victorias tiende a 0,5",
        f"{_separar_miles(info['n_partidas'])} partidas. Ningún jugador tiene ventaja: el azar se reparte",
    )
    lienzo.limites(desde, xs[-1], 0.30, 0.70, log_x=True)
    ticks = [n for n in (10, 100, 1_000, 10_000, 100_000) if n <= xs[-1]]
    lienzo.ejes(ticks, [0.30, 0.40, 0.50, 0.60, 0.70], "Número de partidas", "Tasa de victorias del jugador 1", _etiquetas(ticks), "{:.2f}")
    lienzo.curva(xs, ys, VERDE, 4)
    lienzo.hline(0.5, NARANJA, 3, "50 % esperado", lado="izquierda")
    lienzo.anotar(
        xs[-1],
        curva[-1] - 0.035,
        f"valor final: {curva[-1]:.3f}",
        VERDE,
        24,
        "rm",
        BLANCO,
    )
    return lienzo.guardar(Path(directorio) / "fig05_dos_jugadores.png")


def figura_casillas(datos: dict, directorio: Path) -> Path:
    """Aporte promedio de cada casilla al puntaje total."""
    filas = [fila for fila in datos["categorias"] if fila["clave"] != "_resumen"]
    filas.sort(key=lambda fila: fila["puntaje_promedio"])
    maximo = max(fila["puntaje_promedio"] for fila in filas)

    alto = 220 + 44 * len(filas)
    lienzo = Lienzo(
        "Aporte promedio de cada casilla al puntaje final",
        "Estrategia heurística; las barras se ordenan de mayor a menor de arriba hacia abajo",
        ancho=1500,
        alto=alto,
    )
    lienzo.izquierda = 330
    lienzo.derecha = 200
    lienzo.arriba = 150
    lienzo.abajo = 110
    ticks_x = _ticks_agradables(maximo * 1.12, 6)
    lienzo.limites(0, ticks_x[-1], 0, len(filas))
    lienzo.ejes(ticks_x, [], "Puntos promedio por partida", "")

    for indice, fila in enumerate(filas):
        y0 = indice + 0.18
        y1 = indice + 0.82
        valor = fila["puntaje_promedio"]
        color = NARANJA if fila["clave"] in ("unos", "doses", "treses", "cuatros", "cincos", "seises") else AZUL
        lienzo.barra(0, valor, y1, color, base=y0)
        _, py = lienzo.px(valor, (y0 + y1) / 2)
        lienzo.dibujo.text((lienzo.izquierda - 14, py), fila["categoria"], font=fuente(20), fill=NEGRO, anchor="rm")
        lienzo.dibujo.text((lienzo.px(valor, 0)[0] + 10, py), f"{valor:.1f}", font=fuente(20, True), fill=NEGRO, anchor="lm")

    # Leyenda de zonas
    lienzo.dibujo.rectangle([lienzo.ancho - 190, 70, lienzo.ancho - 175, 85], fill=NARANJA)
    lienzo.dibujo.text((lienzo.ancho - 168, 78), "Zona superior", font=fuente(19), fill=NEGRO, anchor="lm")
    lienzo.dibujo.rectangle([lienzo.ancho - 190, 100, lienzo.ancho - 175, 115], fill=AZUL)
    lienzo.dibujo.text((lienzo.ancho - 168, 108), "Zona inferior", font=fuente(19), fill=NEGRO, anchor="lm")
    return lienzo.guardar(Path(directorio) / "fig06_puntaje_por_casilla.png")


def figura_error_estimador(datos: dict, directorio: Path) -> Path:
    """El error estándar cae como 1/√N (recta de pendiente -1/2 en log-log)."""
    lienzo = Lienzo(
        "El error de la estimación disminuye como 1/√N",
        "Doble escala logarítmica: una recta de pendiente -1/2 confirma el Teorema Central del Límite",
        ancho=1500,
        alto=850,
    )
    niveles = datos["convergencia"]["heuristica"]["niveles"]
    xs = [fila["nivel"] for fila in niveles]
    ys = [fila["error_estandar"] for fila in niveles]
    lienzo.limites(min(xs) * 0.7, max(xs) * 1.6, min(ys) / 2.2, max(ys) * 2.0, log_x=True, log_y=True)
    ticks_x = [n for n in (100, 1_000, 10_000, 100_000) if n <= max(xs)]
    ticks_y = [0.1, 0.2, 0.5, 1, 2, 5]
    ticks_y = [valor for valor in ticks_y if min(ys) / 2.2 <= valor <= max(ys) * 2.0]
    lienzo.ejes(ticks_x, ticks_y, "Número de partidas (N)", "Error estándar (puntos)", _etiquetas(ticks_x), "{:g}")
    lienzo.curva(xs, ys, AZUL, 5, None, puntos=True)
    for x, y in zip(xs, ys):
        lienzo.anotar(x, y * 1.35, f"{y:.2f}", AZUL, 19, "mm", BLANCO)
    return lienzo.guardar(Path(directorio) / "fig07_error_estimador.png")


FIGURAS = (
    figura_convergencia,
    figura_uniformidad,
    figura_intervalos,
    figura_distribucion,
    figura_dos_jugadores,
    figura_casillas,
    figura_error_estimador,
)


def generar_todas(directorio: Path, resultados: dict | None = None) -> list[Path]:
    """Genera todas las figuras y devuelve la lista de archivos creados."""
    directorio = Path(directorio)
    datos = cargar_resultados(directorio, resultados)
    rutas = []
    for funcion in FIGURAS:
        try:
            ruta = funcion(datos, directorio)
            rutas.append(ruta)
            print(f"  ✓ {ruta.name}")
        except Exception as error:  # pragma: no cover - una figura no debe romper el resto
            print(f"  ✗ {funcion.__name__}: {error}")
    return rutas


if __name__ == "__main__":  # pragma: no cover
    import sys

    generar_todas(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("resultados"))
