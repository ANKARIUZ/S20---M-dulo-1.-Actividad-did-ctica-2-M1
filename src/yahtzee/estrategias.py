"""Estrategias de juego.

Una estrategia responde a dos preguntas en cada turno:

1. **¿Qué dados conservo?** (``elegir_conservar``)
2. **¿En qué casilla anoto la tirada final?** (``elegir_categoria``)

Se incluyen tres implementaciones:

* ``EstrategiaAleatoria``: línea base.  Conserva dados al azar y elige una
  casilla al azar.  Sirve para comparar y para evidenciar el efecto de la
  estrategia en los resultados (parte del análisis del documento).
* ``EstrategiaHeuristica``: la "IA" del programa.  Usa un árbol de decisión
  explicable: primero busca la combinación de mayor puntaje, y si no hay
  ninguna, persigue la que está más cerca de completarse.
* ``EstrategiaManual``: delega las decisiones en el jugador humano a través de
  la consola.

Todas comparten la misma interfaz, de modo que el motor del juego y el motor
de Montecarlo funcionan igual con cualquiera de ellas.
"""

from __future__ import annotations

import random
from typing import Sequence

from .dados import contar_caras
from .puntuacion import (
    CATEGORIAS_SUPERIORES,
    NOMBRES,
    es_casa_llena,
    es_grande_recto,
    es_pequeno_recto,
    es_yahtzee,
    puntuar,
)
from .tabla import TablaPuntaje

#: Peso extra que se da a las casillas superiores mientras el bono de 35 siga
#: siendo alcanzable.  Refleja que un punto "superior" vale más que uno
#: "inferior" porque acerca al bono.
PESO_BONO_SUPERIOR = 1.15


class Estrategia:
    """Interfaz común de todas las estrategias."""

    nombre = "base"
    descripcion = ""

    def elegir_conservar(
        self,
        tirada: Sequence[int],
        lanzamientos_restantes: int,
        tabla: TablaPuntaje,
    ) -> list[int]:
        """Devuelve los dados (por valor) que se conservan para el próximo tiro."""
        raise NotImplementedError

    def elegir_categoria(self, tirada: Sequence[int], tabla: TablaPuntaje) -> str:
        """Devuelve la casilla donde se anota la tirada final."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Estrategia aleatoria (línea base)
# ---------------------------------------------------------------------------

class EstrategiaAleatoria(Estrategia):
    """Conserva dados al azar y anota en una casilla libre al azar.

    No es una estrategia "tonta" para el trabajo: es el **grupo de control**
    del experimento.  Comparar sus resultados con los de la estrategia
    heurística permite medir cuánto aporta la toma de decisiones.
    """

    nombre = "Aleatoria"
    descripcion = "Conserva dados al azar y elige casilla al azar (grupo de control)."

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def elegir_conservar(
        self,
        tirada: Sequence[int],
        lanzamientos_restantes: int,
        tabla: TablaPuntaje,
    ) -> list[int]:
        cantidad = self._rng.randint(0, len(tirada))
        return self._rng.sample(list(tirada), cantidad)

    def elegir_categoria(self, tirada: Sequence[int], tabla: TablaPuntaje) -> str:
        return self._rng.choice(tabla.categorias_libres())


# ---------------------------------------------------------------------------
# Estrategia heurística (la "IA")
# ---------------------------------------------------------------------------

class EstrategiaHeuristica(Estrategia):
    """Estrategia explicable basada en un árbol de decisión.

    Para **elegir la casilla** se busca la que maximiza el puntaje inmediato,
    con dos ajustes:

    * las casillas superiores se ponderan un 15 % más mientras el bono siga
      vivo (un punto arriba vale más porque acerca al bono de 35);
    * si hay empate, se prefiere quemar la casilla de menor valor esperado
      (por ejemplo, *Cuatro de la misma clase* antes que *Oportunidad*);
    * si ninguna casilla puntúa, se sacrifica la de menor valor esperado.

    Para **conservar dados** primero se decide un "objetivo" (la combinación
    que se está persiguiendo) y luego se guardan únicamente los dados que
    sirven para ese objetivo.
    """

    nombre = "Heurística"
    descripcion = "Árbol de decisión: busca la mejor combinación y persigue la más cercana."

    #: Valor esperado aproximado de cada casilla si se juega con buena técnica.
    #: Se usa solo para decidir qué casilla "duele menos" quemar con cero.
    VALOR_ESPERADO: dict[str, float] = {
        "unos": 2.0,
        "doses": 4.0,
        "treses": 6.0,
        "cuatros": 8.0,
        "cincos": 10.0,
        "seises": 12.0,
        "tres_iguales": 20.0,
        "cuatro_iguales": 12.0,
        "casa_llena": 18.0,
        "pequeno_recto": 20.0,
        "grande_recto": 15.0,
        "oportunidad": 23.0,
        "yahtzee": 5.0,
    }

    def __init__(self) -> None:
        pass

    # -- Decisión 1: dónde anotar -----------------------------------------

    def _valor_ajustado(self, categoria: str, tirada: Sequence[int], tabla: TablaPuntaje) -> float:
        """Puntaje de la casilla con el ajuste por el bono de la zona superior."""
        puntos = puntuar(categoria, tirada)
        if (
            categoria in CATEGORIAS_SUPERIORES
            and tabla.bono_alcanzable()
            and puntos > 0
        ):
            return puntos * PESO_BONO_SUPERIOR
        return float(puntos)

    def elegir_categoria(self, tirada: Sequence[int], tabla: TablaPuntaje) -> str:
        libres = tabla.categorias_libres()
        valores = {categoria: self._valor_ajustado(categoria, tirada, tabla) for categoria in libres}
        maximo = max(valores.values())

        if maximo > 0:
            candidatas = [categoria for categoria in libres if valores[categoria] == maximo]
            # Desempate: quemar la casilla menos valiosa (menor valor esperado).
            return min(candidatas, key=lambda categoria: self.VALOR_ESPERADO[categoria])

        # Ninguna casilla puntúa: hay que "sacrificar" la menos valiosa.
        return min(libres, key=lambda categoria: self.VALOR_ESPERADO[categoria])

    # -- Decisión 2: qué dados conservar -----------------------------------

    def _objetivo(self, tirada: Sequence[int], tabla: TablaPuntaje) -> str:
        """Combinación que la estrategia va a perseguir en este turno."""
        libres = tabla.categorias_libres()

        # (a) ¿Hay algo que ya puntúe? Entonces ese es el objetivo.
        valores = {categoria: self._valor_ajustado(categoria, tirada, tabla) for categoria in libres}
        mejor = max(valores, key=lambda categoria: valores[categoria])
        if valores[mejor] > 0:
            return mejor

        # (b) Nada puntúa: perseguir la combinación más cercana.
        return self._objetivo_por_cercania(tirada, libres)

    def _objetivo_por_cercania(self, tirada: Sequence[int], libres: Sequence[str]) -> str:
        conteo = contar_caras(tirada)
        maximo_repetido = max(conteo)
        pares = sum(1 for cantidad in conteo if cantidad >= 2)

        def superiores_libres(orden_caras: list[int]) -> list[str]:
            return [
                CATEGORIAS_SUPERIORES[cara - 1]
                for cara in orden_caras
                if CATEGORIAS_SUPERIORES[cara - 1] in libres
            ]

        # Cuatro o cinco iguales.
        if maximo_repetido >= 4:
            if "cuatro_iguales" in libres:
                return "cuatro_iguales"
            if "yahtzee" in libres:
                return "yahtzee"

        # Tres iguales: se intenta la casa llena o la casilla del número repetido.
        if maximo_repetido >= 3:
            if pares >= 2 and "casa_llena" in libres:
                return "casa_llena"
            cara_repetida = conteo.index(maximo_repetido) + 1
            opciones = superiores_libres([cara_repetida])
            if opciones:
                return opciones[0]
            if "tres_iguales" in libres:
                return "tres_iguales"
            if "cuatro_iguales" in libres:
                return "cuatro_iguales"

        # Dos pares: casa llena.
        if pares >= 2 and "casa_llena" in libres:
            return "casa_llena"

        # Escaleras.
        if es_grande_recto(tirada) and "grande_recto" in libres:
            return "grande_recto"
        if es_pequeno_recto(tirada) and "pequeno_recto" in libres:
            return "pequeno_recto"

        # Todos distintos: buscar el inicio de una escalera.
        ventana = _mejor_ventana_escalera(tirada)
        if len(ventana) >= 3 and "pequeno_recto" in libres:
            return "pequeno_recto"

        # Mano dispersa: con muchas casillas libres todavía conviene apostar a
        # un número alto; al final del juego, guardar los dados altos para
        # Oportunidad rinde más.
        if len(libres) <= 6 and "oportunidad" in libres:
            return "oportunidad"

        # Casilla del dado más alto disponible.
        orden = sorted((cara for cara in range(1, 7) if conteo[cara - 1] > 0), reverse=True)
        opciones = superiores_libres(orden)
        if opciones:
            return opciones[0]

        # Último recurso: Oportunidad.
        return "oportunidad" if "oportunidad" in libres else libres[0]

    def elegir_conservar(
        self,
        tirada: Sequence[int],
        lanzamientos_restantes: int,
        tabla: TablaPuntaje,
    ) -> list[int]:
        if lanzamientos_restantes <= 0:
            return list(tirada)

        objetivo = self._objetivo(tirada, tabla)

        # Si el objetivo ya está cumplido y es de puntos fijos, conviene plantarse.
        if puntuar(objetivo, tirada) > 0 and objetivo not in CATEGORIAS_SUPERIORES:
            if objetivo in ("yahtzee", "grande_recto", "pequeno_recto", "casa_llena"):
                return list(tirada)

        return _dados_para_objetivo(tirada, objetivo)


# ---------------------------------------------------------------------------
# Estrategia manual (jugador humano)
# ---------------------------------------------------------------------------

class EstrategiaManual(Estrategia):
    """Pide las decisiones al jugador por consola."""

    nombre = "Manual"
    descripcion = "El jugador humano decide qué conservar y dónde anotar."

    def elegir_conservar(
        self,
        tirada: Sequence[int],
        lanzamientos_restantes: int,
        tabla: TablaPuntaje,
    ) -> list[int]:
        from .consola import mostrar_tirada, pedir_conservar

        mostrar_tirada(tirada, lanzamientos_restantes)
        return pedir_conservar(tirada)

    def elegir_categoria(self, tirada: Sequence[int], tabla: TablaPuntaje) -> str:
        from .consola import mostrar_categorias_disponibles, pedir_categoria

        opciones = mostrar_categorias_disponibles(tabla, tirada)
        return pedir_categoria(opciones)


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _dados_para_objetivo(tirada: Sequence[int], objetivo: str) -> list[int]:
    """Elige qué dados sirven para el objetivo indicado."""
    conteo = contar_caras(tirada)

    if objetivo in CATEGORIAS_SUPERIORES:
        cara = CATEGORIAS_SUPERIORES.index(objetivo) + 1
        return [valor for valor in tirada if valor == cara]

    if objetivo in ("tres_iguales", "cuatro_iguales", "yahtzee"):
        # Conservar el grupo más numeroso; en caso de empate, el de mayor valor.
        cantidad = max(conteo)
        cara = max(cara for cara in range(1, 7) if conteo[cara - 1] == cantidad)
        return [valor for valor in tirada if valor == cara]

    if objetivo == "casa_llena":
        # Conservar los dos valores más repetidos (tres de uno y dos del otro).
        caras = sorted(range(1, 7), key=lambda cara: (conteo[cara - 1], cara), reverse=True)
        primera, segunda = caras[0], caras[1]
        conservar = [primera] * min(conteo[primera - 1], 3)
        conservar += [segunda] * min(conteo[segunda - 1], 2)
        return conservar

    if objetivo in ("pequeno_recto", "grande_recto"):
        ventana = _mejor_ventana_escalera(tirada)
        # Un dado por cada valor de la ventana (los repetidos no ayudan).
        conservar: list[int] = []
        for valor in ventana:
            if valor in tirada:
                conservar.append(valor)
        return conservar

    if objetivo == "oportunidad":
        return [valor for valor in tirada if valor >= 4]

    return list(tirada)


def _mejor_ventana_escalera(tirada: Sequence[int]) -> list[int]:
    """Ventana de cuatro valores consecutivos con más dados presentes.

    Devuelve, por ejemplo, ``[3, 4, 5, 6]`` si esa es la ventana que más se
    acerca a un recto.  En caso de empate se prefiere la de valores más altos.
    """
    caras = set(tirada)
    mejor: list[int] = []
    mejor_puntaje = -1
    for inicio in (1, 2, 3):
        ventana = [inicio, inicio + 1, inicio + 2, inicio + 3]
        presentes = sum(1 for valor in ventana if valor in caras)
        puntaje = presentes * 10 + inicio
        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor = ventana
    return mejor


# ---------------------------------------------------------------------------
# Fábrica
# ---------------------------------------------------------------------------

ESTRATEGIAS: dict[str, type[Estrategia]] = {
    "aleatoria": EstrategiaAleatoria,
    "heuristica": EstrategiaHeuristica,
    "manual": EstrategiaManual,
}


def crear_estrategia(nombre: str, rng: random.Random | None = None) -> Estrategia:
    """Crea una estrategia por su nombre corto (``aleatoria``, ``heuristica``)."""
    clave = nombre.strip().lower()
    if clave not in ESTRATEGIAS:
        raise ValueError(f"Estrategia desconocida: {nombre!r}. Opciones: {', '.join(ESTRATEGIAS)}")
    clase = ESTRATEGIAS[clave]
    if clase is EstrategiaAleatoria:
        return clase(rng)
    return clase()
