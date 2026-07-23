# 🎮 Life RPG (MVP)

Gamifica tu vida: marcá hábitos buenos y malos, ganá **XP** y **monedas**,
perdé **vida**, subí de **nivel** y gastá monedas en la **tienda**. App
offline-first con navegación tipo celular (barra de pestañas abajo).

## Pestañas

- **🏠 Home** — tu nivel, barra de XP, monedas, vida y actividad reciente.
- **✅ Hábitos** — marcá buenos hábitos (+XP, +monedas) y malos (−vida).
- **🛒 Tienda** — gastá monedas; algunos items dan vida (una compra de vida por día).
- **📜 Historial** — registro de todas las acciones.
- **⚙️ Ajustes** — creá/editá hábitos e items, y reiniciá el progreso.

## Reglas del juego

- **Vida** empieza en 1000. Los malos hábitos la bajan.
- Si la vida llega a **0**, se abre un modal **obligatorio** de castigo
  (100 flexiones). Hay que confirmarlo para restaurar la vida a 1000.
- **Niveles**: tope 46. La XP requerida crece con una curva 1.2×
  (`xpToLevel(n) = round(100 · 1.2^(n-1))`, base 100).

## Datos

El estado se guarda de forma local en `life_rpg_data.json` (offline-first).
El archivo se ignora en git y es propio de cada dispositivo.

## Cómo correrlo

1. Instalá las dependencias

   ```
   $ pip install -r requirements.txt
   ```

2. Corré la app

   ```
   $ streamlit run streamlit_app.py
   ```

## Tests

La lógica del juego está en `game.py` (sin dependencia de Streamlit) y tiene
tests con pytest:

```
$ pip install pytest
$ pytest
```
