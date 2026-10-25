"""Pruebas del motor del juego y de las estrategias.

Se ejecutan con::

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from yahtzee.estrategias import EstrategiaAleatoria, EstrategiaHeuristica, crear_estrategia  # noqa: E402
from yahtzee.juego import Jugador, Partida, jugar_partida  # noqa: E402
from yahtzee.montecarlo import Estadistica, simular_puntajes  # noqa: E402
from yahtzee.puntuacion import TODAS_LAS_CATEGORIAS  # noqa: E402
from yahtzee.tabla import TablaPuntaje  # noqa: E402


class PruebasEstrategias(unittest.TestCase):
    def test_estrategia_elige_casilla_libre(self):
        estrategia = EstrategiaHeuristica()
        tabla = TablaPuntaje("Prueba")
        tabla.anotar("unos", (1, 1, 2, 3, 4))
        eleccion = estrategia.elegir_categoria((6, 6, 6, 6, 6), tabla)
        self.assertIn(eleccion, tabla.categorias_libres())

    def test_estrategia_no_conserva_dados_inexistentes(self):
        estrategia = EstrategiaHeuristica()
        tabla = TablaPuntaje("Prueba")
        tirada = (2, 2, 5, 6, 1)
        conservar = estrategia.elegir_conservar(tirada, 2, tabla)
        self.assertLessEqual(len(conservar), 5)
        for valor in conservar:
            self.assertIn(valor, tirada)

    def test_estrategia_prefiere_yahtzee(self):
        estrategia = EstrategiaHeuristica()
        tabla = TablaPuntaje("Prueba")
        self.assertEqual(estrategia.elegir_categoria((5, 5, 5, 5, 5), tabla), "yahtzee")

    def test_estrategia_aleatoria_devuelve_casilla_valida(self):
        estrategia = EstrategiaAleatoria(random.Random(3))
        tabla = TablaPuntaje("Prueba")
        for _ in range(50):
            self.assertIn(estrategia.elegir_categoria((1, 2, 3, 4, 5), tabla), tabla.categorias_libres())

    def test_fabrica_de_estrategias(self):
        self.assertIsInstance(crear_estrategia("heuristica"), EstrategiaHeuristica)
        self.assertIsInstance(crear_estrategia("aleatoria"), EstrategiaAleatoria)
        with self.assertRaises(ValueError):
            crear_estrategia("inexistente")


class PruebasPartida(unittest.TestCase):
    def test_partida_completa_llena_las_trece_casillas(self):
        resultado = jugar_partida([EstrategiaHeuristica(), EstrategiaHeuristica()], random.Random(1))
        self.assertEqual(len(resultado.puntajes), 2)
        self.assertTrue(all(0 <= puntos <= 400 for puntos in resultado.puntajes))

    def test_numero_de_turnos(self):
        rng = random.Random(5)
        jugadores = [Jugador("A", EstrategiaHeuristica()), Jugador("B", EstrategiaHeuristica())]
        partida = Partida(jugadores, rng, registrar_turnos=True)
        partida.jugar()
        self.assertEqual(len(partida._turnos), 26)  # 13 rondas x 2 jugadores

    def test_reproducibilidad(self):
        primera = jugar_partida([EstrategiaHeuristica()], random.Random(42))
        segunda = jugar_partida([EstrategiaHeuristica()], random.Random(42))
        self.assertEqual(primera.puntajes, segunda.puntajes)

    def test_los_dados_siempre_son_validos(self):
        rng = random.Random(11)
        for _ in range(20):
            resultado = jugar_partida([EstrategiaHeuristica()], rng, registrar_turnos=True)
            for turno in resultado.turnos:
                self.assertEqual(len(turno.tirada), 5)
                self.assertTrue(all(1 <= valor <= 6 for valor in turno.tirada))
                self.assertIn(turno.categoria, TODAS_LAS_CATEGORIAS)
                self.assertLessEqual(turno.lanzamientos, 3)


class PruebasMontecarlo(unittest.TestCase):
    def test_estadistica_basica(self):
        estadistica = Estadistica.calcular([1, 2, 3, 4, 5])
        self.assertAlmostEqual(estadistica.media, 3.0)
        self.assertAlmostEqual(estadistica.desviacion, 1.5811, places=3)
        self.assertLess(estadistica.ic95_inferior, estadistica.media)
        self.assertGreater(estadistica.ic95_superior, estadistica.media)

    def test_simulacion_devuelve_n_puntajes(self):
        puntajes = simular_puntajes(50, "heuristica", semilla=3)
        self.assertEqual(len(puntajes), 50)
        self.assertTrue(all(puntos >= 0 for puntos in puntajes))

    def test_promedio_heuristica_supera_aleatoria(self):
        heuristico = sum(simular_puntajes(300, "heuristica", semilla=9)) / 300
        aleatorio = sum(simular_puntajes(300, "aleatoria", semilla=9)) / 300
        self.assertGreater(heuristico, aleatorio)


if __name__ == "__main__":
    unittest.main(verbosity=2)
