# Raceform

Strava te dice **qué hiciste**. Raceform responde **qué significa y qué deberías hacer ahora**.

No es otra app para registrar kilómetros. Toma tus actividades de Strava y, cada día,
responde tres preguntas: cómo estás, qué tenés que entrenar hoy, y para cuánto estás en
tu próxima carrera.

## Cómo ejecutarla

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Sin credenciales configuradas arranca con un **atleta de demostración**: 18 semanas de
entrenamiento coherente de un corredor que baja de 17:45 a 17:15 en 5K. Todas las
pantallas funcionan con esos datos.

### Conectar Strava (opcional)

Copiá `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y completá las
credenciales de tu aplicación de Strava:

```toml
STRAVA_CLIENT_ID = "…"
STRAVA_CLIENT_SECRET = "…"
STRAVA_REDIRECT_URI = "http://localhost:8501"
```

La app importa distancia, tiempo, ritmo, parciales, vueltas, frecuencia cardíaca,
desnivel y cadencia. Es **solo lectura**: nunca escribe en Strava.

### Entrenador de IA (opcional)

Con `ANTHROPIC_API_KEY` configurada, el chat conversa con Claude usando todo tu
historial como contexto. Sin la clave el entrenador sigue respondiendo, pero con reglas
sobre tus propios datos en lugar de conversación abierta — las respuestas siguen citando
tus ritmos y tus sesiones reales.

## Las cinco pantallas

| Pantalla | Qué responde |
|---|---|
| **Hoy** | Estado actual, entrenamiento recomendado y por qué. Una sola acción principal. |
| **Plan** | El calendario hasta la carrera, con el tema de cada semana. |
| **Progreso** | La única pantalla con gráficos de evolución, cada uno con su explicación. |
| **Carreras** | Predicción, preparación por capacidad y estrategia, para cada objetivo. |
| **Perfil** | Conexión, ritmos, hábitos y ajustes. |

El entrenador de IA es accesible desde cualquier pantalla, pero no es la pantalla
principal.

## Cómo funciona el análisis

Todo se deriva de las actividades; no hay nada que configurar a mano.

- **Clasificación** (`analysis/classify.py`) — separa las vueltas en trabajo y
  recuperación y decide cuál de las ocho familias es la sesión: rodaje, fondo, tempo,
  intervalos, repeticiones cortas, cuestas, competencia o test. La entrada en calor y la
  vuelta a la calma nunca se cuentan como recuperación.
- **Fisiología** (`analysis/physiology.py`) — modelo VDOT de Daniels & Gilbert. Da un
  único número al que se traduce cualquier rendimiento, de modo que una serie de 400 m,
  un tempo y una carrera de 5K se comparan en la misma escala. Los ritmos objetivo se
  derivan, no se estiman a ojo.
- **Desnivel** — Strava reporta ascenso total, no pendiente neta. En un circuito ese
  ascenso se devuelve como descenso, así que un recorrido ondulado se modela como mitad
  subida y mitad bajada (se cancela casi por completo) y solo una pendiente sostenida se
  ajusta de verdad.
- **Análisis de sesión** (`analysis/session.py`) — detecta la forma de la serie
  (consistente, cierre rápido, caída, progresivo, irregular), puntúa la ejecución y
  escribe qué pasó, con qué compararlo y qué cambiar. Cada frase está anclada a un número
  que calculó.
- **Predicción** (`analysis/predict.py`) — los corredores rara vez compiten, así que la
  estimación de estado de forma se extrae de *cada* tipo de sesión de calidad —
  competencias, tests, series y tempos — cada una con su propia confianza, y se mezcla
  con peso por recencia. Las cuestas quedan fuera: su ritmo no dice nada fiable sobre la
  forma en llano.
- **Capacidades** (`analysis/capability.py`) — la preparación se descompone en
  velocidad, resistencia específica, base aeróbica, capacidad de cierre y recuperación,
  medidas contra lo que pide *ese* objetivo. El limitante es el que más cuesta en la
  carrera, no simplemente el número más bajo.
- **Plan** (`analysis/plan.py`) — se reconstruye a partir del objetivo, la fase, el
  limitante y cómo venís respondiendo. Cuando algo cambia (enfermedad, sesión perdida,
  competencia inesperada, fatiga, molestia, exceso) **recalcula el resto de la semana**
  en lugar de mover sesiones de lugar, para no juntar estímulos incompatibles.
- **Hábitos** (`analysis/insights.py`) — no da puntos por registrar. Compara dos grupos
  reales de sesiones y solo muestra la relación si aparece de verdad en los datos.

## Pruebas

```bash
python -m pytest tests/ -q
```

175 pruebas sobre el motor de análisis: el modelo VDOT, la segmentación de vueltas, la
clasificación, la puntuación y narrativa de sesiones, la carga de entrenamiento, la
predicción, las capacidades, la generación y adaptación del plan, el mapeo de Strava y
la persistencia.

## Estructura

```
streamlit_app.py           punto de entrada y navegación
raceform/
  models.py                Activity, Lap, Goal, Feedback, HabitDay, PlannedSession
  engine.py                una sola pasada de cómputo que alimenta todas las pantallas
  demo.py                  atleta de demostración determinista
  strava.py                OAuth e importación
  store.py                 persistencia local en JSON
  coach.py                 contexto del entrenador + Claude, con fallback determinista
  analysis/                physiology · classify · session · load · predict ·
                           capability · plan · insights
  ui/                      theme · charts · components · screens/
tests/
```

## Estado

El MVP está completo: conectar Strava e importar, analizar cada entrenamiento, mostrar
preparación y predicción, y recomendar o ajustar la próxima sesión. La persistencia es
local (`~/.raceform/`), pensada para un solo atleta por instalación; una versión
multiusuario necesitaría una base de datos y autenticación propias.
