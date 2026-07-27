# 🎡 Ruleta de rarezas

Una ruleta para cuando estás aburrido y no sabes qué hacer: gira y te sale un tema
fascinante que casi nadie conoce, con una explicación corta y tres hilos concretos
por los que empezar a investigar.

**Probarla:** https://raw.githack.com/eutree10/blank-app/claude/topic-roulette-app-ir0mbh/index.html

## Qué hace

- **72 temas** repartidos en 10 categorías: Ciencia, Historia, Mente, Lenguaje,
  Naturaleza, Cosmos, Tecnología, Sociedad, Arte y Lugares.
- **La ruleta** hace pasar las palabras a toda velocidad y va frenando hasta parar
  en una. No repite temas hasta que se agotan los disponibles.
- **Ficha del tema**: de qué va en tres frases y *por dónde empezar*, con tres
  preguntas que se buscan de un clic.
- **Investigar**: accesos directos a Wikipedia, Google, YouTube y Google Académico
  con la búsqueda ya montada.
- **Mi lista**: guarda temas para más tarde.
- **Filtros** por categoría, atajo de teclado (barra espaciadora para girar) y
  soporte de `prefers-reduced-motion`.

Todo el estado (lista guardada, temas ya vistos, filtros) vive en el `localStorage`
del navegador. No hay servidor ni cuentas.

## Estructura

```
index.html          markup y estructura
assets/styles.css   diseño (paleta oscura, acento dorado, serif de display)
assets/app.js       ruleta, filtros, guardados y persistencia
assets/topics.js    el banco de temas — edita este archivo para añadir más
```

Es una web estática sin dependencias ni build. Para verla en local:

```
python3 -m http.server 8000
# y abrir http://localhost:8000
```

## Añadir un tema

Basta con meter un objeto más en `assets/topics.js`:

```js
{
  t: "Nombre del tema",
  c: "Ciencia",                       // categoría (crea una nueva si quieres)
  h: "El gancho, una frase.",
  d: "De qué va, en dos o tres frases.",
  q: ["Pregunta 1", "Pregunta 2", "Pregunta 3"]
}
```

Las categorías se generan solas a partir del campo `c`.
