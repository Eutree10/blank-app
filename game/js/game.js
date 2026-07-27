/* =========================================================================
   Merchant's Odyssey — estado del juego, jugador y acciones
   ========================================================================= */
'use strict';

const SAVE_KEY = 'merchants_odyssey_save_v1';

class Game {
  constructor(seed) {
    this.seed = seed >>> 0;
    this.world = new World(this.seed);
    this.economy = new Economy(this.world, this);
    this.ai = new AIWorld(this.world, this, 64);
    this.day = 0;
    this.newsLog = [];
    this.stats = { bought: 0, sold: 0, profit: 0, km: 0, days: 0, caught: 0, raids: 0 };

    // --- jugador
    const start = this.pickStartCity();
    this.p = {
      at: start.id,
      gold: 100,
      cargo: {},
      vehicles: { mochila: 1 },
      guards: 0,
      rep: 0,            // reputación honesta
      noto: 0,           // notoriedad (contrabando / piratería)
      loans: [],
      contracts: [],
      buildings: [],     // {city, recipe, level}
      warehouses: {},    // cityId -> {cap, stock:{}}
      insured: false,
      era: 0,
    };
    start.visited = true; start.known = true;
    this.world.reveal(start.x, start.y, 21);
    this.news(`Empiezas en ${start.name} con 100 monedas y una mochila.`, 'you', start.id, '🎒');
    for (const c of this.world.cities) this.economy.refreshContracts(c, 0);
    this.recomputeEra();
  }

  pickStartCity() {
    const cs = this.world.cities.slice().sort((a, b) => b.pop - a.pop);
    const mid = cs.filter(c => c.pop > 3000 && c.coastal);
    return (mid.length ? mid[Math.floor(mid.length / 2)] : cs[0]);
  }

  /* ------------------------------- Consultas ----------------------------- */
  get city() { return this.world.cities[this.p.at]; }

  cargoWeight(cargo) {
    cargo = cargo || this.p.cargo;
    let s = 0; for (const g in cargo) s += cargo[g] * GOOD[g].w;
    return s;
  }
  capacity(terrain) {
    let cap = 0;
    for (const v in this.p.vehicles) {
      const V = VEHICLE[v];
      if (V.terrain === terrain) cap += V.cap * this.p.vehicles[v];
    }
    return cap;
  }
  speed(terrain) {
    let cap = 0, sp = 0;
    for (const v in this.p.vehicles) {
      const V = VEHICLE[v];
      if (V.terrain !== terrain) continue;
      const n = this.p.vehicles[v];
      cap += V.cap * n; sp += V.speed * V.cap * n;
    }
    return cap > 0 ? sp / cap : 1;
  }
  canSea() { return this.capacity('sea') > 0; }
  upkeep() {
    let u = 0;
    for (const v in this.p.vehicles) u += VEHICLE[v].up * this.p.vehicles[v];
    u += this.p.guards * 2.5;
    for (const b of this.p.buildings) u += 10 * b.level;
    return u;
  }
  debt() { let d = 0; for (const l of this.p.loans) d += l.amount; return d; }

  netWorth() {
    const c = this.city;
    let v = this.p.gold;
    for (const g in this.p.cargo) v += this.p.cargo[g] * (c.price[g] || GOOD[g].base);
    for (const vh in this.p.vehicles) v += VEHICLE[vh].cost * this.p.vehicles[vh] * 0.6;
    for (const b of this.p.buildings) v += RECIPE[b.recipe].cost * b.level * 0.7;
    for (const cid in this.p.warehouses) {
      const w = this.p.warehouses[cid], city = this.world.cities[cid];
      v += 1500;
      for (const g in w.stock) v += w.stock[g] * (city.price[g] || GOOD[g].base);
    }
    return v - this.debt();
  }
  title() { return titleFor(this.netWorth()); }

  routeOpts(avoidRisk) {
    return {
      canSea: this.canSea(),
      landSpeed: this.speed('land'),
      seaSpeed: this.speed('sea'),
      avoidRisk: !!avoidRisk,
    };
  }
  routeTo(cid) { return this.world.route(this.p.at, cid, this.routeOpts(true)); }

  /* ------------------------------ Tiempo --------------------------------- */
  advanceDays(n, ctx) {
    const report = { news: [], caught: false, ambush: null, days: n };
    const titleBefore = this.title();
    for (let i = 0; i < n; i++) {
      this.day++;
      this.stats.days++;
      this.economy.tick(this.day);
      this.ai.tick(this.day);
      this.tickPlayer();
    }
    this.recomputeEra();
    this.checkContracts();
    const t = this.title();
    if (t !== titleBefore) {
      this.news(`Ahora te llaman «${t}».`, 'good', null, '👑');
      report.newTitle = t;
    }
    return report;
  }

  tickPlayer() {
    // mantenimiento
    const up = this.upkeep();
    this.p.gold -= up;
    // intereses
    for (const l of this.p.loans) l.amount *= (1 + l.rate);
    // fábricas
    this.runFactories();
    // caducidad de la carga
    for (const g in this.p.cargo) {
      if (GOOD[g].perish) {
        this.p.cargo[g] *= 0.985;
        if (this.p.cargo[g] < 0.5) delete this.p.cargo[g];
      }
    }
    if (this.p.gold < 0) {
      // el banco embarga: préstamo forzoso
      const need = -this.p.gold + 200;
      this.p.gold += need;
      this.p.loans.push({ amount: need * 1.1, rate: 0.0013, from: 'embargo', day: this.day });
      this.news(`Sin liquidez: el banco te adelanta ${fmt(need)} ⦿ con un interés abusivo.`, 'bad', null, '🏦');
    }
    this.p.noto = Math.max(0, this.p.noto - 0.004);
  }

  runFactories() {
    for (const b of this.p.buildings) {
      const c = this.world.cities[b.city], r = RECIPE[b.recipe];
      const runs = b.level * FACTORY_BATCH;
      let ok = true, cost = 0;
      for (const g in r.in) {
        const need = r.in[g] * runs;
        if ((c.stock[g] || 0) < need + 5) { ok = false; break; }
        cost += costToBuy(c, g, need);
      }
      if (!ok || cost > this.p.gold) { b.idle = true; b.why = 'sin insumos u oro'; continue; }
      // no producir a pérdidas
      let est = 0;
      for (const g in r.out) est += revenueToSell(c, g, r.out[g] * runs) * 0.97;
      if (est <= cost) { b.idle = true; b.why = 'margen negativo'; b.profit = (b.profit || 0) * 0.9; continue; }
      b.idle = false; b.why = '';
      for (const g in r.in) c.stock[g] -= r.in[g] * runs;
      this.p.gold -= cost;
      let rev = 0;
      for (const g in r.out) {
        const n = r.out[g] * runs;
        rev += revenueToSell(c, g, n) * 0.97;
        c.stock[g] += n;
      }
      this.p.gold += rev;
      b.profit = (b.profit || 0) * 0.9 + (rev - cost) * 0.1;
      this.stats.profit += rev - cost;
    }
  }

  recomputeEra() {
    const nw = this.netWorth();
    let era = 0;
    if (this.day > 300 && nw > 80000) era = 1;
    if (this.day > 900 && nw > 700000) era = 2;
    if (era > this.p.era) {
      this.p.era = era;
      this.news(era === 1
        ? 'La era industrial comienza: llegan el vapor y el ferrocarril.'
        : 'Era moderna: motores, camiones y aviones de carga.', 'good', null, era === 1 ? '🚂' : '✈️');
    }
  }

  /* ------------------------------- Viajar -------------------------------- */
  travelTo(cid, opts) {
    opts = opts || {};
    const route = this.world.route(this.p.at, cid, this.routeOpts(!opts.fast));
    if (!route) return { err: 'No hay ruta disponible.' };
    // capacidad por tipo de tramo
    const w = this.cargoWeight();
    const usesSea = route.edges.some(ei => this.world.edges[ei].type === 'sea');
    const usesLand = route.edges.some(ei => this.world.edges[ei].type === 'land');
    if (usesSea && w > this.capacity('sea')) return { err: 'La flota naval no puede cargar todo tu inventario.' };
    if (usesLand && w > this.capacity('land')) return { err: 'Tu caravana terrestre no puede con tanta carga.' };

    const days = Math.max(1, Math.round(route.days));
    const log = [];
    let lostAll = false;
    // peajes
    let toll = 0;
    for (const ei of route.edges) toll += this.world.edges[ei].toll || 0;
    if (toll) { this.p.gold -= toll; log.push(`Peajes pagados: ${fmt(toll)} ⦿`); }

    // sucesos por tramo
    for (const ei of route.edges) {
      const e = this.world.edges[ei];
      const guardFactor = 1 / (1 + this.p.guards * 0.14);
      const chance = (e.risk + e.danger) * guardFactor * (this.p.noto > 0.5 ? 1.3 : 1);
      if (rnd() < chance) {
        const A = this.world.cities[e.a], B = this.world.cities[e.b];
        const who = e.type === 'sea' ? 'Piratas' : 'Bandidos';
        if (this.p.guards > 0 && rnd() < this.p.guards * 0.11) {
          const lost = Math.min(this.p.guards, rint(1, 2));
          this.p.guards -= lost;
          log.push(`⚔️ ${who} atacan entre ${A.name} y ${B.name}: tu escolta los repele (pierdes ${lost} guardia${lost > 1 ? 's' : ''}).`);
        } else {
          const gs = Object.keys(this.p.cargo);
          if (gs.length) {
            const g = pick(gs);
            const lost = Math.ceil(this.p.cargo[g] * rrange(0.35, 0.9));
            this.p.cargo[g] -= lost;
            if (this.p.cargo[g] <= 0.4) delete this.p.cargo[g];
            log.push(`🏴‍☠️ ${who} te asaltan cerca de ${B.name}: pierdes ${lost} ${GOOD[g].name}.`);
            if (this.p.insured) {
              const comp = Math.round(lost * GOOD[g].base * 0.6);
              this.p.gold += comp;
              log.push(`El seguro cubre ${fmt(comp)} ⦿.`);
            }
          } else {
            const g2 = Math.round(this.p.gold * 0.15);
            this.p.gold -= g2;
            log.push(`🏴‍☠️ ${who} te roban ${fmt(g2)} ⦿ en el camino.`);
          }
        }
      }
    }

    // revelar mapa por el camino
    let discovered = [];
    for (let i = 0; i < route.path.length - 1; i++) {
      const A = this.world.cities[route.path[i]], B = this.world.cities[route.path[i + 1]];
      discovered = discovered.concat(this.world.revealPath(A.x, A.y, B.x, B.y, 7));
    }
    this.stats.km += Math.round(route.edges.reduce((s, ei) => s + this.world.edges[ei].dist, 0));

    this.advanceDays(days);
    this.p.at = cid;
    const c = this.city;
    c.visited = true; c.known = true;
    discovered = [...new Set(discovered.concat(this.world.reveal(c.x, c.y, 12)))];
    for (const d of discovered) this.news(`Descubres ${d.name} (${BIOMES[d.biome].name.toLowerCase()}).`, 'good', d.id, '🧭');

    return { ok: true, days, log, route, discovered };
  }

  /* ------------------------------ Comercio -------------------------------- */
  maxBuy(g) {
    const c = this.city;
    const w = this.cargoWeight();
    const capL = this.capacity('land'), capS = this.canSea() ? this.capacity('sea') : Infinity;
    const cap = Math.max(capL, this.capacity('sea'));
    const space = Math.floor((cap - w) / GOOD[g].w);
    let n = Math.min(space, Math.floor(c.stock[g]));
    // búsqueda por presupuesto
    let lo = 0, hi = Math.max(0, n);
    while (lo < hi) {
      const mid = Math.ceil((lo + hi) / 2);
      if (costToBuy(c, g, mid) <= this.p.gold) lo = mid; else hi = mid - 1;
    }
    return Math.max(0, lo);
  }

  buy(g, n) {
    const c = this.city;
    n = Math.floor(n);
    if (n <= 0) return { err: 'Cantidad inválida.' };
    if (c.banned[g]) return { err: `${GOOD[g].name} está prohibido en ${c.name}: aquí solo se vende, y a escondidas.` };
    if (c.stock[g] < n) return { err: 'No hay tanto stock.' };
    const cost = costToBuy(c, g, n);
    if (cost > this.p.gold) return { err: 'No tienes suficiente oro.' };
    const cap = Math.max(this.capacity('land'), this.capacity('sea'));
    if (this.cargoWeight() + n * GOOD[g].w > cap + 0.001) return { err: 'No tienes espacio de carga.' };
    this.p.gold -= cost;
    c.stock[g] -= n;
    this.p.cargo[g] = (this.p.cargo[g] || 0) + n;
    this.stats.bought += n;
    if (!this.p.avgCost) this.p.avgCost = {};
    const prev = this.p.avgCost[g] || { n: 0, total: 0 };
    this.p.avgCost[g] = { n: prev.n + n, total: prev.total + cost };
    return { ok: true, cost, unit: cost / n };
  }

  sell(g, n, black) {
    const c = this.city;
    n = Math.min(Math.floor(n), Math.floor(this.p.cargo[g] || 0));
    if (n <= 0) return { err: 'No tienes ese bien.' };
    let rev = revenueToSell(c, g, n);
    let caught = false, note = '';
    if (c.banned[g]) {
      rev *= 1.85;
      const risk = clamp(0.16 + this.p.noto * 0.1 - this.p.rep * 0.004, 0.05, 0.5);
      if (rnd() < risk) {
        caught = true;
        const fine = Math.round(rev * 0.9);
        this.p.gold -= fine;
        this.p.cargo[g] -= n;
        if (this.p.cargo[g] <= 0) delete this.p.cargo[g];
        this.p.noto += 0.25; this.p.rep -= 6;
        c.playerRep -= 8;
        this.stats.caught++;
        return { ok: true, caught: true, fine, msg: `¡Te pillan! La guardia de ${c.name} confisca la mercancía y te multa con ${fmt(fine)} ⦿.` };
      }
      this.p.noto += 0.08;
      note = 'Mercado negro: +85% sobre el precio oficial.';
    } else {
      rev *= (1 - c.tax);
      this.p.rep += n * GOOD[g].base / 4000;
      c.playerRep += 0.2;
    }
    this.p.gold += rev;
    c.stock[g] += n;
    this.p.cargo[g] -= n;
    if (this.p.cargo[g] <= 0.0001) delete this.p.cargo[g];
    this.stats.sold += n;
    // beneficio estimado
    if (this.p.avgCost && this.p.avgCost[g] && this.p.avgCost[g].n > 0) {
      const unitCost = this.p.avgCost[g].total / this.p.avgCost[g].n;
      this.stats.profit += rev - unitCost * n;
      this.p.avgCost[g].n -= n; this.p.avgCost[g].total -= unitCost * n;
      if (this.p.avgCost[g].n <= 0) delete this.p.avgCost[g];
    } else this.stats.profit += rev * 0.3;
    return { ok: true, rev, unit: rev / n, note, caught };
  }

  /* ------------------------------ Servicios ------------------------------- */
  buyVehicle(vid) {
    const V = VEHICLE[vid], c = this.city;
    if (V.era > this.p.era) return { err: 'Esa tecnología aún no existe.' };
    if (V.terrain === 'sea' && !c.shipyard) return { err: 'Aquí no hay astillero.' };
    const price = Math.round(V.cost * (1 + c.tax));
    if (this.p.gold < price) return { err: 'No tienes suficiente oro.' };
    this.p.gold -= price;
    this.p.vehicles[vid] = (this.p.vehicles[vid] || 0) + 1;
    return { ok: true, msg: `Compras ${V.name} por ${fmt(price)} ⦿.` };
  }
  sellVehicle(vid) {
    if (!this.p.vehicles[vid]) return { err: 'No tienes ese vehículo.' };
    if (vid === 'mochila') return { err: 'La mochila no se vende.' };
    const V = VEHICLE[vid];
    const w = this.cargoWeight();
    const after = Math.max(this.capacity('land'), this.capacity('sea')) - V.cap;
    if (w > after) return { err: 'Descarga primero: no cabría la mercancía.' };
    this.p.vehicles[vid]--;
    if (!this.p.vehicles[vid]) delete this.p.vehicles[vid];
    const price = Math.round(V.cost * 0.6);
    this.p.gold += price;
    return { ok: true, msg: `Vendes ${V.name} por ${fmt(price)} ⦿.` };
  }
  hireGuards(n) {
    const price = n * 140;
    if (this.p.gold < price) return { err: 'No tienes suficiente oro.' };
    this.p.gold -= price; this.p.guards += n;
    return { ok: true, msg: `Contratas ${n} guardias (${fmt(price)} ⦿).` };
  }
  buildFactory(recipeId) {
    const r = RECIPE[recipeId], c = this.city;
    const exist = this.p.buildings.find(b => b.city === c.id && b.recipe === recipeId);
    const cost = Math.round(r.cost * (1 + c.tax) * (exist ? Math.pow(1.7, exist.level) : 1));
    if (this.p.gold < cost) return { err: 'No tienes suficiente oro.' };
    this.p.gold -= cost;
    if (exist) { exist.level++; return { ok: true, msg: `${r.name} de ${c.name} ampliada a nivel ${exist.level}.` }; }
    this.p.buildings.push({ city: c.id, recipe: recipeId, level: 1, profit: 0 });
    return { ok: true, msg: `Construyes ${r.name} en ${c.name} por ${fmt(cost)} ⦿.` };
  }
  sellFactory(i) {
    const b = this.p.buildings[i];
    if (!b) return { err: 'No existe ese taller.' };
    const r = RECIPE[b.recipe];
    let paid = 0;
    for (let l = 0; l < b.level; l++) paid += r.cost * Math.pow(1.7, l);
    const back = Math.round(paid * 0.5);
    this.p.gold += back;
    this.p.buildings.splice(i, 1);
    return { ok: true, msg: `Vendes ${r.name} de ${this.world.cities[b.city].name} por ${fmt(back)} ⦿.` };
  }
  buildWarehouse() {
    const c = this.city;
    if (this.p.warehouses[c.id]) {
      const cost = 2200;
      if (this.p.gold < cost) return { err: 'No tienes suficiente oro.' };
      this.p.gold -= cost;
      this.p.warehouses[c.id].cap += 350;
      return { ok: true, msg: `Amplías el almacén de ${c.name} (+350).` };
    }
    const cost = 3000;
    if (this.p.gold < cost) return { err: 'No tienes suficiente oro.' };
    this.p.gold -= cost;
    this.p.warehouses[c.id] = { cap: 350, stock: {} };
    return { ok: true, msg: `Almacén construido en ${c.name}.` };
  }
  storeGood(g, n) {
    const w = this.p.warehouses[this.p.at];
    if (!w) return { err: 'No tienes almacén aquí.' };
    n = Math.min(Math.floor(n), Math.floor(this.p.cargo[g] || 0));
    let used = 0; for (const k in w.stock) used += w.stock[k] * GOOD[k].w;
    const space = Math.floor((w.cap - used) / GOOD[g].w);
    n = Math.min(n, space);
    if (n <= 0) return { err: 'El almacén está lleno.' };
    this.p.cargo[g] -= n; if (this.p.cargo[g] <= 0) delete this.p.cargo[g];
    w.stock[g] = (w.stock[g] || 0) + n;
    return { ok: true };
  }
  takeGood(g, n) {
    const w = this.p.warehouses[this.p.at];
    if (!w) return { err: 'No tienes almacén aquí.' };
    n = Math.min(Math.floor(n), Math.floor(w.stock[g] || 0));
    const cap = Math.max(this.capacity('land'), this.capacity('sea'));
    const space = Math.floor((cap - this.cargoWeight()) / GOOD[g].w);
    n = Math.min(n, space);
    if (n <= 0) return { err: 'No tienes espacio de carga.' };
    w.stock[g] -= n; if (w.stock[g] <= 0) delete w.stock[g];
    this.p.cargo[g] = (this.p.cargo[g] || 0) + n;
    return { ok: true };
  }
  takeLoan(amount) {
    const max = Math.max(1000, Math.round(this.netWorth() * 0.6 + 500 - this.debt()));
    if (amount > max) return { err: `El banco no te presta más de ${fmt(max)} ⦿.` };
    const rate = 0.0012 + (this.p.noto > 0.4 ? 0.0008 : 0) - clamp(this.p.rep, 0, 40) * 0.000008;
    this.p.gold += amount;
    this.p.loans.push({ amount: amount * 1.02, rate, day: this.day });
    return { ok: true, msg: `Recibes ${fmt(amount)} ⦿ al ${(rate * 100).toFixed(2)}% diario.` };
  }
  repayLoan(i, amount) {
    const l = this.p.loans[i];
    if (!l) return { err: 'Préstamo inexistente.' };
    amount = Math.min(amount, this.p.gold, l.amount);
    if (amount <= 0) return { err: 'Nada que pagar.' };
    this.p.gold -= amount; l.amount -= amount;
    if (l.amount < 1) this.p.loans.splice(i, 1);
    return { ok: true };
  }
  buyInsurance() {
    const cost = Math.round(400 + this.cargoWeight() * 3);
    if (this.p.gold < cost) return { err: 'No tienes suficiente oro.' };
    this.p.gold -= cost; this.p.insured = true;
    return { ok: true, msg: 'Seguro de carga contratado.' };
  }

  explore() {
    const c = this.city;
    const cost = 120 + Math.round(this.day * 0.5);
    if (this.p.gold < cost) return { err: 'Necesitas oro para pagar guías y provisiones.' };
    this.p.gold -= cost;
    const days = rint(3, 8);
    // buscar frontera de niebla
    const W = this.world;
    let bestX = c.x, bestY = c.y, bestScore = -1;
    for (let i = 0; i < 400; i++) {
      const ang = rnd() * Math.PI * 2, r = rrange(10, 42);
      const x = Math.round(c.x + Math.cos(ang) * r), y = Math.round(c.y + Math.sin(ang) * r);
      if (!W.inBounds(x, y)) continue;
      let unknown = 0;
      for (let k = 0; k < 12; k++) {
        const px = x + rint(-6, 6), py = y + rint(-6, 6);
        if (W.inBounds(px, py) && !W.known[W.idx(px, py)]) unknown++;
      }
      const score = unknown - r * 0.05;
      if (score > bestScore) { bestScore = score; bestX = x; bestY = y; }
    }
    const found = W.revealPath(c.x, c.y, bestX, bestY, 9).concat(W.reveal(bestX, bestY, 16));
    this.advanceDays(days);
    const uniq = [...new Set(found)];
    for (const d of uniq) this.news(`Expedición: descubres ${d.name}.`, 'good', d.id, '🧭');
    return { ok: true, days, found: uniq, cost };
  }

  buyMap() {
    const c = this.city;
    const cost = 260 + this.day;
    if (this.p.gold < cost) return { err: 'No tienes suficiente oro.' };
    this.p.gold -= cost;
    const unknown = this.world.cities.filter(x => !x.known);
    if (!unknown.length) return { ok: true, msg: 'El cartógrafo admite que ya conoces todo el mundo conocido.' };
    unknown.sort((a, b) => dist(a.x, a.y, c.x, c.y) - dist(b.x, b.y, c.x, c.y));
    const target = unknown[Math.min(unknown.length - 1, rint(0, 2))];
    target.known = true;
    this.world.reveal(target.x, target.y, 9);
    this.world.revealPath(c.x, c.y, target.x, target.y, 3);
    this.news(`Compras una carta náutica: aparece ${target.name}.`, 'good', target.id, '🗺️');
    return { ok: true, msg: `El mapa revela ${target.name}.`, city: target };
  }

  raidCaravan() {
    const c = this.city;
    if (this.p.guards < 5) return { err: 'Necesitas al menos 5 guardias para una emboscada.' };
    const days = rint(2, 5);
    this.advanceDays(days);
    const near = this.ai.merchants.filter(m => m.alive && dist(this.world.cities[m.at].x, this.world.cities[m.at].y, c.x, c.y) < 30);
    this.p.noto += 0.3; this.p.rep -= 5;
    this.stats.raids++;
    if (!near.length || rnd() < 0.35) {
      const lost = Math.min(this.p.guards, rint(1, 3));
      this.p.guards -= lost;
      return { ok: true, days, msg: `La emboscada fracasa. Pierdes ${lost} guardias y tu nombre corre por las tabernas.` };
    }
    const m = pick(near);
    let loot = [], gold = Math.round(m.gold * 0.25);
    m.gold -= gold; this.p.gold += gold;
    const cap = Math.max(this.capacity('land'), this.capacity('sea'));
    for (const g in m.cargo) {
      const space = Math.floor((cap - this.cargoWeight()) / GOOD[g].w);
      const take = Math.min(Math.floor(m.cargo[g]), space);
      if (take > 0) {
        m.cargo[g] -= take;
        this.p.cargo[g] = (this.p.cargo[g] || 0) + take;
        loot.push(`${take} ${GOOD[g].name}`);
      }
    }
    // las ciudades cercanas se enteran
    for (const cc of this.world.cities) if (dist(cc.x, cc.y, c.x, c.y) < 30) cc.playerRep -= 4;
    return { ok: true, days, msg: `Asaltas a ${m.company}: ${fmt(gold)} ⦿${loot.length ? ' y ' + loot.join(', ') : ''}.` };
  }

  /* ------------------------------ Contratos ------------------------------- */
  acceptContract(k) {
    if (this.p.contracts.length >= 5) return { err: 'No puedes llevar más de 5 contratos.' };
    k.taken = true;
    k.deadline = this.day + k.days;
    this.p.contracts.push(k);
    const c = this.world.cities[k.from];
    c.contracts = c.contracts.filter(x => x.id !== k.id);
    return { ok: true };
  }
  deliverContract(k) {
    if (k.to !== this.p.at) return { err: 'No estás en la ciudad de destino.' };
    if ((this.p.cargo[k.good] || 0) < k.qty) return { err: 'No llevas la mercancía completa.' };
    this.p.cargo[k.good] -= k.qty;
    if (this.p.cargo[k.good] <= 0) delete this.p.cargo[k.good];
    this.p.gold += k.reward;
    this.p.rep += 4;
    this.city.playerRep += 5;
    this.city.stock[k.good] += k.qty;
    this.stats.profit += k.reward * 0.5;
    this.p.contracts = this.p.contracts.filter(x => x.id !== k.id);
    return { ok: true, msg: `Contrato cumplido: +${fmt(k.reward)} ⦿ y prestigio en ${this.city.name}.` };
  }
  checkContracts() {
    for (let i = this.p.contracts.length - 1; i >= 0; i--) {
      const k = this.p.contracts[i];
      if (this.day > k.deadline) {
        this.p.gold -= k.penalty;
        this.p.rep -= 5;
        this.world.cities[k.to].playerRep -= 4;
        this.p.contracts.splice(i, 1);
        this.news(`Contrato vencido: pagas ${fmt(k.penalty)} ⦿ de penalización.`, 'bad', k.to, '⏳');
      }
    }
  }

  /* -------------------------------- Noticias ------------------------------ */
  news(text, kind, cityId, icon) {
    this.newsLog.unshift({ day: this.day, text, kind: kind || 'info', cityId: cityId === undefined ? null : cityId, icon: icon || '•' });
    if (this.newsLog.length > 260) this.newsLog.pop();
  }

  /* ------------------------------ Guardado -------------------------------- */
  save() {
    const W = this.world;
    const data = {
      v: 1, seed: this.seed, day: this.day, p: this.p, stats: this.stats,
      news: this.newsLog.slice(0, 80),
      cities: W.cities.map(c => ({
        s: c.stock, pr: c.price, pop: c.pop, we: c.wealth, ta: c.tax, bt: c.baseTax, un: c.unrest,
        ev: c.events, kn: c.known ? 1 : 0, vi: c.visited ? 1 : 0, rp: c.playerRep,
        ba: c.banned, ct: c.contracts, sy: c.shipyard ? 1 : 0, bk: c.bank ? 1 : 0,
        bp: c.basePop, bpr: c.baseProd, bcs: c.baseCons, prd: c.prod, cns: c.cons,
      })),
      edges: W.edges.map(e => [e.blocked, +e.danger.toFixed(3), e.toll || 0]),
      known: btoa(String.fromCharCode(...packBits(W.known))),
      ai: this.ai.merchants.filter(m => m.alive).map(m => ({
        n: m.name, c: m.company, s: m.style.id, g: Math.round(m.gold), ca: m.cargo,
        at: m.at, de: m.dest, dl: m.daysLeft, ed: m.edge, cp: m.cap, sp: +m.speed.toFixed(2),
        cs: m.canSea ? 1 : 0, tr: m.trades, pk: Math.round(m.peak),
      })),
    };
    localStorage.setItem(SAVE_KEY, JSON.stringify(data));
    return true;
  }

  static load() {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return null;
    let d;
    try { d = JSON.parse(raw); } catch (e) { return null; }
    const g = new Game(d.seed);
    g.day = d.day; g.p = d.p; g.stats = d.stats || g.stats;
    g.newsLog = d.news || [];
    d.cities.forEach((s, i) => {
      const c = g.world.cities[i];
      if (!c) return;
      c.stock = s.s; c.price = s.pr; c.pop = s.pop; c.wealth = s.we; c.tax = s.ta; c.baseTax = s.bt;
      c.unrest = s.un; c.events = s.ev || []; c.known = !!s.kn; c.visited = !!s.vi;
      c.playerRep = s.rp || 0; c.banned = s.ba || {}; c.contracts = s.ct || [];
      c.shipyard = !!s.sy; c.bank = !!s.bk;
      if (s.bp) { c.basePop = s.bp; c.baseProd = s.bpr; c.baseCons = s.bcs; }
      if (s.prd) { c.prod = s.prd; c.cons = s.cns; }
      for (const gg of GOOD_IDS) if (!c.priceHist[gg]) c.priceHist[gg] = [];
    });
    (d.edges || []).forEach((e, i) => {
      if (!g.world.edges[i]) return;
      g.world.edges[i].blocked = e[0]; g.world.edges[i].danger = e[1]; g.world.edges[i].toll = e[2];
    });
    if (d.known) unpackBits(atob(d.known), g.world.known);
    if (d.ai) {
      g.ai.merchants = d.ai.map((m, i) => {
        const mm = new Merchant(i, g.world);
        mm.name = m.n; mm.company = m.c; mm.style = AI_STYLES.find(s => s.id === m.s) || AI_STYLES[0];
        mm.gold = m.g; mm.cargo = m.ca; mm.at = m.at; mm.dest = m.de; mm.daysLeft = m.dl;
        mm.edge = m.ed; mm.cap = m.cp; mm.speed = m.sp; mm.canSea = !!m.cs; mm.trades = m.tr; mm.peak = m.pk;
        return mm;
      });
    }
    return g;
  }
  static hasSave() { return !!localStorage.getItem(SAVE_KEY); }
  static clearSave() { localStorage.removeItem(SAVE_KEY); }
}

/* niebla comprimida en bits */
function packBits(u8) {
  const out = new Uint8Array(Math.ceil(u8.length / 8));
  for (let i = 0; i < u8.length; i++) if (u8[i]) out[i >> 3] |= (1 << (i & 7));
  return out;
}
function unpackBits(str, u8) {
  for (let i = 0; i < u8.length; i++) {
    const b = str.charCodeAt(i >> 3) || 0;
    u8[i] = (b >> (i & 7)) & 1;
  }
}
