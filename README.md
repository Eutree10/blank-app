# OMA · Práctica diaria — Nivel 2

App web para entrenar problemas de la **Olimpíada Matemática Argentina (OMA)**.
Cada día te asigna un problema (o conjunto de problemas) **de Nivel 2** de forma
aleatoria y **sin repetir** los que ya completaste, con el objetivo de completarlos
todos con el tiempo.

Fuente de los enunciados: página oficial de OMA — <https://www.oma.org.ar/enunciados/index.htm>

## Cómo funciona

- **Una asignación por día**, con corte a las **00:00** (hora local).
- La selección es **random pero sin repetición**: nunca vuelve a salir un problema completado.
- Reglas por instancia:
  - **Intercolegial** → se asigna el **año completo** (todos los problemas de ese año).
  - **Zonal** → se asignan **2 problemas** por día.
- Si marcás la asignación como **completada**, pasa al **historial** y no vuelve a salir.
- Si **no** la completás antes de las 00:00, queda registrada como **vencida** (no se pierde
  el seguimiento) y sus problemas **vuelven al pool** para poder completarse más adelante.
- Cuando completás todo, aparece una **pantalla de felicitaciones**.

## Pantallas

1. **Hoy** — fecha, instancia, año, nivel, el/los problemas asignados, estado
   (pendiente / completado / vencido) y botón **Marcar como completado** con cuenta regresiva.
2. **Historial** — problemas completados (año, instancia, nivel y fecha), con opción de
   volver a verlos. Incluye el registro de los **no completados**.
3. **Progreso** — total disponibles, completados, pendientes y % de avance, desglosado por
   instancia (Intercolegial / Zonal).
4. **Datos** — importar/exportar el dataset en JSON y hacer copias de seguridad.

## Stack

- **Vite + React + TypeScript** (SPA).
- **Persistencia** en `localStorage` (versionada), aislada en `src/lib/storage.ts` para poder
  migrar a una base de datos real más adelante sin tocar la UI.
- Sin backend: funciona offline y se puede desplegar como sitio estático.

## Desarrollo

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck + build de producción -> dist/
npm run preview    # sirve el build
```

## Cargar los enunciados oficiales de OMA

El entorno donde se generó esta app tiene **bloqueado el acceso a `oma.org.ar`**, por lo que
no se pudieron scrapear los enunciados automáticamente. La app viene con un **dataset de
muestra** (marcado como tal) para probar toda la lógica desde el primer minuto.

Para cargar los problemas reales:

```bash
pip install -r requirements.txt
python scripts/scrape_oma.py            # genera public/oma-nivel2.json
python scripts/scrape_oma.py --list     # lista los certámenes detectados
```

Luego, en la app: **Datos → Subir archivo .json**. El import **reemplaza** el dataset y
**conserva tu historial** de completados (por `id` de problema).

> La estructura del sitio de OMA puede cambiar. El parseo está aislado en `parse_certamen()`
> dentro de `scripts/scrape_oma.py` para poder ajustarlo (o adaptarlo a PDFs) sin tocar el resto.

## Estructura de datos de un problema

```json
{
  "id": "Zonal-2020-N2-P1",
  "anio": 2020,
  "instancia": "Zonal",
  "nivel": 2,
  "numero": 1,
  "enunciado": "…",
  "fuente": "https://www.oma.org.ar/enunciados/…"
}
```

El estado por problema (`fecha_asignado`, `fecha_completado`, `estado`) se deriva del historial
de asignaciones y del registro de completados que guarda la app.

## Organización del código

```
src/
  types.ts             # modelo de datos
  data/seed.ts         # dataset de muestra (Nivel 2)
  lib/
    date.ts            # día / corte 00:00, cuenta regresiva
    random.ts          # RNG determinístico sembrado por fecha
    selection.ts       # motor de selección (reglas por instancia)
    assignment.ts      # asignación diaria: vencimientos + obtener/crear + completar
    progress.ts        # cálculo de progreso general y por instancia
    storage.ts         # persistencia + validación de imports
  store/useStore.tsx   # estado global + acciones (React context)
  components/ui.tsx     # tarjetas, badges, barra de progreso
  screens/             # Hoy, Historial, Progreso, Datos
scripts/scrape_oma.py  # scraper de enunciados oficiales
```
