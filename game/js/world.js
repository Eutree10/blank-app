/* =========================================================================
   Merchant's Odyssey — generación procedural del mundo
   ========================================================================= */
'use strict';

const MAP_W = 224, MAP_H = 144;
const TILES_PER_DAY = 6.5;   // velocidad base de viaje

/* ------------------------------ Ruido de valor --------------------------- */
function noiseGrid(w, h) {
  const g = new Float32Array(w * h);
  for (let i = 0; i < g.length; i++) g[i] = RNG();
  return { w, h, g };
}
function sampleGrid(n, x, y) {
  const gx = x * (n.w - 1), gy = y * (n.h - 1);
  const x0 = Math.floor(gx), y0 = Math.floor(gy);
  const x1 = Math.min(x0 + 1, n.w - 1), y1 = Math.min(y0 + 1, n.h - 1);
  let tx = gx - x0, ty = gy - y0;
  tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
  const a = lerp(n.g[y0 * n.w + x0], n.g[y0 * n.w + x1], tx);
  const b = lerp(n.g[y1 * n.w + x0], n.g[y1 * n.w + x1], tx);
  return lerp(a, b, ty);
}
function fbm(layers, x, y) {
  let v = 0, amp = 1, tot = 0;
  for (const l of layers) { v += sampleGrid(l, x, y) * amp; tot += amp; amp *= 0.5; }
  return v / tot;
}
function makeFbm(base, octaves) {
  const layers = [];
  for (let i = 0; i < octaves; i++) layers.push(noiseGrid(base << i, Math.max(2, (base << i) >> 1)));
  return layers;
}

/* ------------------------------- El mundo -------------------------------- */
class World {
  constructor(seed) {
    this.seed = seed;
    setSeed(seed);
    this.w = MAP_W; this.h = MAP_H;
    this.elev = new Float32Array(MAP_W * MAP_H);
    this.moist = new Float32Array(MAP_W * MAP_H);
    this.temp = new Float32Array(MAP_W * MAP_H);
    this.biome = new Uint8Array(MAP_W * MAP_H);
    this.land = new Uint8Array(MAP_W * MAP_H);
    this.comp = new Int16Array(MAP_W * MAP_H).fill(-1);
    this.known = new Uint8Array(MAP_W * MAP_H);
    this.biomeKeys = Object.keys(BIOMES);
    this.generate();
  }
  idx(x, y) { return y * this.w + x; }
  biomeAt(x, y) { return this.biomeKeys[this.biome[this.idx(x, y)]]; }
  inBounds(x, y) { return x >= 0 && y >= 0 && x < this.w && y < this.h; }

  generate() {
    const eL = makeFbm(4, 5), mL = makeFbm(3, 4), tL = makeFbm(2, 3);
    // continentes: varios centros de masa
    const centers = [];
    const nC = rint(4, 6);
    for (let i = 0; i < nC; i++) centers.push({ x: rrange(0.12, 0.88), y: rrange(0.15, 0.85), r: rrange(0.20, 0.36) });

    for (let y = 0; y < this.h; y++) {
      for (let x = 0; x < this.w; x++) {
        const u = x / this.w, v = y / this.h;
        let mass = 0;
        for (const c of centers) {
          const d = Math.hypot((u - c.x) * 1.35, v - c.y);
          mass = Math.max(mass, clamp(1 - d / c.r, 0, 1));
        }
        // bordes del mapa siempre océano
        const edge = Math.min(u, v, 1 - u, 1 - v);
        const edgeFall = clamp(edge / 0.07, 0, 1);
        let e = fbm(eL, u, v) * 0.62 + mass * 0.72 - 0.34;
        e *= edgeFall;
        const i = this.idx(x, y);
        this.elev[i] = e;
        this.moist[i] = fbm(mL, u + 0.31, v - 0.17);
        // temperatura: latitud + altitud
        const lat = Math.abs(v - 0.5) * 2;
        this.temp[i] = clamp(1.08 - lat * 1.25 + fbm(tL, u * 0.7, v * 0.7) * 0.28 - Math.max(0, e - 0.34) * 1.1, 0, 1);
      }
    }
    // clasificar biomas
    const bk = this.biomeKeys, bi = k => bk.indexOf(k);
    for (let i = 0; i < this.elev.length; i++) {
      const e = this.elev[i], m = this.moist[i], t = this.temp[i];
      let b;
      if (e < -0.02) b = 'ocean';
      else if (e < 0.015) b = 'shallow';
      else if (e < 0.045) b = 'beach';
      else if (e > 0.46) b = 'peak';
      else if (e > 0.34) b = 'mountain';
      else if (e > 0.24) b = 'hills';
      else if (t < 0.16) b = 'snow';
      else if (t < 0.30) b = 'tundra';
      else if (m < 0.34 && t > 0.62) b = 'desert';
      else if (m < 0.44) b = 'savanna';
      else if (m > 0.66 && t > 0.68) b = 'jungle';
      else if (m > 0.54) b = 'forest';
      else b = 'plains';
      this.biome[i] = bi(b);
      this.land[i] = BIOMES[b].land ? 1 : 0;
    }
    this.labelComponents();
    this.placeCities();
    this.balanceWorld();
    this.buildGraph();
    this.placeSites();
  }

  /* --- componentes conexas de tierra (para saber qué se alcanza a pie) --- */
  labelComponents() {
    let id = 0;
    const stack = [];
    for (let y = 0; y < this.h; y++) for (let x = 0; x < this.w; x++) {
      const i = this.idx(x, y);
      if (!this.land[i] || this.comp[i] !== -1) continue;
      stack.push(i); this.comp[i] = id;
      while (stack.length) {
        const k = stack.pop(), kx = k % this.w, ky = (k / this.w) | 0;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const nx = kx + dx, ny = ky + dy;
          if (!this.inBounds(nx, ny)) continue;
          const ni = this.idx(nx, ny);
          if (this.land[ni] && this.comp[ni] === -1) { this.comp[ni] = id; stack.push(ni); }
        }
      }
      id++;
    }
    this.nComp = id;
    this.compSize = new Int32Array(id);
    for (let i = 0; i < this.comp.length; i++) if (this.comp[i] >= 0) this.compSize[this.comp[i]]++;
  }

  /** Biomas del entorno: lo que la ciudad tiene a mano, no solo bajo sus pies. */
  nearBiomes(x, y, r) {
    const set = new Set();
    for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
      const nx = x + dx, ny = y + dy;
      if (this.inBounds(nx, ny)) set.add(this.biomeAt(nx, ny));
    }
    return set;
  }

  isCoastal(x, y) {
    for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
      const nx = x + dx, ny = y + dy;
      if (this.inBounds(nx, ny) && !this.land[this.idx(nx, ny)]) return true;
    }
    return false;
  }

  /* ------------------------------ Ciudades ------------------------------- */
  placeCities() {
    const used = new Set();
    const cands = [];
    for (let y = 3; y < this.h - 3; y++) for (let x = 3; x < this.w - 3; x++) {
      const i = this.idx(x, y);
      if (!this.land[i]) continue;
      if (this.compSize[this.comp[i]] < 60) continue;
      const b = this.biomeAt(x, y);
      if (b === 'peak') continue;
      let score = 1;
      if (this.isCoastal(x, y)) score += 3.2;
      if (b === 'plains') score += 2.2;
      if (b === 'forest' || b === 'savanna') score += 1.2;
      if (b === 'hills') score += 1.0;
      if (b === 'mountain') score += 0.3;
      if (b === 'desert' || b === 'snow') score -= 0.6;
      score += this.moist[i] * 0.8 + RNG() * 1.4;
      if (score > 2.4) cands.push({ x, y, score });
    }
    shuffle(cands);
    cands.sort((a, b) => b.score - a.score);

    const target = 38, minD = 11;
    this.cities = [];
    for (const c of cands) {
      if (this.cities.length >= target) break;
      let ok = true;
      for (const o of this.cities) if (dist(c.x, c.y, o.x, o.y) < minD) { ok = false; break; }
      if (!ok) continue;
      this.cities.push(this.makeCity(c.x, c.y, used));
    }
    this.cities.forEach((c, i) => c.id = i);
  }

  makeCity(x, y, used) {
    const i = this.idx(x, y);
    const b = this.biomeAt(x, y);
    const coastal = this.isCoastal(x, y);
    const pop = Math.round(rrange(1.2, 9) * (coastal ? 1.5 : 1) * (b === 'plains' ? 1.35 : 1) * 1000);
    const c = {
      name: genCityName(used), x, y, biome: b, coastal,
      around: this.nearBiomes(x, y, 6),   // qué hay en sus alrededores
      pop, popTarget: pop, wealth: rrange(0.75, 1.35),
      comp: this.comp[i],
      specialties: [], stock: {}, prod: {}, cons: {}, price: {}, lastPrice: {},
      events: [], known: false, visited: false,
      tax: rrange(0.02, 0.09), unrest: rrange(0, 0.15), tension: 0,
      contracts: [], rumors: [],
      priceHist: {},
      banned: {},           // bienes prohibidos (contrabando)
      playerRep: 0,
      buildings: [],        // fábricas del jugador
      warehouse: null,      // almacén del jugador { cap, stock:{} }
      shipyard: coastal && rnd() < 0.55,
      bank: false,
      demandMod: {},        // modificadores temporales de demanda
      prodMod: {},
    };
    // especialidades
    const pool = SPECIALTIES.filter(s => (!s.coastal || coastal));
    shuffle(pool);
    const n = pickW([[1, 5], [2, 4], [3, 1]]);
    for (const s of pool) {
      if (c.specialties.length >= n) break;
      // coherencia con el bioma
      let w = 1;
      if (s.id === 'minera' && !(b === 'mountain' || b === 'hills')) w = 0.15;
      if (s.id === 'gemas' && !(b === 'mountain' || b === 'peak' || b === 'hills')) w = 0.08;
      if (s.id === 'granero' && !(b === 'plains' || b === 'savanna')) w = 0.2;
      if (s.id === 'maderera' && !(b === 'forest' || b === 'jungle')) w = 0.2;
      if (s.id === 'vinicola' && !(b === 'plains' || b === 'savanna')) w = 0.15;
      if (s.id === 'especiera' && !(b === 'jungle' || b === 'desert' || b === 'savanna')) w = 0.12;
      if (s.id === 'ganadera' && !(b === 'plains' || b === 'savanna' || b === 'tundra')) w = 0.25;
      if (rnd() < w) c.specialties.push(s.id);
    }
    if (!c.specialties.length) c.specialties.push(coastal ? 'puertoPesq' : 'granero');
    c.bank = c.specialties.includes('banca') || rnd() < 0.18;
    if (c.specialties.includes('astillero')) c.shipyard = true;

    // --- carácter: lo que define a la ciudad de un vistazo
    const opts = CITY_TRAITS.filter(t => !t.need || t.need(c));
    const trait = pickW(opts.map(t => [t, t.w]));
    c.trait = trait.id;
    if (trait.taxAdd) c.tax = clamp(c.tax + trait.taxAdd, 0.005, 0.3);
    if (trait.wealth) c.wealth = clamp(c.wealth + trait.wealth, 0.4, 3);
    if (trait.shipyard && coastal) c.shipyard = true;
    if (trait.bank) c.bank = true;
    c.baseTax = c.tax;

    // bienes prohibidos: la base del contrabando
    const contrabandPool = ['vino', 'espadas', 'armadura', 'especias', 'joyas', 'medicina', 'gemas'];
    const nBan = pickW([[0, 6], [1, 3], [2, 1]]);
    shuffle(contrabandPool);
    for (let k = 0; k < nBan; k++) c.banned[contrabandPool[k]] = true;
    for (const b of trait.ban || []) c.banned[b] = true;      // prohibiciones propias del carácter

    this.initEconomy(c);
    return c;
  }

  initEconomy(c) {
    const kpop = c.pop / 1000;
    const prod = {};
    const bp = BIOME_PROD[c.biome] || {};
    for (const g in bp) prod[g] = (prod[g] || 0) + bp[g] * kpop * 0.55;
    if (c.coastal) { prod.pescado = (prod.pescado || 0) + 1.5 * kpop * 0.55; prod.sal = (prod.sal || 0) + 0.5 * kpop * 0.4; }
    for (const s of c.specialties) {
      const sp = SPECIALTY[s];
      for (const g in sp.prod) prod[g] = (prod[g] || 0) + sp.prod[g] * kpop * 0.7;
    }
    // pequeñas industrias urbanas: toda ciudad fabrica algo, en distinta medida
    const urban = {
      harina: 0.50, pan: 0.62, tablones: 0.34, tela: 0.22, cuero: 0.16, herram: 0.13, hierro: 0.16,
      muebles: 0.09, espadas: 0.055, armadura: 0.035, ropa: 0.10, vino: 0.08, medicina: 0.05,
      joyas: 0.022, sal: 0.10, piedra: 0.18, madera: 0.25, grano: 0.35,
    };
    for (const g in urban) {
      const flavor = 0.35 + RNG() * 1.6;                       // perfil industrial de la ciudad
      prod[g] = (prod[g] || 0) + urban[g] * kpop * 0.5 * c.wealth * flavor;
    }

    const cons = {};
    for (const g in BASE_CONSUME) {
      const good = GOOD[g];
      let m = 1;
      if (good.tag === 'lujo') m = c.wealth * c.wealth;
      if (good.tag === 'arma') m = 0.6;
      cons[g] = BASE_CONSUME[g] * kpop * 0.55 * m;
    }
    // el carácter de la ciudad inclina lo que produce y lo que reclama
    const trait = CITY_TRAIT[c.trait];
    if (trait) {
      for (const g in trait.prod || {}) prod[g] = (prod[g] || 0) * 1 + (prod[g] || kpop * 0.3) * (trait.prod[g] - 1);
      for (const g in trait.dem || {}) {
        if (g.startsWith('@')) {
          const tag = g.slice(1);
          for (const gg of GOOD_IDS) if (GOOD[gg].tag === tag) cons[gg] *= trait.dem[g];
        } else cons[g] = (cons[g] || 0) * trait.dem[g];
      }
    }
    c.prod = prod; c.cons = cons;
    for (const g of GOOD_IDS) {
      c.price[g] = GOOD[g].base;
      c.lastPrice[g] = GOOD[g].base;
      c.priceHist[g] = [];
    }
  }

  /** El mundo debe poder alimentarse: producción global ≈ consumo global. */
  balanceWorld() {
    const P = {}, C = {};
    for (const c of this.cities) {
      for (const g of GOOD_IDS) {
        P[g] = (P[g] || 0) + (c.prod[g] || 0);
        C[g] = (C[g] || 0) + (c.cons[g] || 0);
      }
    }
    for (const g of GOOD_IDS) {
      const target = C[g] * 1.26;
      if (P[g] < 1e-6) {           // nadie lo produce: reparte entre unas pocas ciudades
        const picks = shuffle(this.cities.slice()).slice(0, 4);
        for (const c of picks) c.prod[g] = target / picks.length;
        continue;
      }
      const f = clamp(target / P[g], 0.25, 12);
      for (const c of this.cities) if (c.prod[g]) c.prod[g] *= f;
    }
    // existencias iniciales coherentes con el nuevo equilibrio
    for (const c of this.cities) {
      for (const g of GOOD_IDS) {
        const net = (c.prod[g] || 0) - (c.cons[g] || 0);
        const target = Math.max(8, (c.cons[g] || 0) * 20 + (c.prod[g] || 0) * 8);
        c.stock[g] = Math.round(target * rrange(0.65, 1.5) + (net > 0 ? net * 14 : 0));
      }
      c.basePop = c.pop;
      c.baseProd = Object.assign({}, c.prod);
      c.baseCons = Object.assign({}, c.cons);
    }
  }

  /* -------------------------- Grafo de rutas ------------------------------ */
  terrainCost(x1, y1, x2, y2) {
    const steps = Math.max(2, Math.ceil(dist(x1, y1, x2, y2)));
    let sum = 0;
    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const x = Math.round(lerp(x1, x2, t)), y = Math.round(lerp(y1, y2, t));
      if (!this.inBounds(x, y)) { sum += 3; continue; }
      sum += BIOMES[this.biomeAt(x, y)].cost;
    }
    return sum / (steps + 1);
  }
  landPathBlocked(x1, y1, x2, y2) {
    const steps = Math.max(2, Math.ceil(dist(x1, y1, x2, y2)));
    let water = 0;
    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const x = Math.round(lerp(x1, x2, t)), y = Math.round(lerp(y1, y2, t));
      if (this.inBounds(x, y) && !this.land[this.idx(x, y)]) water++;
    }
    return water / (steps + 1) > 0.12;
  }

  buildGraph() {
    const C = this.cities;
    this.edges = [];
    const key = (a, b) => a < b ? a + '_' + b : b + '_' + a;
    const seen = new Set();
    const addEdge = (a, b, type) => {
      const k = key(a, b) + type;
      if (seen.has(k)) return; seen.add(k);
      const A = C[a], B = C[b];
      const d = dist(A.x, A.y, B.x, B.y);
      const tc = type === 'land' ? this.terrainCost(A.x, A.y, B.x, B.y) : 1.0;
      this.edges.push({
        a, b, type, dist: d,
        days: d * tc / TILES_PER_DAY,
        risk: clamp(0.02 + d / 420 + (type === 'sea' ? 0.03 : 0.02) * rnd(), 0.01, 0.30),
        blocked: 0, danger: 0, toll: 0,
      });
    };

    for (let i = 0; i < C.length; i++) {
      // vecinos terrestres del mismo continente
      const land = C.map((o, j) => ({ j, d: dist(C[i].x, C[i].y, o.x, o.y) }))
        .filter(o => o.j !== i && C[o.j].comp === C[i].comp)
        .sort((a, b) => a.d - b.d).slice(0, 6);
      let added = 0;
      for (const o of land) {
        if (added >= 4) break;
        if (this.landPathBlocked(C[i].x, C[i].y, C[o.j].x, C[o.j].y)) continue;
        addEdge(i, o.j, 'land'); added++;
      }
      // rutas marítimas entre puertos
      if (C[i].coastal) {
        const sea = C.map((o, j) => ({ j, d: dist(C[i].x, C[i].y, o.x, o.y) }))
          .filter(o => o.j !== i && C[o.j].coastal)
          .sort((a, b) => a.d - b.d).slice(0, 5);
        let s = 0;
        for (const o of sea) { if (s >= 3) break; addEdge(i, o.j, 'sea'); s++; }
      }
    }
    // asegurar conectividad global de puertos: unir componentes por mar
    this.adj = C.map(() => []);
    this.edges.forEach((e, i) => { this.adj[e.a].push(i); this.adj[e.b].push(i); });
    this.connectIslands();

    // el carácter de la ciudad tiñe sus caminos: piratas frente a las villas
    // pesqueras, bandidos alrededor de las plazas fronterizas
    for (const c of C) {
      const t = CITY_TRAIT[c.trait];
      if (!t) continue;
      for (const ei of this.adj[c.id]) {
        const e = this.edges[ei];
        if (e.type === 'sea' && t.seaDanger) e.danger += t.seaDanger;
        if (e.type === 'land' && t.landDanger) e.danger += t.landDanger;
      }
    }
  }

  connectIslands() {
    // une por mar los grupos desconectados usando los puertos más cercanos
    const C = this.cities;
    const seen = new Array(C.length).fill(-1);
    let group = 0;
    for (let i = 0; i < C.length; i++) {
      if (seen[i] >= 0) continue;
      const q = [i]; seen[i] = group;
      while (q.length) {
        const k = q.pop();
        for (const ei of this.adj[k]) {
          const e = this.edges[ei], o = e.a === k ? e.b : e.a;
          if (seen[o] < 0) { seen[o] = group; q.push(o); }
        }
      }
      group++;
    }
    if (group <= 1) return;
    for (let g = 1; g < group; g++) {
      const A = [], B = [];
      for (let i = 0; i < C.length; i++) (seen[i] === g ? A : B).push(i);
      let best = null;
      for (const a of A) for (const b of B) {
        const d = dist(C[a].x, C[a].y, C[b].x, C[b].y);
        if (!best || d < best.d) best = { a, b, d };
      }
      if (!best) continue;
      C[best.a].coastal = true; C[best.b].coastal = true;
      const e = {
        a: best.a, b: best.b, type: 'sea', dist: best.d,
        days: best.d / TILES_PER_DAY, risk: 0.08, blocked: 0, danger: 0, toll: 0,
      };
      this.edges.push(e);
      const ei = this.edges.length - 1;
      this.adj[best.a].push(ei); this.adj[best.b].push(ei);
      for (let i = 0; i < C.length; i++) if (seen[i] === g) seen[i] = 0;
    }
  }

  /* ------------------------ Lugares por descubrir ------------------------- */
  placeSites() {
    this.sites = [];
    const n = rint(16, 24);
    let guard = 0;
    while (this.sites.length < n && guard++ < 900) {
      const x = rint(4, this.w - 5), y = rint(4, this.h - 5);
      const i = this.idx(x, y);
      const land = !!this.land[i];
      const coastal = land && this.isCoastal(x, y);
      // lejos de las ciudades: hay que salir a buscarlos
      if (this.cities.some(c => dist(c.x, c.y, x, y) < 9)) continue;
      if (this.sites.some(s => dist(s.x, s.y, x, y) < 12)) continue;
      const opts = SITES.filter(s => (s.coastal ? coastal : (s.land ? land : true)));
      if (!opts.length) continue;
      const def = pickW(opts.map(s => [s, s.w]));
      this.sites.push({ id: this.sites.length, type: def.id, x, y, found: false, claimed: false });
    }
  }

  /* ----------------------------- Niebla de guerra ------------------------- */
  reveal(x, y, r) {
    const r2 = r * r;
    let found = [];
    for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
      if (dx * dx + dy * dy > r2) continue;
      const nx = Math.round(x + dx), ny = Math.round(y + dy);
      if (!this.inBounds(nx, ny)) continue;
      this.known[this.idx(nx, ny)] = 1;
    }
    for (const c of this.cities) {
      if (!c.known && dist(c.x, c.y, x, y) <= r + 1.5) { c.known = true; found.push(c); }
    }
    for (const s of this.sites || []) {
      if (!s.found && dist(s.x, s.y, x, y) <= r) { s.found = true; s.isSite = true; found.push(s); }
    }
    return found;
  }
  revealPath(x1, y1, x2, y2, r) {
    const steps = Math.ceil(dist(x1, y1, x2, y2));
    let found = [];
    for (let s = 0; s <= steps; s += 2) {
      const t = s / steps;
      found = found.concat(this.reveal(Math.round(lerp(x1, x2, t)), Math.round(lerp(y1, y2, t)), r));
    }
    return found;
  }

  /* --------------------------- Rutas (Dijkstra) --------------------------- */
  /** Devuelve {days, path:[cityIdx], edges:[edgeIdx]} o null. opts: {seaCap, landCap, seaSpeed, landSpeed, avoidRisk} */
  route(from, to, opts) {
    const n = this.cities.length;
    const D = new Float64Array(n).fill(Infinity);
    const prev = new Int32Array(n).fill(-1), prevE = new Int32Array(n).fill(-1);
    const vis = new Uint8Array(n);
    D[from] = 0;
    for (let it = 0; it < n; it++) {
      let u = -1, best = Infinity;
      for (let i = 0; i < n; i++) if (!vis[i] && D[i] < best) { best = D[i]; u = i; }
      if (u < 0) break;
      vis[u] = 1;
      if (u === to) break;
      for (const ei of this.adj[u]) {
        const e = this.edges[ei];
        if (e.blocked > 0) continue;
        if (e.type === 'sea' && !opts.canSea) continue;
        const speed = e.type === 'sea' ? opts.seaSpeed : opts.landSpeed;
        let cost = e.days / Math.max(0.3, speed);
        if (opts.avoidRisk) cost *= (1 + (e.risk + e.danger) * 3);
        const v = e.a === u ? e.b : e.a;
        if (D[u] + cost < D[v]) { D[v] = D[u] + cost; prev[v] = u; prevE[v] = ei; }
      }
    }
    if (!isFinite(D[to])) return null;
    const path = [to], edges = [];
    let cur = to;
    while (prev[cur] >= 0) { edges.unshift(prevE[cur]); cur = prev[cur]; path.unshift(cur); }
    let days = 0, risk = 0;
    for (const ei of edges) {
      const e = this.edges[ei];
      const speed = e.type === 'sea' ? opts.seaSpeed : opts.landSpeed;
      days += e.days / Math.max(0.3, speed);
      risk = 1 - (1 - risk) * (1 - (e.risk + e.danger));
    }
    return { days, path, edges, risk };
  }
}
