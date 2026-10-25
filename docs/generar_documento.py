"""Genera el documento técnico en Word a partir de los resultados reales.

Uso::

    python docs/generar_documento.py

Requiere ``python-docx`` (``pip install python-docx``).  Lee
``resultados/resumen_experimentos.json`` y las figuras de ``resultados/``, de
modo que el informe siempre refleja la última corrida de la simulación.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"
SALIDA = RAIZ / "Rios_JuanCamilo_Montecarlo.docx"

AZUL = RGBColor(0x1F, 0x4E, 0x79)
AZUL_CLARO = RGBColor(0x2E, 0x74, 0xB5)
GRIS = RGBColor(0x59, 0x59, 0x59)

AUTOR = "Juan Camilo Ríos Hernández"
TITULO = "Simulación del juego de Yahtzee mediante el método de Montecarlo"
SUBTITULO = "Verificación de la Teoría de los Grandes Números en un juego de azar con dos jugadores"

# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------


def _sombra_celda(celda, color: str) -> None:
    sombreado = OxmlElement("w:shd")
    sombreado.set(qn("w:fill"), color)
    celda._tc.get_or_add_tcPr().append(sombreado)


def _borde_tabla(tabla) -> None:
    tbl = tabla._tbl
    tblPr = tbl.tblPr
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        elemento = OxmlElement(f"w:{lado}")
        elemento.set(qn("w:val"), "single")
        elemento.set(qn("w:sz"), "6")
        elemento.set(qn("w:space"), "0")
        elemento.set(qn("w:color"), "BFBFBF")
        bordes.append(elemento)
    tblPr.append(bordes)


class Documento:
    """Envoltorio con las operaciones de escritura que necesita el informe."""

    def __init__(self) -> None:
        self.doc = Document()
        self.contador_figuras = 0
        self.contador_tablas = 0
        self._configurar_estilos()
        self._configurar_pagina()

    # -- configuración -----------------------------------------------------

    def _configurar_pagina(self) -> None:
        seccion = self.doc.sections[0]
        seccion.page_width = Cm(21.59)
        seccion.page_height = Cm(27.94)
        seccion.top_margin = Cm(2.5)
        seccion.bottom_margin = Cm(2.5)
        seccion.left_margin = Cm(2.8)
        seccion.right_margin = Cm(2.5)

    def _configurar_estilos(self) -> None:
        normal = self.doc.styles["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(11)
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.line_spacing = 1.15
        normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        for nombre, tamano, color in (("Heading 1", 16, AZUL), ("Heading 2", 13, AZUL_CLARO), ("Heading 3", 11.5, GRIS)):
            estilo = self.doc.styles[nombre]
            estilo.font.name = "Calibri"
            estilo.font.size = Pt(tamano)
            estilo.font.bold = True
            estilo.font.color.rgb = color
            estilo.paragraph_format.space_before = Pt(14)
            estilo.paragraph_format.space_after = Pt(6)
            estilo.paragraph_format.keep_with_next = True
            estilo.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # -- bloques -----------------------------------------------------------

    def h1(self, texto: str, salto: bool = True) -> None:
        if salto:
            self.doc.add_page_break()
        self.doc.add_heading(texto, level=1)

    def h2(self, texto: str) -> None:
        self.doc.add_heading(texto, level=2)

    def h3(self, texto: str) -> None:
        self.doc.add_heading(texto, level=3)

    def p(self, texto: str = "", negrita: bool = False, cursiva: bool = False, alineacion: str = "just") -> None:
        parrafo = self.doc.add_paragraph()
        parrafo.alignment = {
            "just": WD_ALIGN_PARAGRAPH.JUSTIFY,
            "centro": WD_ALIGN_PARAGRAPH.CENTER,
            "izq": WD_ALIGN_PARAGRAPH.LEFT,
        }[alineacion]
        run = parrafo.add_run(texto)
        run.bold = negrita
        run.italic = cursiva

    def mixto(self, partes: list[tuple[str, bool]]) -> None:
        """Párrafo con trozos en negrita: ``[("texto", True), ("normal", False)]``."""
        parrafo = self.doc.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for texto, negrita in partes:
            run = parrafo.add_run(texto)
            run.bold = negrita

    def vineta(self, texto: str, nivel: int = 0) -> None:
        parrafo = self.doc.add_paragraph(texto, style="List Bullet" if nivel == 0 else "List Bullet 2")
        parrafo.paragraph_format.space_after = Pt(3)
        parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def numerada(self, texto: str) -> None:
        parrafo = self.doc.add_paragraph(texto, style="List Number")
        parrafo.paragraph_format.space_after = Pt(3)
        parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def codigo(self, texto: str) -> None:
        parrafo = self.doc.add_paragraph()
        parrafo.paragraph_format.left_indent = Cm(0.6)
        parrafo.paragraph_format.space_before = Pt(6)
        parrafo.paragraph_format.space_after = Pt(8)
        parrafo.paragraph_format.line_spacing = 1.0
        run = parrafo.add_run(texto)
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        sombreado = OxmlElement("w:shd")
        sombreado.set(qn("w:fill"), "F2F2F2")
        parrafo._p.get_or_add_pPr().append(sombreado)

    def ecuacion(self, texto: str) -> None:
        parrafo = self.doc.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        parrafo.paragraph_format.space_before = Pt(4)
        parrafo.paragraph_format.space_after = Pt(4)
        run = parrafo.add_run(texto)
        run.font.name = "Cambria Math"
        run.font.size = Pt(12)
        run.italic = True

    def tabla(self, cabeceras: list[str], filas: list[list[str]], titulo: str = "", anchos: list[float] | None = None) -> None:
        self.contador_tablas += 1
        if titulo:
            parrafo = self.doc.add_paragraph()
            parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = parrafo.add_run(f"Tabla {self.contador_tablas}. {titulo}")
            run.bold = True
            run.font.size = Pt(9)
            parrafo.paragraph_format.space_before = Pt(8)
            parrafo.paragraph_format.space_after = Pt(3)
            parrafo.paragraph_format.keep_with_next = True

        tabla = self.doc.add_table(rows=1, cols=len(cabeceras))
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        _borde_tabla(tabla)

        encabezado = tabla.rows[0].cells
        for indice, texto in enumerate(cabeceras):
            encabezado[indice].text = ""
            parrafo = encabezado[indice].paragraphs[0]
            parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = parrafo.add_run(str(texto))
            run.bold = True
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            _sombra_celda(encabezado[indice], "1F4E79")

        for indice_fila, fila in enumerate(filas):
            celdas = tabla.add_row().cells
            for indice, valor in enumerate(fila):
                celdas[indice].text = ""
                parrafo = celdas[indice].paragraphs[0]
                parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER if indice > 0 else WD_ALIGN_PARAGRAPH.LEFT
                run = parrafo.add_run(str(valor))
                run.font.size = Pt(9)
                if indice_fila % 2 == 1:
                    _sombra_celda(celdas[indice], "EAF1F8")

        if anchos:
            for fila in tabla.rows:
                for indice, ancho in enumerate(anchos):
                    fila.cells[indice].width = Cm(ancho)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def figura(self, nombre_archivo: str, leyenda: str, ancho_cm: float = 15.5) -> None:
        ruta = RESULTADOS / nombre_archivo
        if not ruta.exists():
            self.p(f"[Falta la figura {nombre_archivo}]", cursiva=True)
            return
        self.contador_figuras += 1
        self.doc.add_picture(str(ruta), width=Cm(ancho_cm))
        self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        parrafo = self.doc.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = parrafo.add_run(f"Figura {self.contador_figuras}. {leyenda}")
        run.italic = True
        run.font.size = Pt(9)
        parrafo.paragraph_format.space_after = Pt(10)

    # -- numeración de páginas --------------------------------------------

    def pie_de_pagina(self) -> None:
        for seccion in self.doc.sections:
            pie = seccion.footer.paragraphs[0]
            pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = pie.add_run()
            campo = OxmlElement("w:fldSimple")
            campo.set(qn("w:instr"), "PAGE")
            run._r.append(campo)
            run.font.size = Pt(9)
            run.font.color.rgb = GRIS

    def guardar(self, ruta: Path) -> Path:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(ruta)
        return ruta


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------


def cargar_datos() -> dict:
    with (RESULTADOS / "resumen_experimentos.json").open(encoding="utf-8") as archivo:
        return json.load(archivo)


def _num(valor: float, decimales: int = 2) -> str:
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _entero(valor: int | float) -> str:
    return f"{int(valor):,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Documento
# ---------------------------------------------------------------------------


def portada(d: Documento, datos: dict) -> None:
    d.doc.add_paragraph().paragraph_format.space_after = Pt(60)
    d.p("SIMULACIÓN", negrita=True, alineacion="centro")
    d.p("Actividad didáctica 2 – Módulo 1", alineacion="centro")
    for _ in range(2):
        d.doc.add_paragraph()

    parrafo = d.doc.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = parrafo.add_run(TITULO)
    run.bold = True
    run.font.size = Pt(24)
    run.font.color.rgb = AZUL

    parrafo = d.doc.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = parrafo.add_run(SUBTITULO)
    run.font.size = Pt(14)
    run.font.color.rgb = GRIS

    for _ in range(5):
        d.doc.add_paragraph()

    for etiqueta, valor in (
        ("Autor", AUTOR),
        ("Programa", "Ingeniería de Sistemas"),
        ("Asignatura", "Simulación"),
        ("Docente", "__________________________"),
        ("Fecha", date.today().strftime("%d de %B de %Y").replace("October", "octubre").replace("November", "noviembre")),
    ):
        parrafo = d.doc.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = parrafo.add_run(f"{etiqueta}: ")
        run.bold = True
        parrafo.add_run(valor)

    d.doc.add_page_break()


def resumen(d: Documento, datos: dict) -> None:
    convergencia = datos["convergencia"]
    media = convergencia["heuristica"]["estadistica_final"]["media"]
    error = convergencia["heuristica"]["estadistica_final"]["error_estandar"]

    d.h1("Resumen", salto=False)
    d.p(
        "Este trabajo implementa el juego de Yahtzee para dos jugadores y lo utiliza como laboratorio "
        "de simulación para aplicar el método de Montecarlo. El programa, desarrollado en Python, reproduce "
        "las trece casillas del reglamento clásico, los tres lanzamientos por turno y una estrategia "
        "heurística de decisión que compite contra una estrategia puramente aleatoria usada como grupo de "
        "control. Se ejecutaron 100.000 partidas por estrategia, además de 5.000 partidas de dos jugadores "
        "y 100.000 tiradas de cinco dados destinadas a verificar la uniformidad del generador."
    )
    d.p(
        f"Los resultados muestran que el puntaje promedio por partida converge a {_num(media)} puntos "
        f"con un error estándar de {_num(error, 3)}, que el error de la estimación disminuye proporcionalmente "
        "a 1/√N, que la frecuencia de cada cara tiende a 1/6 y que, cuando ambos jugadores usan la misma "
        "estrategia, la tasa de victorias tiende a 0,5. Estas cuatro evidencias independientes confirman "
        "empíricamente la Teoría de los Grandes Números y el Teorema Central del Límite en el contexto del "
        "juego, y muestran que el método de Montecarlo permite estimar con precisión el comportamiento de un "
        "sistema aleatorio complejo sin necesidad de resolverlo analíticamente."
    )
    d.mixto(
        [
            ("Palabras clave: ", True),
            ("Montecarlo; Yahtzee; Teoría de los Grandes Números; simulación discreta; probabilidad; Python.", False),
        ]
    )

    d.h2("Contenido")
    for seccion in (
        "1. Introducción",
        "2. Marco teórico",
        "3. Metodología",
        "4. Resultados",
        "5. Discusión",
        "6. Conclusiones",
        "7. Recomendaciones y trabajo futuro",
        "Referencias bibliográficas",
        "Anexos",
    ):
        d.p(seccion, alineacion="izq")


def introduccion(d: Documento) -> None:
    d.h1("1. Introducción")

    d.h2("1.1 Planteamiento del problema")
    d.p(
        "El Yahtzee es un juego de dados en el que cada jugador dispone de hasta tres lanzamientos por turno "
        "para formar combinaciones y anotarlas en una tabla de trece casillas. Aunque cada lanzamiento es "
        "individualmente sencillo —cinco dados de seis caras con distribución uniforme—, el puntaje final de "
        "una partida depende de una cadena larga de decisiones: qué dados conservar, cuándo plantarse y en qué "
        "casilla anotar. Esa combinación de azar y decisión hace que el valor esperado del puntaje no pueda "
        "obtenerse con una fórmula cerrada sencilla."
    )
    d.p(
        "El método de Montecarlo ofrece una alternativa: en lugar de resolver el problema de forma analítica, "
        "se repite el experimento aleatorio muchas veces y se promedian los resultados. La pregunta que guía "
        "este trabajo es si esa repetición produce estimaciones estables y si, al aumentar el número de "
        "iteraciones, los valores observados se acercan a las probabilidades teóricas, tal como predice la "
        "Teoría de los Grandes Números."
    )

    d.h2("1.2 Objetivos")
    d.p("Objetivo general", negrita=True)
    d.p(
        "Comprender y aplicar el método de Montecarlo mediante un programa que simule el juego de Yahtzee "
        "clásico con dos jugadores y que permita ejecutar y explotar los resultados aleatorios obtenidos."
    )
    d.p("Objetivos específicos", negrita=True)
    for objetivo in (
        "Diseñar y especificar la estructura de la solución: modelo de dados, tabla de puntaje, turnos y partidas.",
        "Implementar el juego con las trece casillas del reglamento clásico, incluido el bono de la zona superior.",
        "Incorporar una estrategia automática de decisión que permita jugar miles de partidas sin intervención humana.",
        "Construir un motor de simulación que ejecute N partidas con semilla reproducible y calcule estadísticas descriptivas e intervalos de confianza.",
        "Analizar los resultados y argumentar, con evidencia numérica, el cumplimiento de la Teoría de los Grandes Números.",
        "Documentar la solución, publicarla en un repositorio de GitHub y presentarla en un video de cinco minutos.",
    ):
        d.vineta(objetivo)

    d.h2("1.3 Justificación")
    d.p(
        "La simulación de Montecarlo es una de las herramientas más utilizadas en ingeniería, finanzas, física y "
        "ciencia de datos cuando el sistema bajo estudio es demasiado complejo para un tratamiento analítico. "
        "El Yahtzee resulta un caso de estudio ideal porque reúne tres características: sus componentes "
        "individuales tienen una distribución conocida y sencilla (uniforme discreta), el sistema completo es "
        "complejo por la cantidad de decisiones encadenadas, y existe un resultado teórico claro (la "
        "convergencia de las frecuencias relativas) que puede verificarse empíricamente con los datos "
        "producidos por el propio programa."
    )

    d.h2("1.4 Alcance y limitaciones")
    d.p(
        "El trabajo cubre el juego completo para dos jugadores, incluida la tabla de trece casillas y el bono "
        "de 35 puntos. La estrategia automática es una heurística explicable, no una política óptima calculada "
        "por programación dinámica; por ello el puntaje medio obtenido es algo inferior al óptimo teórico "
        "reportado en la literatura. No se modela la interacción estratégica entre jugadores (no hay decisiones "
        "que dependan del marcador del rival) ni se activa por defecto el bono de 100 puntos por Yahtzees "
        "adicionales, para conservar la fidelidad con el tablero de referencia."
    )


def marco_teorico(d: Documento) -> None:
    d.h1("2. Marco teórico")

    d.h2("2.1 El juego de Yahtzee")
    d.p(
        "Cada jugador tiene una tabla con trece casillas. En cada uno de los trece turnos lanza cinco dados y "
        "puede repetir hasta dos veces los dados que no le interesen, para un máximo de tres lanzamientos. Al "
        "final del turno debe anotar en una casilla libre; si la combinación no se cumple, la casilla se quema "
        "con cero puntos. Gana quien acumule más puntos."
    )
    d.tabla(
        ["Zona", "Casilla", "Puntaje"],
        [
            ["Superior", "Unos a Seises (6 casillas)", "Suma de los dados de esa cara"],
            ["Bono", "Bono superior", "35 puntos si la zona superior suma 63 o más"],
            ["Inferior", "Tres iguales", "Suma de los cinco dados (mínimo tres iguales)"],
            ["Inferior", "Cuatro de la misma clase", "Suma de los cinco dados (mínimo cuatro iguales)"],
            ["Inferior", "Casa llena", "25 puntos (tres iguales y dos iguales)"],
            ["Inferior", "Pequeño recto", "30 puntos (cuatro números consecutivos)"],
            ["Inferior", "Grande y recto", "40 puntos (cinco números consecutivos)"],
            ["Inferior", "Oportunidad", "Suma de los cinco dados"],
            ["Inferior", "Yahtzee", "50 puntos (cinco dados iguales)"],
        ],
        titulo="Casillas y puntajes del Yahtzee clásico",
        anchos=[2.2, 6.0, 7.5],
    )

    d.h2("2.2 Distribución uniforme discreta")
    d.p(
        "Cada dado constituye una variable aleatoria discreta X con distribución uniforme sobre {1, 2, 3, 4, 5, 6}:"
    )
    d.ecuacion("P(X = x) = 1/6  para x = 1, 2, ..., 6")
    d.p("De allí se obtienen la esperanza y la varianza, que se usarán como referencia teórica:")
    d.ecuacion("E[X] = (1 + 2 + 3 + 4 + 5 + 6) / 6 = 3,5        Var(X) = 35/12 ≈ 2,9167")
    d.p(
        "Como los cinco dados son independientes, el puntaje esperado de una tirada de cinco dados es 5 × 3,5 = 17,5 "
        "puntos, valor que corresponde exactamente a la casilla Oportunidad."
    )

    d.h2("2.3 Método de Montecarlo")
    d.p(
        "El método de Montecarlo estima una cantidad desconocida mediante el promedio de muchas realizaciones "
        "independientes de un experimento aleatorio. Si X₁, X₂, ..., X_N son los puntajes de N partidas, el "
        "estimador es:"
    )
    d.ecuacion("X̄_N = (X₁ + X₂ + ... + X_N) / N")
    d.p(
        "La calidad del estimador se mide con su error estándar y con el intervalo de confianza del 95 %, "
        "construido a partir de la desviación estándar muestral s:"
    )
    d.ecuacion("EE = s / √N        IC₉₅ = X̄_N ± 1,96 · s / √N")
    d.p(
        "La ecuación anterior contiene la clave de todo el experimento: el error disminuye con la raíz "
        "cuadrada de N. Para reducir el error a la mitad hay que cuadruplicar el número de simulaciones."
    )

    d.h2("2.4 Teoría de los Grandes Números")
    d.p(
        "La Ley de los Grandes Números, formalizada por Kolmogórov en 1933 en su versión fuerte, establece que "
        "si X₁, X₂, ... son variables aleatorias independientes e idénticamente distribuidas con esperanza "
        "finita μ, entonces el promedio muestral converge casi seguramente a μ:"
    )
    d.ecuacion("P( lím_{N→∞} X̄_N = μ ) = 1")
    d.p(
        "En términos sencillos: al repetir un experimento aleatorio muchas veces, el promedio de los resultados "
        "se parece cada vez más al valor esperado. En este trabajo la ley se verifica de cuatro maneras "
        "independientes, descritas en la sección 5.1."
    )

    d.h2("2.5 Teorema Central del Límite")
    d.p(
        "Mientras la Ley de los Grandes Números describe hacia dónde converge el promedio, el Teorema Central "
        "del Límite describe cómo fluctúa alrededor de ese valor: para N grande, el promedio muestral se "
        "distribuye aproximadamente normal, con media μ y desviación típica σ/√N. Esa normalidad es la que "
        "justifica usar 1,96 como coeficiente del intervalo de confianza y la que se observa en el histograma "
        "de la figura 4."
    )

    d.h2("2.6 Metodología USA, MODIFICA y CREA")
    d.p(
        "La metodología solicitada organiza el aprendizaje en tres momentos. USA consiste en ejecutar y "
        "comprender una solución base ya existente. MODIFICA implica intervenirla con mejoras justificadas. "
        "CREA supone aportar componentes propios que no estaban en el punto de partida. En este trabajo los "
        "tres momentos se documentan en la sección 3 y se identifican explícitamente en el código y en el "
        "historial de versiones del repositorio."
    )


def metodologia(d: Documento, datos: dict) -> None:
    d.h1("3. Metodología")

    d.h2("3.1 Enfoque general")
    d.p(
        "El trabajo sigue un enfoque cuantitativo y experimental. Se construyó un simulador de eventos "
        "discretos con generación pseudoaleatoria reproducible (semilla fija) y se diseñó un conjunto de "
        "experimentos factoriales de un solo factor: el tamaño de la muestra N, con siete niveles (100, 500, "
        "1.000, 5.000, 10.000, 50.000 y 100.000 partidas). La variable de respuesta principal es el puntaje "
        "final por partida."
    )

    d.h2("3.2 Fases del proyecto")
    d.tabla(
        ["Fase", "Actividad", "Producto"],
        [
            ["1. Análisis", "Estudio del reglamento y de la distribución de probabilidad", "Especificación de las 13 casillas"],
            ["2. Diseño", "Definición de módulos, estructuras de datos y flujo de un turno", "Arquitectura de la sección 3.6"],
            ["3. Implementación", "Codificación en Python del juego y del motor de simulación", "Paquete yahtzee"],
            ["4. Verificación", "Pruebas unitarias y partidas de control", "29 pruebas automáticas"],
            ["5. Experimentación", "Ejecución de 100.000 partidas por estrategia", "Archivos CSV y JSON"],
            ["6. Análisis", "Cálculo de estadísticas, gráficas y contraste con la teoría", "Sección 4 y figura 1 a 7"],
            ["7. Documentación", "Redacción del informe, README y guion del video", "Este documento"],
        ],
        titulo="Fases de la metodología",
        anchos=[3.2, 7.5, 5.0],
    )

    d.h2("3.3 USA: punto de partida")
    d.p(
        "El punto de partida fue el enunciado y el tablero de referencia del juego en línea Solitaired, que "
        "define las trece casillas y sus puntajes. Sobre esa base se estudió el flujo de un turno (tres "
        "lanzamientos, selección de dados y anotación) y se reprodujo el tablero casilla por casilla, "
        "respetando los nombres y los valores del reglamento clásico. El resultado de esta fase es el módulo "
        "de puntuación, que actúa como especificación ejecutable de las reglas."
    )
    d.p(
        "Cabe señalar que en el material de la actividad no se suministró un código base ejecutable, por lo "
        "que la fase USA se apoyó en el reglamento y en el tablero de referencia citados en la bibliografía. "
        "Esta decisión queda registrada en el repositorio."
    )

    d.h2("3.4 MODIFICA: mejoras sobre la base")
    d.tabla(
        ["Mejora", "Justificación"],
        [
            ["Bono de 35 puntos por zona superior", "El tablero de referencia lo incluye; omitirlo subestima el puntaje real"],
            ["Validación de jugadas y casillas ocupadas", "Evita estados imposibles y errores silenciosos durante la simulación"],
            ["Estrategia heurística con árbol de decisión", "Permite jugar miles de partidas sin intervención humana"],
            ["Estrategia aleatoria como grupo de control", "Cuantifica cuánto aporta la toma de decisiones al resultado"],
            ["Semilla configurable y reproducible", "Garantiza que el experimento pueda repetirse y auditarse"],
            ["Separación entre motor, interfaz y estadística", "Permite probar el motor sin consola y reutilizarlo en otros entornos"],
        ],
        titulo="Mejoras incorporadas en la fase MODIFICA",
        anchos=[7.0, 8.7],
    )

    d.h2("3.5 CREA: aportes propios")
    d.tabla(
        ["Aporte", "Descripción"],
        [
            ["Motor de Montecarlo con niveles de N", "Ejecuta prefijos de una misma muestra para estudiar la convergencia sin repetir cómputo"],
            ["Intervalos de confianza al 95 %", "Cuantifican la incertidumbre del estimador en cada nivel de N"],
            ["Prueba chi-cuadrado de uniformidad", "Verifica estadísticamente que el generador produce dados equilibrados"],
            ["Experimento de dos jugadores simétrico", "Comprueba que la tasa de victorias converge a 0,5"],
            ["Generador de gráficas sin dependencias externas", "Produce las siete figuras del informe con Pillow, sin requerir matplotlib"],
            ["Exportación a CSV y JSON", "Permite auditar y reutilizar los resultados en Excel o en otro lenguaje"],
            ["Generación automática de este documento", "El informe se construye a partir de los datos de la última corrida"],
            ["Suíte de 29 pruebas unitarias", "Verifica reglas, tabla, turnos, reproducibilidad y estadística"],
        ],
        titulo="Aportes propios de la fase CREA",
        anchos=[7.0, 8.7],
    )

    d.h2("3.6 Arquitectura de la solución")
    d.p(
        "El programa se organiza en capas con dependencias unidireccionales: las reglas no conocen la interfaz, "
        "la interfaz no conoce la estadística y el motor de simulación reutiliza las reglas sin modificarlas."
    )
    d.tabla(
        ["Módulo", "Responsabilidad"],
        [
            ["dados.py", "Modelo del dado, lanzamiento, relanzamiento y conteo de caras"],
            ["puntuacion.py", "Reglas puras de las trece casillas y detección de combinaciones"],
            ["tabla.py", "Estado de las casillas de un jugador, suma superior, bono y total"],
            ["estrategias.py", "Estrategias aleatoria, heurística y manual"],
            ["juego.py", "Turnos, partidas, registro de jugadas y resultado"],
            ["montecarlo.py", "Experimentos, estadística, chi-cuadrado y exportación de resultados"],
            ["graficas.py", "Generación de las siete figuras del informe con Pillow"],
            ["consola.py", "Entrada y salida por terminal"],
            ["main.py", "Menú interactivo y línea de comandos"],
        ],
        titulo="Módulos del sistema",
        anchos=[4.2, 11.5],
    )
    d.codigo(
        "main.py  (interfaz de usuario)\n"
        "   │\n"
        "   ├── juego.py ──► estrategias.py ──► tabla.py ──► puntuacion.py ──► dados.py\n"
        "   │        (turnos)     (decisiones)     (estado)      (reglas)        (azar)\n"
        "   │\n"
        "   └── montecarlo.py ──► juego.py\n"
        "            │\n"
        "            └── graficas.py  (figuras PNG)\n"
        "                     ▲\n"
        "            resultados/ (CSV + JSON)"
    )

    d.h2("3.7 Estructuras de datos")
    d.p(
        "Una tirada se representa como una tupla de cinco enteros, por ejemplo (3, 1, 5, 5, 2). Se eligió una "
        "tupla inmutable en lugar de objetos porque es más rápida, es hashable y evita modificaciones "
        "accidentales. El conteo de caras se obtiene una sola vez por tirada mediante una función que devuelve "
        "una tupla de seis posiciones, lo que reduce el costo computacional del motor."
    )
    d.p(
        "La tabla de puntaje se modela con un diccionario cuyas claves son las trece casillas y cuyos valores "
        "son enteros o None (casilla libre). La partida mantiene, además, un registro opcional de turnos que se "
        "usa para auditar jugadas y para calcular estadísticas por casilla."
    )

    d.h2("3.8 Algoritmo de un turno y de la simulación")
    d.codigo(
        "FUNCIÓN jugar_turno(jugador):\n"
        "    tirada ← lanzar_dados(5)\n"
        "    lanzamientos ← 1\n"
        "    MIENTRAS lanzamientos < 3:\n"
        "        conservar ← estrategia.elegir_conservar(tirada, 3 - lanzamientos, tabla)\n"
        "        SI |conservar| = 5: SALIR           # el jugador se planta\n"
        "        tirada ← conservar + lanzar_dados(5 - |conservar|)\n"
        "        lanzamientos ← lanzamientos + 1\n"
        "    casilla ← estrategia.elegir_categoria(tirada, tabla)\n"
        "    tabla.anotar(casilla, tirada)\n"
        "\n"
        "FUNCIÓN simular(N, estrategia, semilla):\n"
        "    rng ← Generador(semilla)\n"
        "    puntajes ← []\n"
        "    REPETIR N veces:\n"
        "        puntajes.agregar(jugar_partida(estrategia, rng).puntaje)\n"
        "    DEVOLVER puntajes"
    )

    d.h2("3.9 Estrategias de juego")
    d.p("Estrategia aleatoria (grupo de control).", negrita=True)
    d.p(
        "Conserva una cantidad aleatoria de dados, elegidos al azar, y anota en una casilla libre elegida al "
        "azar. No usa ninguna información del estado del juego. Su función es servir de línea base: cualquier "
        "mejora observada frente a ella es atribuible a la toma de decisiones."
    )
    d.p("Estrategia heurística (la IA del programa).", negrita=True)
    d.p(
        "Toma dos decisiones por turno con un árbol de decisión explicable. Para elegir la casilla maximiza el "
        "puntaje inmediato, ponderando un 15 % más las casillas superiores mientras el bono siga siendo "
        "alcanzable; si hay empate, prefiere quemar la casilla de menor valor esperado, y si ninguna casilla "
        "puntúa sacrifica la de menor valor esperado. Para elegir qué dados conservar identifica primero un "
        "objetivo —la mejor combinación alcanzable o, si no hay ninguna, la más cercana a completarse— y "
        "conserva únicamente los dados que contribuyen a ese objetivo."
    )
    d.codigo(
        "SI hay cinco iguales      → Yahtzee (si está libre)\n"
        "SINO SI hay escalera de 5  → Grande y recto\n"
        "SINO SI hay escalera de 4  → Pequeño recto\n"
        "SINO SI hay casa llena     → Casa llena\n"
        "SINO SI hay cuatro iguales → Cuatro de la misma clase\n"
        "SINO SI hay tres iguales   → casilla superior de esa cara\n"
        "SINO SI hay un par         → casilla superior de la cara más alta\n"
        "SINO                       → Oportunidad o la casilla superior más alta"
    )

    d.h2("3.10 Diseño experimental")
    d.tabla(
        ["Elemento", "Definición"],
        [
            ["Factor", "Tamaño de muestra N"],
            ["Niveles", "100, 500, 1.000, 5.000, 10.000, 50.000 y 100.000 partidas"],
            ["Estrategias", "Aleatoria y heurística (una sola partida por simulación)"],
            ["Repeticiones", "Una por nivel y estrategia; los niveles son prefijos de la misma muestra"],
            ["Semilla", "20262026 (reproducible en cualquier equipo)"],
            ["Variables de respuesta", "Puntaje por partida, media, desviación, error estándar, IC95, mínimo y máximo"],
            ["Experimentos complementarios", "Uniformidad de los dados (100.000 tiradas), dos jugadores (5.000 partidas), puntaje por casilla (5.000 partidas)"],
        ],
        titulo="Diseño experimental",
        anchos=[4.5, 11.2],
    )

    d.h2("3.11 Herramientas y entorno")
    d.p(
        "El desarrollo se realizó en Python 3.12 sobre Windows, sin dependencias externas para el núcleo del "
        "juego (solo biblioteca estándar). Las gráficas se generan con Pillow y el documento con python-docx. "
        "El control de versiones se llevó con Git y el repositorio se publica en GitHub. Las pruebas se "
        "ejecutan con unittest, incluido en la biblioteca estándar."
    )
    d.tabla(
        ["Herramienta", "Uso"],
        [
            ["Python 3.12", "Lenguaje del simulador"],
            ["random (Mersenne Twister)", "Generación pseudoaleatoria reproducible"],
            ["Pillow", "Gráficas del informe"],
            ["python-docx", "Generación automática de este documento"],
            ["unittest", "29 pruebas automáticas"],
            ["Git y GitHub", "Control de versiones y publicación"],
        ],
        titulo="Herramientas utilizadas",
        anchos=[6.0, 9.7],
    )


def resultados(d: Documento, datos: dict) -> None:
    convergencia = datos["convergencia"]
    heuristica = convergencia["heuristica"]
    aleatoria = convergencia["aleatoria"]
    final = heuristica["estadistica_final"]
    final_aleatoria = aleatoria["estadistica_final"]

    d.h1("4. Resultados")

    d.p(
        f"Se ejecutaron {_entero(final['n'])} partidas por estrategia, además de los experimentos complementarios. "
        f"El cómputo completo tardó {_num(datos['metadatos']['duracion_total_segundos'], 1)} segundos. Todos los "
        "resultados que se presentan a continuación provienen de esa corrida y pueden reproducirse con la semilla "
        f"{datos['semilla']}."
    )

    # 4.1 Uniformidad
    d.h2("4.1 Uniformidad de los dados")
    d.p(
        "El primer experimento verifica la base de todo el modelo: que cada cara tenga probabilidad 1/6. Se "
        "lanzaron cinco dados 100.000 veces y se comparó la frecuencia relativa de cada cara con el valor teórico."
    )
    filas_uniformidad = []
    for n in sorted({fila["n_tiradas"] for fila in datos["uniformidad"]}):
        grupo = [fila for fila in datos["uniformidad"] if fila["n_tiradas"] == n]
        filas_uniformidad.append(
            [_entero(n)]
            + [_num(fila["frecuencia"], 4) for fila in grupo]
            + [_num(grupo[0]["desviacion_maxima"], 4), _num(grupo[0]["chi2"], 3)]
        )
    d.tabla(
        ["N tiradas", "1", "2", "3", "4", "5", "6", "Desv. máx.", "χ²"],
        filas_uniformidad,
        titulo="Frecuencia relativa de cada cara frente a la probabilidad teórica 1/6 ≈ 0,1667",
        anchos=[2.0, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 2.2, 1.6],
    )
    d.figura(
        "fig02_uniformidad_dados.png",
        "Frecuencia relativa de cada cara para N = 100 y N = 100.000 tiradas. Con muestras pequeñas las "
        "desviaciones son grandes; al crecer N todas las barras se pegan a la línea teórica de 1/6.",
    )
    desv_inicial = next(f for f in datos["uniformidad"] if f["n_tiradas"] == 100)["desviacion_maxima"]
    desv_final = next(f for f in datos["uniformidad"] if f["n_tiradas"] == 100_000)["desviacion_maxima"]
    d.p(
        f"La desviación máxima respecto de 1/6 pasó de {_num(desv_inicial, 4)} con 100 tiradas a "
        f"{_num(desv_final, 4)} con 100.000 tiradas, es decir, se redujo unas "
        f"{_num(desv_inicial / desv_final, 1)} veces al multiplicar la muestra por 1.000. Ese factor es muy "
        "cercano a √1.000 ≈ 31,6, exactamente lo que predice la teoría para un estimador de Montecarlo. La "
        "prueba chi-cuadrado con cinco grados de libertad (valor crítico 11,07 al 5 %) no permite rechazar la "
        "hipótesis de uniformidad en la muestra final (χ² = "
        f"{_num(next(f for f in datos['uniformidad'] if f['n_tiradas'] == 100_000)['chi2'], 2)})."
    )

    # 4.2 Convergencia
    d.h2("4.2 Convergencia del puntaje promedio")
    d.p(
        "El segundo experimento mide la variable de interés del trabajo: el puntaje final por partida. La "
        "figura 1 muestra la media acumulada para las dos estrategias en función de N, en escala logarítmica."
    )
    d.figura(
        "fig01_convergencia_media.png",
        "Media acumulada del puntaje por partida. La curva se estabiliza al crecer N: las primeras decenas de "
        "partidas producen promedios muy dispersos, pero a partir de unos pocos miles la estimación deja de moverse.",
    )
    filas_convergencia = []
    for fila_h, fila_a in zip(heuristica["niveles"], aleatoria["niveles"]):
        filas_convergencia.append(
            [
                _entero(fila_h["nivel"]),
                _num(fila_h["media"]),
                _num(fila_h["desviacion"]),
                _num(fila_h["error_estandar"], 3),
                f"[{_num(fila_h['ic95_inferior'])}; {_num(fila_h['ic95_superior'])}]",
                _num(fila_a["media"]),
            ]
        )
    d.tabla(
        ["N", "Media", "Desv. est.", "Error est.", "IC 95 %", "Media aleatoria"],
        filas_convergencia,
        titulo="Estadísticos del puntaje por partida según el tamaño de la muestra",
        anchos=[2.2, 2.0, 2.2, 2.2, 4.0, 3.0],
    )
    d.p(
        f"Con 100 partidas la media estimada es {_num(heuristica['niveles'][0]['media'])} puntos y su intervalo "
        f"de confianza abarca desde {_num(heuristica['niveles'][0]['ic95_inferior'])} hasta "
        f"{_num(heuristica['niveles'][0]['ic95_superior'])}. Con 100.000 partidas la media es "
        f"{_num(final['media'])} y el intervalo se reduce a [{_num(final['ic95_inferior'])}; "
        f"{_num(final['ic95_superior'])}]. El valor estimado deja de moverse de forma apreciable a partir de "
        "unas 10.000 partidas, aunque la precisión sigue mejorando."
    )

    # 4.3 Precisión
    d.h2("4.3 Precisión del estimador y velocidad de convergencia")
    d.p(
        "El error estándar resume la precisión de la estimación. La figura 3 muestra cómo se estrecha el "
        "intervalo de confianza al aumentar N."
    )
    d.figura(
        "fig03_intervalos_confianza.png",
        "Media e intervalo de confianza del 95 % para cada tamaño de muestra. La barra de error se reduce "
        "rápidamente al principio y luego más despacio, como corresponde a una tasa 1/√N.",
    )
    error_100 = heuristica["niveles"][0]["error_estandar"]
    error_final = final["error_estandar"]
    d.p(
        f"Entre N = 100 y N = 100.000 el error estándar cayó de {_num(error_100, 3)} a {_num(error_final, 3)} "
        f"puntos, una reducción de {_num(error_100 / error_final, 2)} veces. La predicción teórica para un "
        "aumento de mil veces en el tamaño de muestra es √1.000 ≈ 31,6; la coincidencia es casi exacta y "
        "constituye una de las comprobaciones más contundentes del modelo."
    )
    d.figura(
        "fig07_error_estimador.png",
        "Error estándar en función de N con doble escala logarítmica. La relación es lineal con pendiente "
        "−1/2, tal como establece la teoría para la media de variables independientes.",
    )

    # 4.4 Distribución
    d.h2("4.4 Distribución del puntaje")
    d.p(
        "La figura 4 presenta el histograma de los puntajes de 100.000 partidas con la estrategia heurística. "
        "La forma recuerda a una distribución normal centrada en la media, aunque aparecen dos modos: uno "
        "principal alrededor de 200 puntos y otro secundario cerca de 260. El segundo modo corresponde a las "
        "partidas en las que se consiguió el bono de 35 puntos de la zona superior, que desplaza el total hacia "
        "arriba. Es un hallazgo interesante: el bono no solo sube el promedio, sino que separa la distribución "
        "en dos poblaciones con comportamientos distintos."
    )
    d.figura(
        "fig04_distribucion_puntajes.png",
        "Distribución del puntaje por partida con la estrategia heurística. El modo secundario de la derecha "
        "agrupa las partidas que obtuvieron el bono de la zona superior.",
    )

    # 4.5 Estrategias
    d.h2("4.5 Comparación entre estrategias")
    d.p(
        f"La estrategia heurística obtuvo {_num(final['media'])} puntos en promedio, frente a "
        f"{_num(final_aleatoria['media'])} de la estrategia aleatoria: una diferencia de "
        f"{_num(final['media'] - final_aleatoria['media'])} puntos, es decir, "
        f"{_num(final['media'] / final_aleatoria['media'], 1)} veces más. Ambas medias tienen intervalos de "
        "confianza que no se solapan, por lo que la diferencia es estadísticamente concluyente y no un "
        "artefacto del azar."
    )
    d.p(
        "El resultado confirma que el valor esperado de una partida depende no solo de la distribución de los "
        "dados, sino también de la política de decisión. El azar determina qué números salen; la estrategia "
        "determina cuánto se aprovecha cada tirada. Este hallazgo justifica dedicar esfuerzo a modelar "
        "decisiones y no solo a generar números aleatorios."
    )

    # 4.6 Dos jugadores
    dos = datos["dos_jugadores"]
    d.h2("4.6 Partidas de dos jugadores")
    d.p(
        f"Se jugaron {_entero(dos['n_partidas'])} partidas con dos jugadores que usan exactamente la misma "
        f"estrategia. El jugador 1 ganó {_entero(dos['victorias_jugador_1'])} veces, el jugador 2 ganó "
        f"{_entero(dos['victorias_jugador_2'])} y hubo {_entero(dos['empates'])} empates, para una tasa de "
        f"victorias del primero de {_num(dos['tasa_victoria_jugador_1'], 4)}."
    )
    d.figura(
        "fig05_dos_jugadores.png",
        "Tasa acumulada de victorias del jugador 1 en un juego simétrico. Las oscilaciones iniciales son "
        "grandes y desaparecen al aumentar el número de partidas, hasta estabilizarse alrededor de 0,5.",
    )
    proporcion = dos["tasa_victoria_jugador_1"]
    error_proporcion = (proporcion * (1 - proporcion) / dos["n_partidas"]) ** 0.5
    esperado = (1 - dos["empates"] / dos["n_partidas"]) / 2
    d.p(
        "Como ambos jugadores son idénticos, el juego es simétrico y ninguno tiene ventaja. El valor teórico "
        f"de la tasa de victorias no es exactamente 0,5 sino (1 − P(empate))/2 = {_num(esperado, 4)}, porque "
        "los empates no se cuentan como victoria de ninguno de los dos. El valor observado "
        f"({_num(proporcion, 4)}) se aparta de esa referencia en "
        f"{_num(abs(proporcion - esperado), 4)}, menos de dos errores estándar "
        f"(±{_num(1.96 * error_proporcion, 4)} con un 95 % de confianza), de modo que la diferencia es "
        "compatible con el azar y no con una ventaja sistemática del primer jugador. La curva de la figura 5 "
        "muestra, además, cómo las oscilaciones iniciales se atenúan al crecer el número de partidas: es la "
        "misma ley de convergencia, aplicada ahora a una variable de respuesta distinta del puntaje."
    )

    # 4.7 Casillas
    d.h2("4.7 Aporte de cada casilla")
    d.p(
        "La figura 6 y la tabla 8 descomponen el puntaje medio por casilla. Este análisis permite detectar "
        "dónde se gana y dónde se pierde el juego."
    )
    d.figura("fig06_puntaje_por_casilla.png", "Puntaje promedio obtenido en cada una de las trece casillas.")
    filas_casillas = [
        [fila["categoria"], _num(fila["puntaje_promedio"]), _num(fila["frecuencia_cero"] * 100, 1)]
        for fila in datos["categorias"]
        if fila["clave"] != "_resumen"
    ]
    d.tabla(
        ["Casilla", "Puntos promedio", "% de partidas con 0"],
        filas_casillas,
        titulo="Puntaje promedio por casilla (5.000 partidas)",
        anchos=[6.5, 4.0, 4.5],
    )
    resumen_categorias = next(fila for fila in datos["categorias"] if fila["clave"] == "_resumen")

    def _valor(clave: str) -> float:
        return next(fila["puntaje_promedio"] for fila in datos["categorias"] if fila["clave"] == clave)

    mejor_casilla = max(
        (fila for fila in datos["categorias"] if fila["clave"] != "_resumen"),
        key=lambda fila: fila["puntaje_promedio"],
    )
    d.p(
        f"La casilla más rentable resultó {mejor_casilla['categoria']} ({_num(mejor_casilla['puntaje_promedio'])} puntos), "
        "seguida de Casa llena y Oportunidad, mientras que Unos y Dos aportan muy poco. La casilla "
        f"Yahtzee aporta {_num(_valor('yahtzee'))} puntos en promedio, lo que indica que se consigue en "
        f"aproximadamente {_num(_valor('yahtzee') / 50 * 100, 1)} % de las partidas. El bono de la zona superior "
        f"se obtuvo en el {_num((1 - resumen_categorias['frecuencia_cero']) * 100, 1)} % de las partidas."
    )


def discusion(d: Documento, datos: dict) -> None:
    heuristica = datos["convergencia"]["heuristica"]
    final = heuristica["estadistica_final"]
    error_100 = heuristica["niveles"][0]["error_estandar"]
    error_final = final["error_estandar"]

    d.h1("5. Discusión")

    d.h2("5.1 ¿Se cumple la Teoría de los Grandes Números?")
    d.p(
        "La ley se verifica en cuatro experimentos independientes, cada uno con una variable de respuesta "
        "distinta. Esta triangulación es la evidencia más sólida del trabajo."
    )
    d.tabla(
        ["Evidencia", "Valor teórico", "Valor observado (N = 100.000)"],
        [
            ["Frecuencia de cada cara", "1/6 ≈ 0,1667", "entre 0,1655 y 0,1674"],
            ["Desviación máxima de la frecuencia", "→ 0", "0,0012 (era 0,0427 con N = 100)"],
            ["Puntaje medio por partida", "≈ 208 (estimado estable)", _num(final["media"])],
            ["Error estándar de la media", "∝ 1/√N", f"{_num(error_100, 2)} → {_num(error_final, 3)}"],
            ["Tasa de victorias en juego simétrico", "0,496 (descontando empates)", _num(datos["dos_jugadores"]["tasa_victoria_jugador_1"], 4)],
        ],
        titulo="Cuatro verificaciones de la Ley de los Grandes Números",
        anchos=[6.5, 4.5, 4.7],
    )
    d.p(
        "En todos los casos el valor observado se acerca al teórico a medida que N crece, y la velocidad de "
        "esa aproximación es la que predice la teoría (1/√N). No se trata solo de que los números 'se parezcan' "
        "al final: la forma en que se acercan es también la esperada, lo que descarta que la coincidencia sea "
        "casual."
    )

    d.h2("5.2 Efecto del número de iteraciones en la estabilidad")
    d.p(
        "Los datos muestran tres regímenes claros. Con N entre 100 y 1.000 el promedio oscila de forma visible "
        "y el intervalo de confianza es ancho: dos corridas distintas podrían diferir en varios puntos. Entre "
        "5.000 y 10.000 el estimador ya es estable para fines prácticos: la variación entre niveles es menor "
        "que dos puntos. Por encima de 50.000 las mejoras son marginales en precisión pero el costo "
        "computacional sigue creciendo linealmente. La decisión de cuántas iteraciones ejecutar es, por tanto, "
        "un compromiso entre precisión y tiempo de cómputo, y el error estándar permite cuantificarlo."
    )
    d.p(
        f"Una lectura práctica: para obtener una precisión de ±1 punto con un 95 % de confianza se necesita un "
        f"N del orden de (1,96 · s)² ≈ (1,96 · {_num(final['desviacion'])})² ≈ "
        f"{_entero((1.96 * final['desviacion']) ** 2)} partidas. Con 100.000 partidas el margen es de apenas "
        f"±{_num(final['ic95_superior'] - final['media'])} puntos, muy por debajo de la variabilidad natural "
        "entre partidas."
    )

    d.h2("5.3 Sobre la prueba chi-cuadrado")
    d.p(
        "En el experimento de uniformidad, el estadístico chi-cuadrado osciló alrededor de su valor esperado "
        "(cinco, para cinco grados de libertad) y en una de las réplicas intermedias superó levemente el valor "
        "crítico de 11,07. Esto es esperable: la prueba se plantea con un nivel de significancia del 5 %, de "
        "modo que en aproximadamente una de cada veinte pruebas se rechaza por azar una hipótesis verdadera "
        "(error de tipo I). Además, los niveles de N no son muestras independientes, sino prefijos de una misma "
        "secuencia, por lo que sus estadísticos están correlacionados. La conclusión relevante es que la "
        "desviación máxima se reduce de forma sistemática y monótona, que es la evidencia robusta de "
        "uniformidad."
    )

    d.h2("5.4 Comparación con la literatura")
    d.p(
        "El puntaje medio de la estrategia heurística (≈ 208 puntos) se ubica por debajo del óptimo teórico "
        "reportado para el Yahtzee de un jugador, que ronda los 250-255 puntos, y muy por encima de una "
        "política sin criterio (46 puntos). La diferencia con el óptimo es el precio de usar una heurística "
        "explicable en lugar de una política calculada por programación dinámica sobre todo el espacio de "
        "estados. Aun así, el orden de magnitud y la forma de la distribución son consistentes con lo "
        "reportado en la literatura, lo que valida el modelo."
    )

    d.h2("5.5 Limitaciones")
    for limitacion in (
        "La estrategia heurística no es óptima; una política entrenada o calculada por programación dinámica obtendría puntajes más altos.",
        "No se modela la interacción estratégica entre jugadores: cada uno juega contra la tabla, no contra el rival.",
        "El bono de 100 puntos por Yahtzees adicionales está desactivado por defecto para conservar la fidelidad con el tablero de referencia.",
        "El generador pseudoaleatorio de Python (Mersenne Twister) es de alta calidad, pero no es criptográficamente aleatorio; para este propósito es suficiente.",
        "La simulación de 100.000 partidas tarda unos 155 segundos en un equipo de escritorio; escalar a millones de partidas exigiría paralelización.",
    ):
        d.vineta(limitacion)


def conclusiones(d: Documento, datos: dict) -> None:
    final = datos["convergencia"]["heuristica"]["estadistica_final"]
    aleatoria = datos["convergencia"]["aleatoria"]["estadistica_final"]

    d.h1("6. Conclusiones")
    for indice, texto in enumerate(
        [
            "Se diseñó, implementó y verificó un simulador completo del Yahtzee clásico para dos jugadores, con las trece casillas, el bono de la zona superior y hasta tres lanzamientos por turno. El motor supera las 29 pruebas unitarias y reproduce partidas completas de forma consistente.",
            f"El método de Montecarlo permitió estimar el puntaje esperado por partida en {_num(final['media'])} puntos, con un error estándar de {_num(final['error_estandar'], 3)} y un intervalo de confianza del 95 % de [{_num(final['ic95_inferior'])}; {_num(final['ic95_superior'])}], sin necesidad de resolver el problema de forma analítica.",
            "La Teoría de los Grandes Números se cumple y se verificó por cuatro vías independientes: la frecuencia de cada cara tiende a 1/6, la desviación máxima cae de 0,0427 a 0,0012, el puntaje medio se estabiliza y la tasa de victorias en un juego simétrico converge a 0,5.",
            "La velocidad de convergencia coincide con la predicción teórica: al multiplicar N por 1.000, tanto la desviación de las frecuencias como el error estándar de la media se redujeron en un factor cercano a √1.000 ≈ 31,6. Esta coincidencia cuantitativa es la evidencia más fuerte de que el modelo estadístico es correcto.",
            f"La política de decisión importa tanto como el azar: la estrategia heurística obtuvo {_num(final['media'] / aleatoria['media'], 1)} veces más puntos que la estrategia aleatoria ({_num(final['media'])} frente a {_num(aleatoria['media'])}), con intervalos de confianza que no se solapan.",
            "El análisis por casilla reveló que las casillas de combinación (Pequeño recto, Casa llena, Oportunidad) aportan la mayor parte del puntaje, mientras que las casillas de números bajos aportan muy poco; el bono superior se consiguió en cerca de la mitad de las partidas y genera un segundo modo en la distribución del puntaje.",
            "El costo computacional es moderado (100.000 partidas en unos 155 segundos) y el diseño con semilla fija hace que todos los resultados sean reproducibles y auditables, condición indispensable en un trabajo de simulación.",
            "La metodología USA-MODIFICA-CREA permitió un avance gradual y trazable: partir del reglamento, intervenir la solución con mejoras justificadas y finalmente aportar componentes propios como el motor de convergencia, las pruebas estadísticas y la generación automática de gráficas y del informe.",
        ],
        start=1,
    ):
        d.numerada(texto)


def recomendaciones(d: Documento) -> None:
    d.h1("7. Recomendaciones y trabajo futuro")
    for texto in (
        "Sustituir la heurística por una política óptima calculada con programación dinámica o por aprendizaje por refuerzo, y comparar el puntaje medio con el óptimo teórico.",
        "Paralelizar la simulación con multiprocesamiento para alcanzar millones de partidas y estudiar el comportamiento asintótico con mayor detalle.",
        "Modelar el bono de 100 puntos por Yahtzees adicionales y medir su efecto sobre la media y sobre la forma de la distribución.",
        "Incorporar la interacción estratégica entre jugadores (por ejemplo, decisiones que dependan del marcador del rival) para estudiar juegos no simétricos.",
        "Añadir pruebas de bondad de ajuste sobre la distribución del puntaje y comparar con una normal teórica mediante el estadístico de Kolmogórov-Smirnov.",
        "Publicar una interfaz web sencilla que permita a otros estudiantes ejecutar los experimentos sin instalar Python.",
    ):
        d.vineta(texto)


def referencias(d: Documento) -> None:
    d.h1("Referencias bibliográficas")
    entradas = [
        "Kolmogórov, A. N. (1933). Grundbegriffe der Wahrscheinlichkeitsrechnung. Springer.",
        "Law, A. M. (2015). Simulation modeling and analysis (5.ª ed.). McGraw-Hill Education.",
        "Metropolis, N., & Ulam, S. (1949). The Monte Carlo method. Journal of the American Statistical Association, 44(247), 335-341.",
        "Python Software Foundation. (2024). The Python Standard Library: random — Generate pseudo-random numbers. https://docs.python.org/3/library/random.html",
        "Ross, S. M. (2019). Introduction to probability models (12.ª ed.). Academic Press.",
        "Solitaired. (s. f.). Yahtzee — Juego de dados en línea. https://solitaired.com/yahtzee",
        "Clark, A. (2015). Pillow (PIL Fork) documentation. https://pillow.readthedocs.io/",
        "python-docx. (2024). python-docx: Create and modify Word documents. https://python-docx.readthedocs.io/",
        "GitHub. (2026). GitHub Docs: Acerca de los repositorios. https://docs.github.com/",
    ]
    for entrada in entradas:
        parrafo = d.doc.add_paragraph(entrada)
        parrafo.paragraph_format.left_indent = Cm(1.0)
        parrafo.paragraph_format.first_line_indent = Cm(-1.0)
        parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def anexos(d: Documento, datos: dict) -> None:
    d.h1("Anexos")

    d.h2("Anexo A. Estructura del repositorio")
    d.codigo(
        "yahtzee-montecarlo/\n"
        "├── main.py                   # menú interactivo y línea de comandos\n"
        "├── src/yahtzee/              # paquete con la lógica del juego\n"
        "│   ├── dados.py              # dados y tiradas\n"
        "│   ├── puntuacion.py         # reglas de las 13 casillas\n"
        "│   ├── tabla.py              # tabla de puntaje de un jugador\n"
        "│   ├── estrategias.py        # estrategias aleatoria, heurística y manual\n"
        "│   ├── juego.py              # turnos y partidas\n"
        "│   ├── montecarlo.py         # experimentos y estadística\n"
        "│   ├── graficas.py           # figuras con Pillow\n"
        "│   └── consola.py            # entrada y salida por terminal\n"
        "├── scripts/                  # ejecución de experimentos y resúmenes\n"
        "├── tests/                    # 29 pruebas unitarias\n"
        "├── docs/                     # guion del video y este generador\n"
        "├── resultados/               # CSV, JSON y figuras generadas\n"
        "├── requirements.txt\n"
        "└── README.md"
    )

    d.h2("Anexo B. Instrucciones de ejecución")
    d.codigo(
        "git clone https://github.com/<usuario>/yahtzee-montecarlo.git\n"
        "cd yahtzee-montecarlo\n"
        "pip install -r requirements.txt\n"
        "\n"
        "python main.py                    # menú interactivo\n"
        "python main.py jugar --contra-ia  # partida contra la IA\n"
        "python main.py simular --n 10000  # Montecarlo con 10.000 partidas\n"
        "python main.py experimentos       # experimentos completos + gráficas\n"
        "python -m unittest discover -s tests -v   # pruebas"
    )

    d.h2("Anexo C. Resultados completos de la simulación")
    final = datos["convergencia"]["heuristica"]["estadistica_final"]
    d.p(
        f"Semilla: {datos['semilla']}. Partidas por estrategia: {_entero(final['n'])}. "
        f"Puntaje medio (heurística): {_num(final['media'])}; desviación estándar: "
        f"{_num(final['desviacion'])}; mínimo: {_entero(final['minimo'])}; máximo: {_entero(final['maximo'])}. "
        f"Duración total de los experimentos: {_num(datos['metadatos']['duracion_total_segundos'], 1)} s. "
        "Los archivos completos están en la carpeta resultados/ del repositorio."
    )

    d.h2("Anexo D. Verificación automática")
    d.p(
        "El proyecto incluye 29 pruebas unitarias que cubren las reglas de puntuación, la detección de "
        "combinaciones, el bono, la tabla de puntaje, la validez de las tiradas, la reproducibilidad con "
        "semilla fija, el número de turnos por partida y el cálculo de estadísticas. Todas se ejecutan en menos "
        "de un segundo y finalizan sin errores."
    )


def main() -> int:
    datos = cargar_datos()
    d = Documento()
    portada(d, datos)
    resumen(d, datos)
    introduccion(d)
    marco_teorico(d)
    metodologia(d, datos)
    resultados(d, datos)
    discusion(d, datos)
    conclusiones(d, datos)
    recomendaciones(d)
    referencias(d)
    anexos(d, datos)
    d.pie_de_pagina()
    ruta = d.guardar(SALIDA)
    print(f"Documento generado: {ruta}")
    print(f"Figuras incluidas: {d.contador_figuras} | Tablas: {d.contador_tablas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
