# Life RPG

App de hábitos que convierte tu día a día en un juego de rol simple. Completa
hábitos buenos para ganar XP y monedas, sube de nivel, evita los hábitos malos
que restan vida y gasta tus monedas en recompensas personales.

Construida con **React Native + Expo Router + TypeScript**. Todo el progreso se
guarda localmente en el dispositivo con **AsyncStorage** (en web usa
`localStorage`). No hay backend, ni registro, ni conexión obligatoria.

## Cómo ejecutar

```bash
cd life-rpg
npm install
npm start        # abre Expo (Android / iOS / web)
npm run web      # ejecuta directamente la versión web
```

Expo Go permite abrir la app en un teléfono escaneando el QR. La misma base de
código funciona como web responsive con aspecto de app móvil.

## Concepto

El jugador tiene cuatro estadísticas: **Nivel**, **XP**, **Monedas** y **Vida**
(máximo 1000). Se empieza en nivel 1 con 0 XP, 0 monedas y 1000 de vida.

- **Hábitos buenos** → suman XP y monedas.
- **Hábitos malos** → restan vida.
- Cada hábito se marca **una vez por día** y se reactiva al cambiar de día.
- Al quedarse sin vida aparece un castigo obligatorio para recuperarla.
- Las monedas se gastan en la **tienda**.

### Niveles y rangos

La XP para subir sigue la fórmula `round(100 × 1.2^(nivel-1))`. El nivel máximo
es 46. Los rangos según el nivel son: Aprendiz, Explorador, Aventurero, Héroe,
Maestro y Gran Maestro.

## Estructura del proyecto

```
app/                 Pantallas (Expo Router)
  _layout.tsx        Layout raíz + providers + modales globales
  (tabs)/            Navegación inferior: Inicio, Hábitos, Tienda, Perfil
components/          Componentes reutilizables (StatBar, HabitCard, ...)
context/             Estado global del jugador (PlayerContext)
storage/             Persistencia con AsyncStorage
types/               Interfaces de TypeScript
utils/               Cálculos de nivel, fechas, ids
constants/           Colores, hábitos iniciales, recompensas, config
```

## Componentes principales

`StatBar`, `HabitCard`, `ShopItemCard`, `PixelCharacter`, `LevelUpModal`,
`LifeZeroModal`, `BottomNavigation`, además de formularios reutilizables para
crear hábitos y recompensas.
