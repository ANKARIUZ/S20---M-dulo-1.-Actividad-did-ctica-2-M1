# 🎥 Guion del video — máximo 5 minutos

**Actividad didáctica 2-M1 · Simulación · Juan Camilo Ríos Hernández**

---

## Antes de grabar (checklist técnico)

- [ ] Cerrar notificaciones (Windows: *Asistente de concentración*).
- [ ] Aumentar el tamaño de la fuente de la terminal (`Ctrl + rueda del ratón` o propiedades → fuente 20).
- [ ] Tener abiertas: la terminal, el repositorio en GitHub y el documento Word.
- [ ] Probar el micrófono 10 segundos y escuchar.
- [ ] Grabar la pantalla completa a 1080p.
- [ ] Ensayar una vez con cronómetro.

## Preparación del entorno antes de grabar

```powershell
cd yahtzee-montecarlo
python main.py reglas
python main.py jugar --auto
```

Dejar además listos estos comandos para pegarlos sin escribir:

```powershell
python main.py simular --n 10000
python scripts/resumen_resultados.py
```

---

## Guion minuto a minuto

### 0:00 – 0:25 · Presentación

> "Hola, soy Juan Camilo Ríos Hernández. En este video presento la actividad de simulación del juego
> de Yahtzee con Montecarlo. El objetivo no era solo hacer el juego, sino usarlo como laboratorio
> para verificar la Teoría de los Grandes Números."

**En pantalla:** portada del documento o el título del repositorio.

---

### 0:25 – 1:10 · Qué es el juego y qué se construyó

> "El Yahtzee se juega con cinco dados y una tabla de trece casillas. En cada turno hay hasta tres
> lanzamientos y al final se anota en una casilla libre. La distribución de cada dado es uniforme:
> cada cara tiene probabilidad un sexto.
>
> Lo que construí es un programa en Python con tres partes: las reglas del juego, una estrategia
> automática que decide qué dados conservar, y un motor de Montecarlo que juega miles de partidas
> solo."

**En pantalla:** estructura de carpetas del repositorio, o el código de `puntuacion.py`.

---

### 1:10 – 1:55 · Metodología USA · MODIFICA · CREA ⭐ (punto obligatorio)

> "Trabajé con la metodología USA, MODIFICA y CREA.
>
> **USA:** partí del reglamento y del tablero de referencia, y reproduje las trece casillas tal cual.
>
> **MODIFICA:** agregué el bono de 35 puntos, la validación de jugadas, una estrategia heurística
> para jugar automáticamente y una estrategia aleatoria como grupo de control, para poder medir
> cuánto aporta decidir bien.
>
> **CREA:** mi aporte propio es el motor de Montecarlo con niveles de N, los intervalos de confianza,
> la prueba chi-cuadrado de uniformidad, las gráficas y la generación automática del informe a partir
> de los datos reales."

**En pantalla:** tabla USA/MODIFICA/CREA del documento o del README.

---

### 1:55 – 2:40 · Demostración del programa

```powershell
python main.py jugar --auto
```

> "Aquí se ve una partida completa entre dos IA. Cada línea es un turno: la tirada, la casilla
> elegida y los puntos. La estrategia conserva los dados que sirven a su objetivo y anota donde más
> le conviene."

Después, una simulación corta:

```powershell
python main.py simular --n 10000
```

> "Con diez mil partidas el programa devuelve el promedio, la desviación, el error estándar y el
> intervalo de confianza del noventa y cinco por ciento."

**En pantalla:** la terminal con la partida y el resumen estadístico.

---

### 2:40 – 4:15 · Resultados y Ley de los Grandes Números ⭐ (punto obligatorio)

> "Estos son los resultados con cien mil partidas por estrategia."

**En pantalla:** `resultados/fig01_convergencia_media.png`

> "La estrategia heurística promedia **208,56 puntos**; la aleatoria, apenas **45,88**. Es decir,
> decidir bien multiplica por cuatro y medio el resultado.
>
> Miren la curva: con cien partidas el promedio salta, y a partir de unos miles se queda quieto.
> Eso es exactamente la Ley de los Grandes Números: el promedio de muchos experimentos aleatorios
> converge al valor esperado."

**En pantalla:** `resultados/fig02_uniformidad_dados.png`

> "La segunda evidencia es la uniformidad de los dados. Con cien tiradas la frecuencia de cada cara
> se aleja hasta cuatro centésimas de un sexto; con cien mil tiradas la desviación máxima es de
> **0,0012**. Y la prueba chi-cuadrado queda por debajo del valor crítico: no hay evidencia de que
> el dado esté cargado."

**En pantalla:** `resultados/fig03_intervalos_confianza.png`

> "La tercera evidencia es la precisión. El error estándar pasó de **3,66** a **0,12** puntos al
> multiplicar la muestra por mil. La teoría dice que el error baja con la raíz de N: raíz de mil es
> treinta y uno coma seis, y la reducción observada fue de **treinta veces**. La coincidencia es casi
> exacta."

**En pantalla:** `resultados/fig04_distribucion_puntajes.png`

> "Y la cuarta: la distribución del puntaje tiene forma de campana, como predice el Teorema Central
> del Límite. Aparece un segundo pico cerca de 260 puntos: son las partidas en las que se ganó el
> bono de la zona superior."

---

### 4:15 – 4:45 · Conclusiones

> "En conclusión: el método de Montecarlo permitió estimar el comportamiento de un juego complejo sin
> resolverlo analíticamente, y las cuatro evidencias —uniformidad, convergencia, precisión y juego
> simétrico— confirman la Teoría de los Grandes Números. El código, los resultados y el documento
> están en el repositorio de GitHub."

**En pantalla:** repositorio de GitHub.

---

### 4:45 – 5:00 · Cierre

> "Gracias por su atención."

---

## Frases que NO se deben olvidar (rúbrica)

1. Explicar **USA, MODIFICA y CREA** con ejemplos concretos. ✅ (1:10)
2. Mostrar **las mejoras** incorporadas a la solución inicial. ✅ (1:10)
3. Justificar con **los resultados obtenidos** por qué se cumple la **Teoría de los Grandes
   Números**. ✅ (2:40)

## Consejos

- Hablar pausado: 5 minutos dan para unas 700 palabras.
- No leer el documento: señalarlo y explicarlo.
- Si algo falla en vivo, cortar y volver a grabar esa sección; luego unir con el editor.
- Subir a YouTube como **"no listado"** o a Drive con permiso de lectura para cualquier persona con
  el enlace.
- Verificar el enlace en una ventana de incógnito antes de entregar.
