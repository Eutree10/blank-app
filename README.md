# ⚖️ Merchant's Odyssey

> «No eres un héroe. Eres el comerciante que mueve el mundo.»

Simulación de comercio en un mundo procedural que evoluciona sin ti. Empiezas con una
mochila y 100 monedas; terminas (si sabes leer el mercado) con flotas, fábricas y rutas
propias. Todo corre en el navegador, sin dependencias ni servidor.

**Jugar:** abre `game/index.html` — o el enlace githack del PR.

---

## Qué hay dentro

| Sistema | Detalle |
|---|---|
| **Mundo procedural** | Mapa de 224×144 con ruido fractal: continentes, biomas, costas y montañas. ~38 ciudades con población, riqueza, impuestos y especialidades coherentes con su terreno. |
| **Economía viva** | 27 bienes en 3 niveles (materia prima → elaborado → manufactura). El precio sale de stock frente a demanda, con elasticidad: si algo se pone carísimo, la gente compra menos y se produce más. Producción y consumo globales se normalizan al generar el mundo, así que el mundo no se muere solo. |
| **Sucesos** | 18 tipos: guerra, peste, hambruna, sequía, minas descubiertas o agotadas, ferias, auges industriales, revoluciones, aranceles, erupciones, modas… Cada uno mueve producción, demanda, impuestos, población y peligro de las rutas. |
| **Rutas** | Grafo terrestre y marítimo con Dijkstra. Las rutas se cortan por nieve o temporales y se infestan de bandidos y piratas. Sin barco, media parte del mundo es inalcanzable. |
| **Niebla de guerra** | El mapa empieza oculto. Se descubre viajando, con expediciones o comprando cartas náuticas. |
| **Memoria de precios** | Solo recuerdas lo que has visto: cada mercado guarda la fecha del dato. El panel *Mundo* calcula las mejores rutas con esa información imperfecta. |
| **Rivales con IA** | ~64 casas comerciales compran, venden, abren rutas, crecen y quiebran por su cuenta. Compiten contigo por el stock y aparecen en la tabla de patrimonios. |
| **Crecimiento** | Mulas, carretas, caravanas, diligencias y barcos; con el tiempo llegan el vapor, el tren y los aviones de carga. |
| **Fabricación** | 14 talleres (trigo → harina → pan, hierro → espadas, uva → vino…). Compran insumos y venden producción cada día a precio local: si saturas el mercado, tu propio taller deja de ser rentable. |
| **Otros oficios** | Contrabando de bienes prohibidos (+85% y riesgo de decomiso), banca y apalancamiento, almacenes para especular, contratos con plazo y emboscadas a caravanas rivales. |

## Controles

- **Mapa**: arrastrar para mover, rueda para zoom, clic en una ciudad para verla y viajar.
- **Mercado**: clic en un bien para desplegar compra/venta, histórico y dónde recuerdas mejores precios.
- **Teclado**: `espacio` esperar un día · `M` mercado · `C` ciudad · `I` imperio · `W` mundo.

La partida se guarda sola en `localStorage` (y con el botón *Guardar*). El mundo es
determinista: la misma semilla genera el mismo mapa.

## Estructura

```
game/
  index.html          portada + interfaz
  css/style.css       paleta cálida oscura, cifras en monoespaciada
  js/core.js          RNG determinista, bienes, recetas, vehículos, biomas
  js/world.js         generación del mundo, ciudades, grafo de rutas, niebla
  js/economy.js       precios, oferta/demanda, sucesos, contratos
  js/ai.js            comerciantes rivales
  js/game.js          estado del jugador, acciones, guardado
  js/render.js        render pixel art del mapa sobre canvas
  js/ui.js            paneles, mercado, modales
  js/main.js          arranque y bucle
```

---

<details>
<summary>Plantilla Streamlit original</summary>

```
$ pip install -r requirements.txt
$ streamlit run streamlit_app.py
```
</details>
