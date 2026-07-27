/* =========================================================================
   Merchant's Odyssey — economía viva: precios, oferta/demanda, eventos
   ========================================================================= */
'use strict';

/* ------------------------------- Precios --------------------------------- */
function needOf(c, g) {
  return Math.max(8, (c.cons[g] || 0) * 20 + (c.prod[g] || 0) * 8);
}
/** Precio "justo" según stock relativo. */
function fairPrice(c, g, stockOverride) {
  const good = GOOD[g];
  const need = needOf(c, g);
  const stock = Math.max(0, stockOverride === undefined ? c.stock[g] : stockOverride);
  const ratio = stock / need;
  let m = Math.pow(2 / (1 + ratio), 1.25);
  if (ratio < 0.35) m *= 1 + (0.35 - ratio) * 2.4;   // pánico por escasez
  if (ratio > 3.5) m *= 0.92;                         // saturación
  let p = good.base * clamp(m, 0.32, 4.2);
  // riqueza: los lujos valen más donde hay dinero
  if (good.tag === 'lujo' || good.tag === 'joyas') p *= Math.pow(c.wealth, 0.7);
  if (good.tag === 'alimento') p *= Math.pow(c.wealth, 0.15);
  // efectos activos
  p *= mulOf(c.demandMod, g);
  // topes suaves: se comprimen en vez de cortar, así dos bienes carísimos
  // no acaban exactamente en la misma cifra
  const hi = good.base * 3.2, room = good.base * 3.8;      // asíntota ≈ 7× lo normal
  if (p > hi) p = hi + room * (1 - Math.exp(-(p - hi) / room));
  const lo = good.base * 0.45, down = good.base * 0.16;    // asíntota ≈ 0.29×
  if (p < lo) p = lo - down * (1 - Math.exp(-(lo - p) / down));
  return p;
}
function mulOf(map, g) {
  let m = 1;
  if (!map) return 1;
  if (map['*']) m *= map['*'];
  if (map[g]) m *= map[g];
  const tag = GOOD[g].tag;
  if (map['@' + tag]) m *= map['@' + tag];
  return m;
}
/** Precio de compra (lo que paga el jugador) y de venta (lo que recibe). */
function spreadOf(c) {
  return clamp(0.085 - c.pop / 320000 - (c.playerRep || 0) * 0.003, 0.028, 0.095);
}
function buyPriceAt(c, g, stockOverride) {
  return fairPrice(c, g, stockOverride) * (1 + spreadOf(c));
}
function sellPriceAt(c, g, stockOverride) {
  return fairPrice(c, g, stockOverride) * (1 - spreadOf(c));
}

/** Coste total de comprar n unidades (con impacto de mercado). */
function costToBuy(c, g, n) {
  let total = 0, stock = c.stock[g];
  const chunk = Math.max(1, Math.ceil(n / 120));
  let left = n;
  while (left > 0) {
    const k = Math.min(chunk, left);
    total += buyPriceAt(c, g, stock - k / 2) * k;
    stock -= k; left -= k;
  }
  return total;
}
function revenueToSell(c, g, n) {
  let total = 0, stock = c.stock[g];
  const chunk = Math.max(1, Math.ceil(n / 120));
  let left = n;
  while (left > 0) {
    const k = Math.min(chunk, left);
    total += sellPriceAt(c, g, stock + k / 2) * k;
    stock += k; left -= k;
  }
  return total;
}

/* --------------------------- Efectos y eventos --------------------------- */
/* Un efecto vive en una ciudad: multiplicadores de producción/demanda,
   ajustes de población, impuestos e inestabilidad.                          */
const EVENTS = [
  {
    id: 'guerra', name: 'Guerra', icon: '⚔️', w: 10, dur: [45, 160],
    news: c => `${c.name} entra en guerra. Los mercados de armas se disparan.`,
    make: () => ({ prodMul: { '*': 0.75 }, demMul: { '@arma': 4.2, grano: 1.7, pan: 1.6, medicina: 2.4, hierro: 1.9, caballo: 1 }, taxAdd: 0.07, unrestAdd: 0.25, popMul: 0.9994, danger: 0.10 }),
  },
  {
    id: 'paz', name: 'Paz firmada', icon: '🕊️', w: 4, dur: [40, 90],
    cond: c => c.events.some(e => e.id === 'guerra'),
    news: c => `${c.name} firma la paz. Vuelve el comercio y el turismo.`,
    make: () => ({ prodMul: { '*': 1.15 }, demMul: { '@lujo': 1.6, vino: 1.7, joyas: 1.5 }, taxAdd: -0.02, unrestAdd: -0.2, ends: ['guerra'] }),
  },
  {
    id: 'peste', name: 'Peste', icon: '☠️', w: 7, dur: [25, 70],
    news: c => `Una peste asola ${c.name}. La medicina vale su peso en oro.`,
    make: () => ({ prodMul: { '*': 0.55 }, demMul: { medicina: 6.5, hierbas: 3.4, vino: 1.6, '@alimento': 0.8 }, popMul: 0.9975, unrestAdd: 0.3 }),
  },
  {
    id: 'hambruna', name: 'Hambruna', icon: '🥀', w: 8, dur: [25, 65],
    news: c => `Hambruna en ${c.name}: el grano se paga a precio de oro.`,
    make: () => ({ prodMul: { grano: 0.15, harina: 0.4, pan: 0.4, uva: 0.3 }, demMul: { grano: 2.6, pan: 2.8, harina: 2.4, pescado: 1.9 }, popMul: 0.9985, unrestAdd: 0.35 }),
  },
  {
    id: 'sequia', name: 'Sequía', icon: '🌵', w: 7, dur: [30, 90],
    cond: c => ['plains', 'savanna', 'desert'].includes(c.biome),
    news: c => `Sequía prolongada alrededor de ${c.name}.`,
    make: () => ({ prodMul: { grano: 0.35, uva: 0.3, hierbas: 0.5, lana: 0.7 }, demMul: { grano: 1.5, pescado: 1.3 } }),
  },
  {
    id: 'minahallada', name: 'Mina descubierta', icon: '⛏️', w: 8, dur: [120, 400],
    cond: c => ['mountain', 'hills', 'peak', 'desert'].includes(c.biome),
    news: c => `¡Se descubre una veta de mineral cerca de ${c.name}!`,
    make: () => ({ prodMul: { mineral: 3.4, carbon: 2.2, gemas: 2.0, piedra: 1.5 }, popMul: 1.0016, wealthAdd: 0.10 }),
  },
  {
    id: 'minaagotada', name: 'Mina agotada', icon: '🕯️', w: 6, dur: [140, 400],
    cond: c => (c.prod.mineral || 0) > 1,
    news: c => `La mina de ${c.name} se agota. Los mineros emigran.`,
    make: () => ({ prodMul: { mineral: 0.2, carbon: 0.4, gemas: 0.15 }, popMul: 0.9992, wealthAdd: -0.08 }),
  },
  {
    id: 'feria', name: 'Feria internacional', icon: '🎪', w: 11, dur: [10, 22],
    news: c => `Feria internacional en ${c.name}: acuden compradores de todo el mundo.`,
    make: () => ({ demMul: { '@lujo': 2.6, ropa: 2.2, joyas: 2.4, vino: 1.9, muebles: 2.0, especias: 2.1 }, wealthAdd: 0.04 }),
  },
  {
    id: 'boom', name: 'Auge industrial', icon: '🏭', w: 8, dur: [60, 160],
    news: c => `${c.name} vive un auge industrial: los talleres no paran.`,
    make: () => ({ prodMul: { hierro: 2.0, herram: 2.2, tela: 1.8, tablones: 1.8, ropa: 1.6 }, demMul: { mineral: 1.8, carbon: 1.9, madera: 1.7, lana: 1.6 }, popMul: 1.0014, wealthAdd: 0.12 }),
  },
  {
    id: 'revolucion', name: 'Revolución', icon: '🚩', w: 5, dur: [20, 60],
    cond: c => c.unrest > 0.35,
    news: c => `¡Revolución en ${c.name}! Cae el gobierno y con él los impuestos.`,
    make: () => ({ prodMul: { '*': 0.6 }, demMul: { '@arma': 2.6, '@alimento': 1.4 }, taxAdd: -0.05, unrestAdd: -0.15, danger: 0.06 }),
  },
  {
    id: 'impuestos', name: 'Nuevos impuestos', icon: '📜', w: 9, dur: [30, 120],
    news: c => `${c.name} aprueba nuevos aranceles portuarios.`,
    make: () => ({ taxAdd: 0.09, unrestAdd: 0.12, demMul: { '@lujo': 0.85 } }),
  },
  {
    id: 'librecomercio', name: 'Libre comercio', icon: '🤝', w: 7, dur: [40, 140],
    news: c => `${c.name} declara puerto franco: aranceles a la baja.`,
    make: () => ({ taxAdd: -0.055, demMul: { '*': 1.1 }, wealthAdd: 0.05 }),
  },
  {
    id: 'erupcion', name: 'Erupción volcánica', icon: '🌋', w: 3, dur: [15, 45],
    cond: c => ['mountain', 'peak', 'hills'].includes(c.biome),
    news: c => `Una erupción cubre de ceniza los campos de ${c.name}.`,
    make: () => ({ prodMul: { '*': 0.4, grano: 0.15 }, demMul: { grano: 2.2, madera: 1.8, medicina: 1.8 }, popMul: 0.997, stockHit: 0.35 }),
  },
  {
    id: 'descubrimiento', name: 'Descubrimiento técnico', icon: '💡', w: 6, dur: [90, 300],
    news: c => `Los gremios de ${c.name} perfeccionan un nuevo método de producción.`,
    make: () => ({ prodMul: { harina: 1.8, pan: 1.7, tablones: 1.7, hierro: 1.6, tela: 1.7, cuero: 1.6 }, wealthAdd: 0.08 }),
  },
  {
    id: 'inmigracion', name: 'Oleada migratoria', icon: '🧳', w: 6, dur: [40, 120],
    news: c => `Miles de familias llegan a ${c.name} buscando fortuna.`,
    make: () => ({ popMul: 1.0028, demMul: { '@alimento': 1.5, tela: 1.3, madera: 1.4 }, unrestAdd: 0.1 }),
  },
  {
    id: 'moda', name: 'Capricho de la moda', icon: '👑', w: 9, dur: [20, 60],
    news: c => `En ${c.name} nadie quiere vestir lo de ayer.`,
    make: () => ({ demMul: { ropa: 3.0, tela: 2.2, joyas: 2.0 } }),
  },
  {
    id: 'plagaganado', name: 'Plaga de ganado', icon: '🐑', w: 6, dur: [30, 80],
    cond: c => (c.prod.lana || 0) > 0.6,
    news: c => `Una plaga diezma los rebaños de ${c.name}.`,
    make: () => ({ prodMul: { lana: 0.2, pieles: 0.3 }, demMul: { lana: 2.0, tela: 1.6, cuero: 1.7 } }),
  },
  {
    id: 'bendicion', name: 'Cosecha excepcional', icon: '🌻', w: 8, dur: [25, 60],
    news: c => `Cosecha récord en ${c.name}: los graneros rebosan.`,
    make: () => ({ prodMul: { grano: 2.8, uva: 2.2, hierbas: 1.8 }, demMul: { grano: 0.75 } }),
  },
];

function makeEvent(def, c) {
  const e = Object.assign({ id: def.id, name: def.name, icon: def.icon }, def.make());
  e.daysLeft = rint(def.dur[0], def.dur[1]);
  e.total = e.daysLeft;
  if (e.stockHit) {
    for (const g of GOOD_IDS) c.stock[g] *= (1 - e.stockHit * rrange(0.5, 1));
  }
  if (e.wealthAdd) c.wealth = clamp(c.wealth + e.wealthAdd, 0.4, 3.2);
  if (e.ends) c.events = c.events.filter(x => !e.ends.includes(x.id));
  return e;
}

/* ------------------------- Motor de simulación --------------------------- */
class Economy {
  constructor(world, game) { this.world = world; this.game = game; }

  /** Un día completo del mundo. */
  tick(day) {
    const W = this.world;
    for (const c of W.cities) this.tickCity(c, day);
    this.tickEdges();
    this.spawnEvents(day);
    if (day % 5 === 0) for (const c of W.cities) this.refreshContracts(c, day);
  }

  tickCity(c, day) {
    // --- efectos activos -> multiplicadores del día
    const prodMul = {}, demMul = {};
    let popMul = 1, taxAdd = 0, unrestAdd = -0.006;
    for (let i = c.events.length - 1; i >= 0; i--) {
      const e = c.events[i];
      for (const k in e.prodMul || {}) prodMul[k] = (prodMul[k] || 1) * e.prodMul[k];
      for (const k in e.demMul || {}) demMul[k] = (demMul[k] || 1) * e.demMul[k];
      popMul *= e.popMul || 1;
      taxAdd += e.taxAdd || 0;
      unrestAdd += e.unrestAdd ? e.unrestAdd * 0.02 : 0;
      e.daysLeft--;
      if (e.daysLeft <= 0) c.events.splice(i, 1);
    }
    c.prodMod = prodMul; c.demandMod = demMul;
    if (c.baseTax === undefined) c.baseTax = c.tax;
    c.tax = clamp(c.baseTax + taxAdd, 0.005, 0.35);

    // --- producción (responde al precio: si sale a cuenta, se produce más)
    for (const g in c.prod) {
      const rel = (c.price[g] || GOOD[g].base) / GOOD[g].base;
      const supply = clamp(Math.pow(rel, 0.45), 0.55, 2.0);
      const amount = c.prod[g] * mulOf(prodMul, g) * supply * (1 - c.unrest * 0.5);
      c.stock[g] = (c.stock[g] || 0) + amount;
    }
    // --- consumo (elástico: si está carísimo, la gente compra menos)
    let foodWant = 0, foodGot = 0;
    for (const g in c.cons) {
      const rel = (c.price[g] || GOOD[g].base) / GOOD[g].base;
      const elas = clamp(Math.pow(rel, -(GOOD[g].tag === 'alimento' ? 0.35 : 0.7)), 0.22, 2.0);
      const want = c.cons[g] * mulOf(demMul, g) * elas;
      const got = Math.min(c.stock[g] || 0, want);
      c.stock[g] = Math.max(0, (c.stock[g] || 0) - got);
      if (GOOD[g].tag === 'alimento') { foodWant += want; foodGot += got; }
    }
    const foodSat = foodWant > 0 ? foodGot / foodWant : 1;
    unrestAdd += (0.75 - foodSat) * 0.03;
    c.unrest = clamp(c.unrest + unrestAdd, 0, 1);

    // --- caducidad y comercio de fondo (caravanas anónimas)
    for (const g of GOOD_IDS) {
      if (GOOD[g].perish) c.stock[g] *= 0.975;
      // caravanas anónimas: los faltantes se cubren rápido, los excedentes se van despacio
      const gap = needOf(c, g) - c.stock[g];
      c.stock[g] += gap > 0 ? gap * 0.032 : gap * 0.008;
      if (c.stock[g] < 0) c.stock[g] = 0;
    }

    // --- población y riqueza
    c.pop = Math.max(200, c.pop * popMul * (1 + (foodSat - 0.9) * 0.0025 - c.unrest * 0.0012));
    c.wealth = clamp(c.wealth + (foodSat - 0.85) * 0.0018 - c.unrest * 0.0009, 0.35, 3.2);
    if (day % 30 === 0) this.rescaleProduction(c);

    // --- precios pegajosos
    for (const g of GOOD_IDS) {
      const target = fairPrice(c, g);
      c.lastPrice[g] = c.price[g];
      c.price[g] = c.price[g] ? c.price[g] + (target - c.price[g]) * 0.34 : target;
      const h = c.priceHist[g];
      h.push(c.price[g]);
      if (h.length > 90) h.shift();
    }
  }

  /** Reescala producción/consumo cuando la población cambia mucho. */
  rescaleProduction(c) {
    const kpop = c.pop / 1000;
    if (!c.basePop) { c.basePop = c.pop; c.baseProd = Object.assign({}, c.prod); c.baseCons = Object.assign({}, c.cons); return; }
    const f = c.pop / c.basePop;
    for (const g in c.baseProd) c.prod[g] = c.baseProd[g] * f;
    for (const g in c.baseCons) c.cons[g] = c.baseCons[g] * f * (GOOD[g].tag === 'lujo' ? Math.pow(c.wealth, 1.2) : 1);
  }

  tickEdges() {
    for (const e of this.world.edges) {
      if (e.blocked > 0) e.blocked--;
      if (e.danger > 0) e.danger = Math.max(0, e.danger - 0.004);
      if (e.tollDays > 0) { e.tollDays--; if (e.tollDays === 0) e.toll = 0; }
    }
  }

  spawnEvents(day) {
    const W = this.world, G = this.game;
    // eventos de ciudad
    if (rnd() < 0.55) {
      const c = pick(W.cities);
      if (c.events.length < 3) {
        const opts = EVENTS.filter(d => (!d.cond || d.cond(c)) && !c.events.some(e => e.id === d.id));
        if (opts.length) {
          const def = pickW(opts.map(o => [o, o.w]));
          const ev = makeEvent(def, c);
          c.events.push(ev);
          if (ev.danger) for (const ei of W.adj[c.id]) W.edges[ei].danger += ev.danger;
          // solo llegan noticias de las tierras que conoces
          if (c.known) G.news(def.news(c), 'event', c.id, def.icon);
        }
      }
    }
    // eventos de ruta
    if (rnd() < 0.30) {
      const e = pick(W.edges);
      const A = W.cities[e.a], B = W.cities[e.b];
      const seen = A.known && B.known;
      if (e.type === 'sea' && rnd() < 0.6) {
        e.danger = clamp(e.danger + rrange(0.08, 0.22), 0, 0.6);
        if (seen) G.news(`Piratas avistados en la ruta ${A.name} — ${B.name}.`, 'route', A.id, '🏴‍☠️');
      } else if (rnd() < 0.45) {
        e.blocked = rint(8, 30);
        if (seen) G.news(`La ruta ${A.name} — ${B.name} queda cortada (${e.type === 'sea' ? 'temporales' : 'nieve y desprendimientos'}).`, 'route', A.id, '❄️');
      } else {
        e.danger = clamp(e.danger + rrange(0.06, 0.18), 0, 0.6);
        if (seen) G.news(`Bandidos asaltan caravanas entre ${A.name} y ${B.name}.`, 'route', A.id, '🗡️');
      }
    }
    // nuevos puertos / rutas descubiertas
    if (rnd() < 0.02) {
      const pool = W.cities.filter(x => x.coastal && !x.shipyard);
      const c = pool.length ? pick(pool) : null;
      if (c) { c.shipyard = true; if (c.known) G.news(`${c.name} inaugura un astillero. Se abren nuevas rutas marítimas.`, 'event', c.id, '⚓'); }
    }
  }

  /* ------------------------------ Contratos ------------------------------ */
  refreshContracts(c, day) {
    c.contracts = c.contracts.filter(k => k.expires > day && !k.taken);
    const W = this.world;
    while (c.contracts.length < (c.pop > 6000 ? 3 : 2)) {
      const targets = W.cities.filter(o => o.id !== c.id && o.comp !== undefined);
      const to = pick(targets);
      if (!to) break;
      // pide algo que escasea en destino y abunda cerca
      const cand = GOOD_IDS.filter(g => (to.stock[g] || 0) < needOf(to, g) * 0.8);
      const g = cand.length ? pick(cand) : pick(GOOD_IDS);
      const d = dist(c.x, c.y, to.x, to.y);
      const qty = Math.max(5, Math.round(rrange(8, 60) * (GOOD[g].tier === 2 ? 0.4 : 1)));
      const unit = fairPrice(to, g);
      const reward = Math.round(unit * qty * rrange(1.35, 1.85) + d * 8);
      c.contracts.push({
        id: 'k' + day + '_' + c.id + '_' + Math.floor(rnd() * 1e6),
        good: g, qty, from: c.id, to: to.id,
        days: Math.round(d / 4 + rrange(14, 40)),
        reward, penalty: Math.round(reward * 0.35),
        expires: day + rint(20, 45), taken: false,
      });
    }
  }
}
