# ✅ Lista de verificación de la entrega

**Actividad didáctica 2-M1 · Simulación · Juan Camilo Ríos Hernández · 25 de octubre de 2026**

---

## 1. Entregables obligatorios

| # | Entregable | Estado | Dónde está |
|---|---|---|---|
| 1 | Código fuente | ✅ | `src/yahtzee/`, `main.py`, `scripts/` |
| 2 | Modificaciones y aportes sobre la guía | ✅ | README (USA/MODIFICA/CREA) y documento, sección 3 |
| 3 | Documentación para comprender la solución | ✅ | `README.md`, `docs/diseno_solucion.md` |
| 4 | Documento técnico (Word/PDF) | ✅ | `Rios_JuanCamilo_Montecarlo.docx` |
| 5 | Repositorio público en GitHub | ⬜ | **Pendiente de subir** (ver pasos 5) |
| 6 | Video de máximo 5 minutos | ⬜ | **Pendiente de grabar** (guion en `docs/guion_video.md`) |

---

## 2. Correspondencia con la rúbrica (100 puntos)

| Criterio | Puntos | Evidencia en el trabajo |
|---|---|---|
| **Estructura de la solución** | 20 | Documento §2.2 (distribución uniforme), §3.6–3.7 (arquitectura y estructuras de datos), §3.8 (algoritmo). Tabla de 13 casillas con su puntaje. |
| **Implementación de la solución** | 20 | 9 módulos documentados, 29 pruebas unitarias, README con instrucciones, documento §3.4–3.5 (MODIFICA y CREA con justificación). |
| **Análisis del caso planteado** | 20 | Documento §5.1 (cuatro verificaciones de la Ley), §5.2 (efecto de las iteraciones), §5.3 (chi-cuadrado), §5.4 (comparación con la literatura). |
| **Video de presentación** | 20 | Guion minuto a minuto en `docs/guion_video.md` con los tres puntos obligatorios marcados. |
| **Cargar en GitHub** | 10 | Estructura ordenada, `.gitignore`, `LICENSE`, README detallado. |
| **Puntualidad y entrega** | 10 | Entrega del 25 de octubre de 2026 con los nombres de archivo exigidos. |

---

## 3. Nomenclatura de archivos

| Requisito | Archivo |
|---|---|
| `Apellido_Nombre_Montecarlo.docx` | `Rios_JuanCamilo_Montecarlo.docx` |

> Si el docente exige el formato `Apellido_Nombre`, renombrar a `Rios_JuanCamilo_Montecarlo.docx`
> (ya es el nombre usado) o a `Rios_Juan_Montecarlo.docx`.

---

## 4. Verificación técnica antes de entregar

```bash
# 1. Las pruebas pasan
python -m unittest discover -s tests -v

# 2. El juego funciona
python main.py jugar --auto

# 3. La simulación funciona
python main.py simular --n 1000

# 4. Los resultados están completos
ls resultados/
```

- [ ] 29 pruebas sin errores.
- [ ] Se genera una partida completa de 13 turnos por jugador.
- [ ] Existen los 7 archivos PNG en `resultados/`.
- [ ] El documento abre en Word sin errores y tiene las 5 secciones mínimas.

---

## 5. Publicar en GitHub

```bash
cd yahtzee-montecarlo
git init
git add .
git commit -m "feat: simulador de Yahtzee con Montecarlo y análisis de la Ley de los Grandes Números"
git branch -M main
git remote add origin https://github.com/<usuario>/yahtzee-montecarlo.git
git push -u origin main
```

**Comprobar:** abrir el enlace en una ventana de incógnito. El repositorio debe ser **público** o
estar compartido con el docente.

---

## 6. Grabar y publicar el video

- [ ] Duración **menor o igual a 5 minutos**.
- [ ] Explica **USA, MODIFICA y CREA**.
- [ ] Muestra el programa funcionando.
- [ ] Presenta las mejoras realizadas.
- [ ] Justifica con **resultados propios** la Teoría de los Grandes Números.
- [ ] Audio claro y pantalla legible.
- [ ] Subido a YouTube (no listado), Drive u OneDrive con permiso de lectura.
- [ ] Enlace probado en incógnito.

---

## 7. Formulario de entrega

Registrar en la plataforma:

1. Enlace al repositorio de GitHub.
2. Enlace al video.
3. Documento técnico (`Rios_JuanCamilo_Montecarlo.docx`).

> El documento técnico **no se sube al repositorio como enlace**: se adjunta en el formulario y, si
> se desea, también se deja en el repositorio para consulta.

---

## 8. Puntos que el docente suele revisar

1. Que el programa **ejecute** sin errores en un equipo limpio.
2. Que el análisis **use los números reales** de la simulación (no cifras inventadas).
3. Que se explique **por qué** el error disminuye con N (1/√N), no solo que disminuye.
4. Que el repositorio tenga un **README** que permita ejecutar el proyecto en menos de cinco minutos.
5. Que el video **no exceda** los cinco minutos.
