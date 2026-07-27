/* =========================================================================
   Merchant's Odyssey — core: RNG, utilidades, datos del juego
   ========================================================================= */
'use strict';

/* ---------------------------------- RNG --------------------------------- */
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function hashStr(s) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

/** Generador global del mundo (determinista por semilla). */
let RNG = mulberry32(1);
function setSeed(seed) { RNG = mulberry32(seed >>> 0); }

const rnd = () => RNG();
const rint = (a, b) => a + Math.floor(RNG() * (b - a + 1));
const rrange = (a, b) => a + RNG() * (b - a);
const pick = (arr) => arr[Math.floor(RNG() * arr.length)];
function pickW(entries) { // [[valor, peso], ...]
  let total = 0; for (const e of entries) total += e[1];
  let r = RNG() * total;
  for (const e of entries) { r -= e[1]; if (r <= 0) return e[0]; }
  return entries[entries.length - 1][0];
}
function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(RNG() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; }
  return arr;
}

/* -------------------------------- Utilidades ---------------------------- */
const clamp = (v, a, b) => v < a ? a : (v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const dist = (x1, y1, x2, y2) => Math.hypot(x2 - x1, y2 - y1);

function fmt(n) {
  n = Math.round(n);
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + 'MM';
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(2) + 'M';
  return n.toLocaleString('es-ES');
}
function fmtGold(n) { return fmt(n) + ' ⦿'; }
function pct(n) { return (n >= 0 ? '+' : '') + Math.round(n * 100) + '%'; }

/* --------------------------------- Bienes -------------------------------- */
// tier 0 = materia prima · 1 = elaborado · 2 = manufacturado / lujo
const GOODS = [
  { id: 'grano',    name: 'Grano',        icon: '🌾', tier: 0, base: 8,   w: 1.0, tag: 'alimento' },
  { id: 'pescado',  name: 'Pescado',      icon: '🐟', tier: 0, base: 11,  w: 1.0, tag: 'alimento', perish: true },
  { id: 'madera',   name: 'Madera',       icon: '🪵', tier: 0, base: 7,   w: 1.4, tag: 'material' },
  { id: 'piedra',   name: 'Piedra',       icon: '🪨', tier: 0, base: 6,   w: 1.8, tag: 'material' },
  { id: 'mineral',  name: 'Mineral',      icon: '⛏️', tier: 0, base: 13,  w: 1.5, tag: 'material' },
  { id: 'carbon',   name: 'Carbón',       icon: '🕳️', tier: 0, base: 11,  w: 1.2, tag: 'material' },
  { id: 'lana',     name: 'Lana',         icon: '🐑', tier: 0, base: 15,  w: 0.9, tag: 'material' },
  { id: 'pieles',   name: 'Pieles',       icon: '🦌', tier: 0, base: 18,  w: 1.0, tag: 'material' },
  { id: 'sal',      name: 'Sal',          icon: '🧂', tier: 0, base: 14,  w: 1.0, tag: 'alimento' },
  { id: 'hierbas',  name: 'Hierbas',      icon: '🌿', tier: 0, base: 16,  w: 0.6, tag: 'lujo' },
  { id: 'uva',      name: 'Uva',          icon: '🍇', tier: 0, base: 19,  w: 1.0, tag: 'alimento', perish: true },
  { id: 'especias', name: 'Especias',     icon: '🌶️', tier: 0, base: 38,  w: 0.5, tag: 'lujo' },
  { id: 'gemas',    name: 'Gemas',        icon: '💎', tier: 0, base: 62,  w: 0.4, tag: 'lujo' },

  { id: 'harina',   name: 'Harina',       icon: '🥣', tier: 1, base: 23,  w: 1.0, tag: 'alimento' },
  { id: 'tablones', name: 'Tablones',     icon: '🪚', tier: 1, base: 21,  w: 1.2, tag: 'material' },
  { id: 'hierro',   name: 'Hierro',       icon: '🔩', tier: 1, base: 44,  w: 1.3, tag: 'material' },
  { id: 'tela',     name: 'Tela',         icon: '🧵', tier: 1, base: 40,  w: 0.8, tag: 'material' },
  { id: 'cuero',    name: 'Cuero',        icon: '🟫', tier: 1, base: 52,  w: 0.9, tag: 'material' },
  { id: 'herram',   name: 'Herramientas', icon: '🔧', tier: 1, base: 82,  w: 1.1, tag: 'equipo' },

  { id: 'pan',      name: 'Pan',          icon: '🍞', tier: 2, base: 17,  w: 0.8, tag: 'alimento', perish: true },
  { id: 'muebles',  name: 'Muebles',      icon: '🪑', tier: 2, base: 62,  w: 1.6, tag: 'lujo' },
  { id: 'espadas',  name: 'Espadas',      icon: '🗡️', tier: 2, base: 112, w: 1.0, tag: 'arma' },
  { id: 'armadura', name: 'Armaduras',    icon: '🛡️', tier: 2, base: 172, w: 1.4, tag: 'arma' },
  { id: 'ropa',     name: 'Ropa',         icon: '👕', tier: 2, base: 98,  w: 0.7, tag: 'lujo' },
  { id: 'vino',     name: 'Vino',         icon: '🍷', tier: 2, base: 74,  w: 1.1, tag: 'lujo' },
  { id: 'medicina', name: 'Medicina',     icon: '🧪', tier: 2, base: 138, w: 0.5, tag: 'medicina' },
  { id: 'joyas',    name: 'Joyas',        icon: '💍', tier: 2, base: 205, w: 0.3, tag: 'lujo' },
];
const GOOD = {}; GOODS.forEach((g, i) => { GOOD[g.id] = g; g.idx = i; });
const GOOD_IDS = GOODS.map(g => g.id);

/* --------------------------------- Recetas ------------------------------- */
/** Lotes que procesa cada nivel de taller al día. */
const FACTORY_BATCH = 6;
const RECIPES = [
  { id: 'molino',     name: 'Molino',        icon: '🥣', in: { grano: 2 },              out: { harina: 1 },   cost: 900,   days: 1 },
  { id: 'panaderia',  name: 'Panadería',     icon: '🍞', in: { harina: 1 },             out: { pan: 2 },      cost: 1200,  days: 1 },
  { id: 'aserradero', name: 'Aserradero',    icon: '🪚', in: { madera: 2 },             out: { tablones: 1 }, cost: 1000,  days: 1 },
  { id: 'carpint',    name: 'Carpintería',   icon: '🪑', in: { tablones: 2 },           out: { muebles: 1 },  cost: 2600,  days: 1 },
  { id: 'fundicion',  name: 'Fundición',     icon: '🔩', in: { mineral: 2, carbon: 1 }, out: { hierro: 1 },   cost: 3200,  days: 1 },
  { id: 'herreria',   name: 'Herrería',      icon: '🔧', in: { hierro: 1, tablones: 1 },out: { herram: 1 },   cost: 4200,  days: 1 },
  { id: 'armeria',    name: 'Armería',       icon: '🗡️', in: { hierro: 2 },             out: { espadas: 1 },  cost: 6000,  days: 1 },
  { id: 'tallerarm',  name: 'Taller de armaduras', icon: '🛡️', in: { hierro: 2, cuero: 1 }, out: { armadura: 1 }, cost: 9500, days: 1 },
  { id: 'telar',      name: 'Telar',         icon: '🧵', in: { lana: 2 },               out: { tela: 1 },     cost: 2200,  days: 1 },
  { id: 'sastreria',  name: 'Sastrería',     icon: '👕', in: { tela: 2 },               out: { ropa: 1 },     cost: 5200,  days: 1 },
  { id: 'curtiduria', name: 'Curtiduría',    icon: '🟫', in: { pieles: 2, sal: 1 },     out: { cuero: 1 },    cost: 3000,  days: 1 },
  { id: 'bodega',     name: 'Bodega',        icon: '🍷', in: { uva: 3 },                out: { vino: 1 },     cost: 4000,  days: 1 },
  { id: 'botica',     name: 'Botica',        icon: '🧪', in: { hierbas: 2, vino: 1 },   out: { medicina: 1 }, cost: 7800,  days: 1 },
  { id: 'joyeria',    name: 'Joyería',       icon: '💍', in: { gemas: 2, hierro: 1 },   out: { joyas: 1 },    cost: 12000, days: 1 },
];
const RECIPE = {}; RECIPES.forEach(r => RECIPE[r.id] = r);

/* -------------------------------- Vehículos ------------------------------ */
// terreno: 'land' | 'sea' · era: 0 clásica, 1 industrial, 2 moderna
const VEHICLES = [
  { id: 'mochila',  name: 'Mochila',        icon: '🎒', terrain: 'land', cap: 14,   speed: 1.00, cost: 0,      up: 0,   era: 0 },
  { id: 'mula',     name: 'Mula de carga',  icon: '🐴', terrain: 'land', cap: 40,   speed: 1.00, cost: 380,    up: 1.4, era: 0 },
  { id: 'carreta',  name: 'Carreta',        icon: '🛒', terrain: 'land', cap: 120,  speed: 1.15, cost: 900,    up: 3,   era: 0 },
  { id: 'caravana', name: 'Caravana',       icon: '🐫', terrain: 'land', cap: 340,  speed: 1.10, cost: 2400,   up: 7,   era: 0 },
  { id: 'diligenc', name: 'Diligencia',     icon: '🚚', terrain: 'land', cap: 190,  speed: 1.90, cost: 6000,   up: 12,  era: 0 },
  { id: 'tren',     name: 'Tren de vapor',  icon: '🚂', terrain: 'land', cap: 1600, speed: 2.60, cost: 45000,  up: 70,  era: 1 },
  { id: 'camion',   name: 'Convoy de camiones', icon: '🚛', terrain: 'land', cap: 1000, speed: 3.40, cost: 90000, up: 130, era: 2 },
  { id: 'avion',    name: 'Avión de carga', icon: '✈️', terrain: 'land', cap: 500,  speed: 7.00, cost: 260000, up: 380, era: 2 },

  { id: 'barca',    name: 'Barca',          icon: '🛶', terrain: 'sea',  cap: 60,   speed: 1.20, cost: 900,    up: 2.5, era: 0 },
  { id: 'coca',     name: 'Coca mercante',  icon: '⛵', terrain: 'sea',  cap: 260,  speed: 1.25, cost: 3200,   up: 8,   era: 0 },
  { id: 'galeon',   name: 'Galeón',         icon: '🚢', terrain: 'sea',  cap: 800,  speed: 1.15, cost: 8500,   up: 22,  era: 0 },
  { id: 'cliper',   name: 'Clíper',         icon: '⛴️', terrain: 'sea',  cap: 520,  speed: 2.20, cost: 22000,  up: 40,  era: 0 },
  { id: 'vapor',    name: 'Buque de vapor', icon: '🛳️', terrain: 'sea',  cap: 2000, speed: 1.90, cost: 70000,  up: 110, era: 1 },
  { id: 'portacont',name: 'Portacontenedores', icon: '🏗️', terrain: 'sea', cap: 6000, speed: 2.30, cost: 300000, up: 430, era: 2 },
];
const VEHICLE = {}; VEHICLES.forEach(v => VEHICLE[v.id] = v);

/* --------------------------------- Biomas -------------------------------- */
const BIOMES = {
  ocean:    { name: 'Océano',   land: false, cost: 1.0, col: ['#0d2233', '#123049', '#16405f'] },
  shallow:  { name: 'Bajíos',   land: false, cost: 1.0, col: ['#17506f', '#1c5f80', '#227091'] },
  beach:    { name: 'Costa',    land: true,  cost: 1.0, col: ['#c4a86c', '#d3b878', '#b99c60'] },
  plains:   { name: 'Llanura',  land: true,  cost: 1.0, col: ['#5b7a3a', '#688a41', '#527034'] },
  forest:   { name: 'Bosque',   land: true,  cost: 1.4, col: ['#2f5530', '#376138', '#294b2a'] },
  jungle:   { name: 'Selva',    land: true,  cost: 1.8, col: ['#25562f', '#2c6537', '#1f4a29'] },
  desert:   { name: 'Desierto', land: true,  cost: 1.5, col: ['#c2a260', '#d1b26e', '#b39355'] },
  savanna:  { name: 'Sabana',   land: true,  cost: 1.1, col: ['#8a8b45', '#98994e', '#7c7d3d'] },
  tundra:   { name: 'Tundra',   land: true,  cost: 1.6, col: ['#7d8a86', '#8c9995', '#6f7c78'] },
  snow:     { name: 'Nieve',    land: true,  cost: 2.1, col: ['#cfd8da', '#dee6e8', '#bfc9cb'] },
  hills:    { name: 'Colinas',  land: true,  cost: 1.6, col: ['#6b6a3e', '#797846', '#5d5c35'] },
  mountain: { name: 'Montaña',  land: true,  cost: 2.6, col: ['#736a63', '#82796f', '#645c56'] },
  peak:     { name: 'Cumbre',   land: true,  cost: 3.4, col: ['#a9a29a', '#bab3aa', '#98918a'] },
};

/* ---- Producción base por bioma (unidades/día por 1000 habitantes) -------- */
const BIOME_PROD = {
  plains:   { grano: 3.2, lana: 1.1, uva: 0.5 },
  forest:   { madera: 3.0, pieles: 1.0, hierbas: 0.8 },
  jungle:   { madera: 2.0, especias: 0.9, hierbas: 1.2 },
  desert:   { sal: 1.6, especias: 0.8, piedra: 0.6 },
  savanna:  { grano: 1.4, lana: 1.2, pieles: 0.7 },
  tundra:   { pieles: 1.4, lana: 0.8, madera: 0.5 },
  snow:     { pieles: 1.2, mineral: 0.6 },
  hills:    { mineral: 1.6, carbon: 1.4, piedra: 1.4, lana: 0.6 },
  mountain: { mineral: 2.4, carbon: 1.6, piedra: 1.8, gemas: 0.25 },
  peak:     { mineral: 1.8, gemas: 0.4, piedra: 1.2 },
  beach:    { pescado: 2.4, sal: 1.2 },
};

/* --------------------- Especialidades / industrias ----------------------- */
const SPECIALTIES = [
  { id: 'granero',   name: 'Granero regional', prod: { grano: 3.0, harina: 0.8 }, icon: '🌾' },
  { id: 'puertoPesq',name: 'Puerto pesquero',  prod: { pescado: 3.2 },            icon: '🐟', coastal: true },
  { id: 'minera',    name: 'Cuenca minera',    prod: { mineral: 2.6, carbon: 1.6 },icon: '⛏️' },
  { id: 'gemas',     name: 'Yacimiento de gemas', prod: { gemas: 0.7 },           icon: '💎' },
  { id: 'forja',     name: 'Ciudad de forjas', prod: { hierro: 1.4, herram: 0.5 },icon: '🔩' },
  { id: 'textil',    name: 'Distrito textil',  prod: { tela: 1.3, ropa: 0.35 },   icon: '🧵' },
  { id: 'vinicola',  name: 'Región vinícola',  prod: { uva: 2.0, vino: 0.5 },     icon: '🍷' },
  { id: 'maderera',  name: 'Comarca maderera', prod: { madera: 3.0, tablones: 0.8 }, icon: '🪵' },
  { id: 'especiera', name: 'Ruta de especias', prod: { especias: 1.2 },           icon: '🌶️' },
  { id: 'boticaria', name: 'Escuela de boticarios', prod: { medicina: 0.35, hierbas: 1.0 }, icon: '🧪' },
  { id: 'astillero', name: 'Astillero',        prod: { tablones: 1.2 },           icon: '⚓', coastal: true, shipyard: true },
  { id: 'banca',     name: 'Plaza bancaria',   prod: {},                          icon: '🏦', bank: true },
  { id: 'joyera',    name: 'Gremio de joyeros',prod: { joyas: 0.28 },             icon: '💍' },
  { id: 'ganadera',  name: 'Tierras ganaderas',prod: { lana: 2.2, pieles: 1.6 },  icon: '🐑' },
];
const SPECIALTY = {}; SPECIALTIES.forEach(s => SPECIALTY[s.id] = s);

/* --------------------------- Consumo por cultura ------------------------- */
// Consumo base por 1000 hab/día. Todas las ciudades comen; las ricas consumen lujo.
const BASE_CONSUME = {
  grano: 1.6, pan: 1.1, pescado: 0.9, sal: 0.5, madera: 1.0, tablones: 0.6,
  piedra: 0.5, carbon: 0.7, mineral: 0.6, hierro: 0.5, herram: 0.35,
  lana: 0.5, tela: 0.5, ropa: 0.35, pieles: 0.4, cuero: 0.35,
  uva: 0.4, vino: 0.45, hierbas: 0.3, medicina: 0.22, especias: 0.3,
  muebles: 0.25, espadas: 0.14, armadura: 0.09, gemas: 0.1, joyas: 0.1, harina: 0.7,
};

/* --------------------------- Nombres procedurales ------------------------ */
const NAME_A = ['Val', 'Kar', 'Mor', 'Bel', 'Tor', 'San', 'Cas', 'Nor', 'Vel', 'Dor', 'Mar', 'Ald', 'Gran', 'Sel', 'Tar', 'Pun', 'Rio', 'Al', 'Ker', 'Zam', 'Bra', 'Ost', 'Lum', 'Fen', 'Cor', 'Vic', 'Ner', 'Sil', 'Tras', 'Mon'];
const NAME_B = ['a', 'o', 'e', 'i', 'ia', 'or', 'an', 'en', 'ar', 'un', 'ur', 'is', 'os', 'ea'];
const NAME_C = ['dor', 'mar', 'burgo', 'ford', 'gard', 'stad', 'ville', 'polis', 'heim', 'grad', 'thia', 'vera', 'landa', 'cea', 'nia', 'rica', 'tona', 'sur', 'nova', 'puerto', 'lar', 'ria', 'zia', 'mira'];
function genCityName(used) {
  for (let i = 0; i < 60; i++) {
    let n = pick(NAME_A) + pick(NAME_B) + (rnd() < 0.72 ? pick(NAME_C) : '');
    n = n.charAt(0).toUpperCase() + n.slice(1);
    if (rnd() < 0.10) n = pick(['Puerto ', 'Alto ', 'Villa ', 'Nueva ', 'San ']) + n;
    if (!used.has(n)) { used.add(n); return n; }
  }
  return 'Ciudad ' + used.size;
}
const MERCH_FIRST = ['Alba', 'Bruno', 'Casilda', 'Dimitri', 'Eneko', 'Fátima', 'Goran', 'Helia', 'Ivo', 'Jazmín', 'Kiro', 'Lucía', 'Marek', 'Nadia', 'Osmán', 'Petra', 'Quim', 'Rocío', 'Sasha', 'Tomás', 'Ulla', 'Vera', 'Wilem', 'Xenia', 'Yusuf', 'Zoe', 'Anselmo', 'Beatriz', 'Ciro', 'Delia', 'Efrén', 'Greta', 'Halim', 'Irina'];
const MERCH_LAST = ['Vareda', 'Kostas', 'Almeida', 'Doriac', 'Verlan', 'Ibarra', 'Marchetti', 'Solvig', 'Osoria', 'Kandel', 'Frey', 'Trevisi', 'Bragan', 'Nurel', 'Cerdán', 'Halvor', 'Ríos', 'Zamit', 'Quiroga', 'Estévez', 'Lund', 'Bakri', 'Oteiza', 'Vantar'];
const COMPANY_SUFFIX = ['& Hijos', 'Hermanos', 'y Cía.', 'Consorcio', 'Casa', 'Compañía', 'Sociedad', 'Gremio'];

/* --------------------------- Títulos del jugador ------------------------- */
const TITLES = [
  { at: 0, name: 'Buhonero' },
  { at: 2000, name: 'Mercachifle' },
  { at: 8000, name: 'Mercader' },
  { at: 25000, name: 'Comerciante de renombre' },
  { at: 75000, name: 'Naviero' },
  { at: 200000, name: 'Magnate' },
  { at: 600000, name: 'Príncipe mercante' },
  { at: 1500000, name: 'Amo de las rutas' },
  { at: 5000000, name: 'Leyenda del comercio' },
];
function titleFor(nw) { let t = TITLES[0]; for (const x of TITLES) if (nw >= x.at) t = x; return t.name; }

const MONTHS = ['Ventoso', 'Germinal', 'Floreal', 'Pradial', 'Mesidor', 'Termidor', 'Fructidor', 'Vendimia', 'Brumario', 'Frimario', 'Nivoso', 'Pluvioso'];
function dateStr(day) {
  const y = Math.floor(day / 360) + 1;
  const m = Math.floor((day % 360) / 30);
  const d = (day % 30) + 1;
  return `${d} de ${MONTHS[m]}, año ${y}`;
}
