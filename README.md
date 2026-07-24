# 📋 PackList

Una app móvil **MVP** extremadamente simple para crear listas de equipaje —
para viajes, vacaciones o cualquier actividad. Sin login, sin nube, sin
fricción: todo se guarda **localmente en tu dispositivo**.

Es una PWA (Progressive Web App) autónoma en HTML/CSS/JavaScript puro, sin
dependencias ni paso de compilación. Funciona offline y puede instalarse en la
pantalla de inicio del móvil.

## Funciones (solo lo esencial)

- **Crea listas** con nombre libre.
- **Añade ítems** en texto libre a un checklist vertical.
- **Marca / desmarca** cada ítem tocándolo — al marcarlo se muestra tachado y
  atenuado.
- **Elimina ítems** deslizando hacia la izquierda o con una pulsación larga
  (con opción de **deshacer**).
- La **pantalla principal** muestra todas tus listas con su nombre y un
  indicador de `marcados / totales`, más un botón **+** para crear una lista
  nueva.
- **Almacenamiento local** (`localStorage`): tus datos nunca salen del
  dispositivo. No hay cuentas ni sincronización.

Deliberadamente **no** incluye compartir, categorías, recordatorios,
notificaciones ni fotos. Es una base mínima pensada para ampliarse más adelante.

## Cómo ejecutarla

Al ser estática, basta con servir la carpeta con cualquier servidor HTTP:

```bash
python3 -m http.server 8501
```

Luego abre `http://localhost:8501` en el navegador (idealmente en móvil o en la
vista de dispositivo móvil de las herramientas de desarrollo).

> El service worker y `localStorage` requieren servirla por HTTP; abrir el
> `index.html` directamente con `file://` puede limitar esas funciones.

## Instalar como app

En un navegador móvil compatible, usa **«Añadir a la pantalla de inicio»**.
PackList se abrirá en pantalla completa como una app nativa y seguirá
funcionando sin conexión.

## Estructura

| Archivo                   | Propósito                                             |
| ------------------------- | ----------------------------------------------------- |
| `index.html`              | Estructura de las dos vistas (listas y detalle).      |
| `styles.css`              | Estilo minimalista mono, adaptable a claro/oscuro.    |
| `app.js`                  | Estado, persistencia local, navegación y gestos.      |
| `sw.js`                   | Service worker para funcionamiento offline.           |
| `manifest.webmanifest`    | Metadatos de la PWA (nombre, iconos, colores).        |
| `assets/`                 | Iconos de la app.                                     |
