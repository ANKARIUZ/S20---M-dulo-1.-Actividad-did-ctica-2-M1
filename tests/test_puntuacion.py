"""Pruebas de las reglas de puntuación.

Se ejecutan con::

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from yahtzee.dados import contar_caras, lanzar_dados, relanzar  # noqa: E402
from yahtzee.puntuacion import (  # noqa: E402
    es_casa_llena,
    es_grande_recto,
    es_pequeno_recto,
    es_yahtzee,
    puntuar,
)
from yahtzee.tabla import TablaPuntaje  # noqa: E402


class PruebasDados(unittest.TestCase):
    def test_valores_en_rango(self):
        import random

        rng = random.Random(123)
        for _ in range(500):
            tirada = lanzar_dados(5, rng)
            self.assertEqual(len(tirada), 5)
            self.assertTrue(all(1 <= valor <= 6 for valor in tirada))

    def test_contar_caras(self):
        self.assertEqual(contar_caras((3, 3, 3, 5, 5)), (0, 0, 3, 0, 2, 0))
        self.assertEqual(contar_caras((1, 2, 3, 4, 5)), (1, 1, 1, 1, 1, 0))

    def test_relanzar_conserva_los_dados_elegidos(self):
        import random

        rng = random.Random(7)
        nueva = relanzar((1, 2, 3, 4, 5), [6, 6], rng)
        self.assertEqual(len(nueva), 5)
        self.assertEqual(nueva[:2], (6, 6))

    def test_relanzar_todo(self):
        import random

        rng = random.Random(7)
        self.assertEqual(len(relanzar((1, 2, 3, 4, 5), [], rng)), 5)


class PruebasCombinaciones(unittest.TestCase):
    def test_yahtzee(self):
        self.assertTrue(es_yahtzee((4, 4, 4, 4, 4)))
        self.assertFalse(es_yahtzee((4, 4, 4, 4, 5)))
        self.assertEqual(puntuar("yahtzee", (4, 4, 4, 4, 4)), 50)
        self.assertEqual(puntuar("yahtzee", (4, 4, 4, 4, 5)), 0)

    def test_casa_llena(self):
        self.assertTrue(es_casa_llena((2, 2, 2, 5, 5)))
        self.assertTrue(es_casa_llena((3, 3, 3, 3, 3)), "un Yahtzee también vale como casa llena")
        self.assertFalse(es_casa_llena((2, 2, 3, 4, 5)))
        self.assertEqual(puntuar("casa_llena", (2, 2, 2, 5, 5)), 25)

    def test_rectos(self):
        self.assertTrue(es_pequeno_recto((1, 2, 3, 4, 6)))
        self.assertTrue(es_pequeno_recto((2, 3, 4, 5, 5)))
        self.assertFalse(es_pequeno_recto((1, 2, 3, 5, 6)))
        self.assertTrue(es_grande_recto((2, 3, 4, 5, 6)))
        self.assertFalse(es_grande_recto((1, 2, 3, 4, 6)))
        self.assertEqual(puntuar("pequeno_recto", (1, 2, 3, 4, 6)), 30)
        self.assertEqual(puntuar("grande_recto", (2, 3, 4, 5, 6)), 40)
        # Una escalera grande también cumple el recto pequeño.
        self.assertEqual(puntuar("pequeno_recto", (2, 3, 4, 5, 6)), 30)


class PruebasPuntaje(unittest.TestCase):
    def test_casillas_superiores(self):
        tirada = (1, 1, 3, 4, 5)
        self.assertEqual(puntuar("unos", tirada), 2)
        self.assertEqual(puntuar("doses", tirada), 0)
        self.assertEqual(puntuar("treses", tirada), 3)
        self.assertEqual(puntuar("seises", tirada), 0)

    def test_inferiores_por_suma(self):
        tirada = (6, 6, 6, 2, 1)
        self.assertEqual(puntuar("tres_iguales", tirada), 21)
        self.assertEqual(puntuar("cuatro_iguales", tirada), 0)
        self.assertEqual(puntuar("oportunidad", tirada), 21)

    def test_cuatro_iguales(self):
        tirada = (5, 5, 5, 5, 2)
        self.assertEqual(puntuar("cuatro_iguales", tirada), 22)
        self.assertEqual(puntuar("tres_iguales", tirada), 22)

    def test_categoria_invalida(self):
        with self.assertRaises(ValueError):
            puntuar("casilla_inventada", (1, 2, 3, 4, 5))


class PruebasTabla(unittest.TestCase):
    def test_tabla_vacia(self):
        tabla = TablaPuntaje("Prueba")
        self.assertFalse(tabla.completa())
        self.assertEqual(tabla.total(), 0)
        self.assertEqual(len(tabla.categorias_libres()), 13)

    def test_bono_superior(self):
        tabla = TablaPuntaje("Prueba")
        # Cada tirada aporta un solo dado de la cara correspondiente.
        tabla.anotar("unos", (1, 1, 1, 1, 1))  # 5 puntos
        tabla.anotar("doses", (2, 1, 1, 1, 1))  # 2 puntos
        tabla.anotar("treses", (3, 1, 1, 1, 1))  # 3 puntos
        tabla.anotar("cuatros", (4, 1, 1, 1, 1))  # 4 puntos
        tabla.anotar("cincos", (5, 1, 1, 1, 1))  # 5 puntos
        self.assertEqual(tabla.suma_superior(), 19)
        self.assertEqual(tabla.bono(), 0)
        tabla.anotar("seises", (6, 1, 1, 1, 1))  # 6 puntos
        self.assertEqual(tabla.suma_superior(), 25)
        self.assertEqual(tabla.bono(), 0)

    def test_bono_alcanzado(self):
        tabla = TablaPuntaje("Prueba")
        for cara, categoria in enumerate(("unos", "doses", "treses", "cuatros", "cincos", "seises"), start=1):
            tabla.anotar(categoria, (cara, cara, cara, cara, cara))
        # 5 + 10 + 15 + 20 + 25 + 30 = 105 >= 63
        self.assertEqual(tabla.suma_superior(), 105)
        self.assertEqual(tabla.bono(), 35)
        self.assertEqual(tabla.total(), 105 + 35)

    def test_bono_alcanzable(self):
        tabla = TablaPuntaje("Prueba")
        self.assertTrue(tabla.bono_alcanzable())
        for categoria in ("unos", "doses", "treses", "cuatros", "cincos", "seises"):
            tabla.anotar(categoria, (1, 1, 1, 1, 1))
        self.assertFalse(tabla.bono_alcanzable(), "sin casillas superiores libres el bono ya no es alcanzable")

    def test_no_se_puede_repetir_casilla(self):
        tabla = TablaPuntaje("Prueba")
        tabla.anotar("unos", (1, 1, 1, 1, 1))
        with self.assertRaises(ValueError):
            tabla.anotar("unos", (1, 1, 1, 1, 1))

    def test_tabla_completa(self):
        tabla = TablaPuntaje("Prueba")
        for categoria in tabla.categorias_libres():
            tabla.anotar(categoria, (3, 3, 3, 3, 3))
        self.assertTrue(tabla.completa())
        self.assertEqual(len(tabla.categorias_libres()), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
