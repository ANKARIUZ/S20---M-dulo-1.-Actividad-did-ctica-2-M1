# Documento de diseño de la solución

**Actividad didáctica 2-M1 · Simulación · Juan Camilo Ríos Hernández**

Este documento resume las decisiones de diseño que sustentan la implementación. El informe técnico
completo (`Rios_JuanCamilo_Montecarlo.docx`) desarrolla los mismos puntos con mayor profundidad.

---

## 1. Especificación del problema

Construir un programa que:

1. Simule el Yahtzee clásico con **dos jugadores**, cinco dados de seis caras y hasta tres
   lanzamientos por turno.
2. Reproduzca la **tabla de trece casillas** del reglamento, incluido el bono de 35 puntos.
3. Permita **jugar interactivamente** y, sobre todo, **simular miles de partidas** sin intervención
   humana.
4. Genere resultados que permitan **comprobar la Teoría de los Grandes Números**.

El requisito 3 es el que distingue este trabajo de un simple juego: sin una estrategia automática no
hay forma de ejecutar 100.000 partidas.

---

## 2. Modelo matemático

| Concepto | Definición |
|---|---|
| Dado | Variable aleatoria discreta uniforme en {1, 2, 3, 4, 5, 6} |
| Distribución | P(X = x) = 1/6 para toda cara |
| Esperanza | E[X] = 3,5 |
| Varianza | Var(X) = 35/12 ≈ 2,9167 |
| Tirada | Vector de cinco dados independientes |
| Partida | 13 turnos por jugador |
| Estimador | Media muestral del puntaje de N partidas |
| Precisión | EE = s/√N; IC₉₅ = X̄ ± 1,96 · s/√N |

---

## 3. Arquitectura

Se adoptó una arquitectura en capas con dependencias unidireccionales:

```
 Interfaz (main.py, consola.py)
        │
        ▼
 Motor de juego (juego.py) ──► Estrategias (estrategias.py)
        │                              │
        ▼                              ▼
 Tabla de puntaje (tabla.py) ──► Reglas (puntuacion.py) ──► Dados (dados.py)
        │
        ▼
 Motor de Montecarlo (montecarlo.py) ──► Gráficas (graficas.py)
```

| Módulo | Responsabilidad | Depende de |
|---|---|---|
| `dados.py` | Lanzar, relanzar y contar caras | — |
| `puntuacion.py` | Puntuar cada casilla y detectar combinaciones | `dados` |
| `tabla.py` | Estado de las 13 casillas, bono y total | `puntuacion` |
| `estrategias.py` | Decidir qué conservar y dónde anotar | `tabla` |
| `juego.py` | Ejecutar turnos y partidas | `estrategias`, `dados` |
| `montecarlo.py` | Repetir partidas y calcular estadística | `juego` |
| `graficas.py` | Generar las figuras | `montecarlo` (datos) |
| `consola.py` | Entrada y salida por terminal | `tabla` |

**Por qué capas:** las reglas no saben que existe una pantalla, la pantalla no sabe que existe
estadística y el motor de simulación reutiliza el mismo código que el juego interactivo. Esto
garantiza que lo que se simula es exactamente el juego que se juega.

---

## 4. Estructuras de datos

| Elemento | Representación | Justificación |
|---|---|---|
| Dado | `int` de 1 a 6 | Simple y rápido |
| Tirada | `tuple[int, ...]` de longitud 5 | Inmutable, hashable, rápida |
| Conteo de caras | `tuple[int, ...]` de longitud 6 | Evita recalcular combinaciones |
| Tabla | `dict[str, int \| None]` | Acceso O(1) por casilla; `None` = libre |
| Registro de turno | `@dataclass(frozen=True)` | Trazabilidad y auditoría |
| Resultado | `@dataclass` | Transporte limpio entre capas |

---

## 5. Algoritmo

### 5.1 Turno

```
tirada ← lanzar_dados(5)
lanzamientos ← 1
MIENTRAS lanzamientos < 3:
    conservar ← estrategia.elegir_conservar(tirada, 3 - lanzamientos, tabla)
    SI |conservar| = 5: SALIR
    tirada ← conservar + lanzar_dados(5 - |conservar|)
    lanzamientos ← lanzamientos + 1
casilla ← estrategia.elegir_categoria(tirada, tabla)
tabla.anotar(casilla, tirada)
```

### 5.2 Simulación

```
rng ← Generador(semilla)
PARA i ← 1 HASTA N:
    puntajes[i] ← jugar_partida(estrategia, rng)
media ← promedio(puntajes)
IC95 ← media ± 1,96 · desviación(puntajes) / √N
```

Complejidad: O(N · 13 · 3) lanzamientos de dados; 100.000 partidas ≈ 160 s en un equipo de escritorio.

---

## 6. Estrategia heurística

### 6.1 Elección de la casilla

1. Calcular el puntaje de cada casilla libre.
2. Ponderar ×1,15 las casillas superiores mientras el bono siga siendo alcanzable.
3. Elegir el máximo; en caso de empate, quemar la casilla de menor valor esperado.
4. Si ninguna puntúa, sacrificar la de menor valor esperado.

### 6.2 Elección de los dados a conservar

1. Determinar el **objetivo**: la mejor combinación alcanzable; si no hay ninguna, la más cercana.
2. Conservar únicamente los dados que contribuyen a ese objetivo.
3. Plantarse si el objetivo ya se cumplió y es de puntos fijos (Yahtzee, rectos, casa llena).

**Valor esperado aproximado usado para el desempate:** Unos 2, Dos 4, Tres 6, Cuatro 8, Cinco 10,
Seises 12, Tres iguales 20, Cuatro iguales 12, Casa llena 18, Pequeño recto 20, Grande y recto 15,
Oportunidad 23, Yahtzee 5.

---

## 7. Diseño experimental

| Elemento | Valor |
|---|---|
| Factor | N (tamaño de muestra) |
| Niveles | 100, 500, 1.000, 5.000, 10.000, 50.000, 100.000 |
| Estrategias | aleatoria y heurística |
| Semilla | 20262026 |
| Respuesta | puntaje por partida |
| Estadísticos | media, desviación, error estándar, IC95, mínimo, máximo |

Se simula **una sola vez** el mayor N y se toman prefijos para los niveles menores: es válido porque
el estimador solo depende de los primeros valores y evita repetir el 90 % del cómputo.

---

## 8. Decisiones de diseño relevantes

| Decisión | Alternativa descartada | Motivo |
|---|---|---|
| Tuplas en vez de objetos `Dado` | Clase `Dado` con estado | Velocidad y ausencia de efectos colaterales |
| Estrategia heurística | Programación dinámica óptima | Explicable, rápida y suficiente para el objetivo |
| Estrategia aleatoria | Ninguna | Sin grupo de control no se puede medir el valor de decidir |
| Pillow para gráficas | matplotlib | Funciona sin acceso a PyPI en el equipo de desarrollo |
| JSON + CSV | Base de datos | Portabilidad y facilidad de auditoría |
| Semilla fija | Aleatoriedad total | Reproducibilidad exigida en trabajos de simulación |

---

## 9. Verificación

- **29 pruebas unitarias** (`python -m unittest discover -s tests`).
- Partidas de control con semilla fija para comprobar reproducibilidad.
- Comparación de las frecuencias observadas con 1/6 mediante chi-cuadrado.
- Comprobación de que el error estándar decrece como 1/√N.
