/* =========================================================================
   Merchant's Odyssey — comerciantes rivales con IA
   ========================================================================= */
'use strict';

const AI_STYLES = [
  { id: 'honesto', name: 'honesto', margin: 1.00, risk: 0.6, icon: '🧾' },
  { id: 'espec', name: 'especulador', margin: 1.15, risk: 1.0, icon: '📈' },
  { id: 'contra', name: 'contrabandista', margin: 1.25, risk: 1.5, icon: '🕯️' },
  { id: 'pirata', name: 'corsario', margin: 1.35, risk: 2.0, icon: '🏴‍☠️' },
  { id: 'gremio', name: 'gremial', margin: 0.95, risk: 0.4, icon: '⚖️' },
];

class Merchant {
  constructor(id, world) {
    this.id = id;
    const first = pick(MERCH_FIRST), last = pick(MERCH_LAST);
    this.name = first + ' ' + last;
    this.company = rnd() < 0.5 ? `${last} ${pick(COMPANY_SUFFIX)}` : `Casa ${last}`;
    this.style = pick(AI_STYLES);
    this.gold = rrange(300, 2200);
    this.cargo = {};
    this.at = rint(0, world.cities.length - 1);
    this.dest = -1; this.daysLeft = 0; this.edge = -1;
    this.cap = pickW([[30, 5], [80, 4], [180, 2], [400, 1]]);
    this.speed = rrange(0.9, 1.4);
    this.canSea = rnd() < 0.5;
    this.alive = true;
    this.trades = 0;
    this.peak = this.gold;
    this.history = [];
  }
  load() { let s = 0; for (const g in this.cargo) s += this.cargo[g] * GOOD[g].w; return s; }
  netWorth(world) {
    let v = this.gold;
    const c = world.cities[this.at];
    for (const g in this.cargo) v += this.cargo[g] * (c ? c.price[g] : GOOD[g].base);
    return v;
  }
}

class AIWorld {
  constructor(world, game, n = 64) {
    this.world = world; this.game = game;
    this.merchants = []; this.target = n; this.nextId = n;
    for (let i = 0; i < n; i++) this.merchants.push(new Merchant(i, world));
  }

  tick(day) {
    const W = this.world;
    for (const m of this.merchants) {
      if (!m.alive) continue;
      if (m.daysLeft > 0) {
        m.daysLeft--;
        if (m.daysLeft <= 0 && m.dest >= 0) this.arrive(m);
        continue;
      }
      this.decide(m, day);
    }
    if (day % 10 === 0) this.churn(day);
  }

  arrive(m) {
    const W = this.world;
    const e = W.edges[m.edge];
    m.at = m.dest; m.dest = -1;
    // riesgo del camino
    if (e && rnd() < (e.risk + e.danger) * 0.5 * m.style.risk) {
      const lossG = Object.keys(m.cargo);
      if (lossG.length) {
        const g = pick(lossG);
        const lost = Math.ceil(m.cargo[g] * rrange(0.3, 1));
        m.cargo[g] -= lost; if (m.cargo[g] <= 0) delete m.cargo[g];
      } else m.gold *= 0.85;
    }
    // vender todo en destino
    const c = W.cities[m.at];
    for (const g in m.cargo) {
      const n = m.cargo[g];
      if (n <= 0) continue;
      const rev = revenueToSell(c, g, n);
      m.gold += rev;
      c.stock[g] += n;
      m.trades++;
    }
    m.cargo = {};
    // crecer: mejorar capacidad
    if (m.gold > m.cap * 90 && rnd() < 0.25) { m.cap = Math.round(m.cap * 1.6); m.gold *= 0.75; if (!m.canSea && rnd() < 0.4) m.canSea = true; }
    m.peak = Math.max(m.peak, m.gold);
  }

  decide(m, day) {
    const W = this.world;
    const here = W.cities[m.at];
    let best = null;
    for (const ei of W.adj[m.at]) {
      const e = W.edges[ei];
      if (e.blocked > 0) continue;
      if (e.type === 'sea' && !m.canSea) continue;
      const to = e.a === m.at ? e.b : e.a;
      const dst = W.cities[to];
      const days = Math.max(0.5, e.days / m.speed);
      for (const g of GOOD_IDS) {
        const stock = here.stock[g] || 0;
        if (stock < 12) continue;
        if (here.banned[g] || dst.banned[g]) continue;   // los rivales no contrabandean
        const bp = buyPriceAt(here, g);
        const sp = sellPriceAt(dst, g);
        if (sp <= bp * 1.06) continue;
        const affordable = Math.floor(m.gold * 0.85 / bp);
        const byCap = Math.floor(m.cap / GOOD[g].w);
        const qty = Math.min(affordable, byCap, Math.floor(stock * 0.35), Math.floor((dst.stock[g] || 0) * 0.6 + 40));
        if (qty < 3) continue;
        const profit = (sp - bp) * qty * m.style.margin;
        const perDay = profit / (days + 0.6) - (e.risk + e.danger) * profit * (2.2 / m.style.risk);
        if (!best || perDay > best.perDay) best = { g, qty, to, ei, days, perDay, bp };
      }
    }
    if (!best || best.perDay <= 0) {
      // moverse igualmente para no estancarse
      const opts = W.adj[m.at].filter(ei => W.edges[ei].blocked <= 0 && (W.edges[ei].type !== 'sea' || m.canSea));
      if (opts.length && rnd() < 0.5) {
        const ei = pick(opts), e = W.edges[ei];
        m.edge = ei; m.dest = e.a === m.at ? e.b : e.a; m.daysLeft = Math.max(1, Math.round(e.days / m.speed));
      } else m.daysLeft = 1;
      return;
    }
    const cost = costToBuy(here, best.g, best.qty);
    if (cost > m.gold) { m.daysLeft = 1; return; }
    m.gold -= cost;
    here.stock[best.g] = Math.max(0, here.stock[best.g] - best.qty);
    m.cargo[best.g] = (m.cargo[best.g] || 0) + best.qty;
    m.edge = best.ei; m.dest = best.to;
    m.daysLeft = Math.max(1, Math.round(best.days));
  }

  churn(day) {
    for (const m of this.merchants) {
      if (!m.alive) continue;
      if (m.gold < 40 && m.load() < 1) {
        m.alive = false;
        if (m.peak > 20000) this.game.news(`${m.company} quiebra tras años de esplendor.`, 'rival', null, '📉');
      }
    }
    this.merchants = this.merchants.filter(m => m.alive);
    while (this.merchants.length < this.target && rnd() < 0.7) {
      this.merchants.push(new Merchant(this.nextId++, this.world));
    }
  }

  leaderboard() {
    const list = this.merchants.filter(m => m.alive)
      .map(m => ({ name: m.company, who: m.name, nw: m.netWorth(this.world), style: m.style }));
    list.sort((a, b) => b.nw - a.nw);
    return list;
  }
}
