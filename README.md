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
| **Carácter de cada ciudad** | Once arquetipos (villa pesquera, ciudad minera, corte principesca, ciudad santa, plaza militar, puerto franco, comarca agrícola, gremios, universidad, encrucijada de caravanas, villa fronteriza). Cada uno inclina su producción, su demanda, sus impuestos, lo que prohíbe y el peligro de sus caminos. Al entrar, una línea te dice qué esperar. |
| **Fama** | Seis facetas —honrado, benefactor, contrabandista, corsario, especulador, mercader imperial— que crecen con lo que haces, no con lo que tienes. Cambian impuestos, márgenes, contratos y si una ciudad te veta las puertas. |
| **Memoria** | Las ciudades guardan hechos concretos («nos trajo grano durante la hambruna y no nos desangró») y te los recuerdan años después al llegar o en la taberna. Los rivales también, y sus herederos heredan la opinión. |
| **Generaciones** | Los mercaderes rivales envejecen, se retiran y dejan la casa a un hijo que conserva el apellido, el capital mermado y la memoria de lo que hiciste. Una casa arruinada puede reabrir una generación después. |
| **Grandes acontecimientos** | Cada varios meses cae uno sobre una región entera durante estaciones: la Gran Guerra, la Peste Negra, la Gran Hambruna, la Fiebre del Oro, la Feria de las Naciones, la Revolución de los Talleres, el Gran Bloqueo o la Paz Dorada. |
| **Lugares por descubrir** | Ruinas, pecios, monasterios, caravanas perdidas, minas abandonadas, oasis e islas sin nombre. Unos dan botín; otros, ventajas permanentes: una mina que rinde cada mes, rutas más rápidas o mares más seguros. |
| **Encargos descomunales** | Pedidos de cientos de unidades con plazos de estaciones, que se entregan por partes. No caben en una carreta: hacen falta flotas. |
| **Mercado por puestos** | Alterna entre la tabla y una vista de puestos con su tendero, que comenta lo que le sobra y lo que escasea. |
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
  Rombo relleno = visitada · rombo hueco = la has visto pero no pisado · punto de color = comerciante rival.
- **Mercado**: agrupado por categoría y plegable, con las gangas del día destacadas arriba. Clic en un bien
  para desplegar compra/venta, y dentro su **ficha**: todos los mercados que recuerdas (compra, venta, días
  de viaje, antigüedad del dato) y la mejor operación posible desde donde estás, con la ganancia estimada.
  En un bien prohibido, la ficha indica el porcentaje exacto de que te pillen al venderlo.
- **Bodega**: clic en un artículo para abrir su panel de venta, con deslizador para elegir cuántos,
  el total que recibes y la ganancia frente a lo que pagaste.
- **Oro en mano** es lo que puedes gastar ahora; **patrimonio** es tu marcador (oro + mercancía +
  flota + negocios − deudas) y lo que ordena la tabla de los más ricos.
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
  js/lore.js          fama, memoria de las ciudades, generaciones de rivales
  js/economy.js       precios, oferta/demanda, sucesos, grandes acontecimientos, contratos
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
