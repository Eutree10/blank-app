/* =========================================================================
   Merchant's Odyssey — interfaz
   ========================================================================= */
'use strict';

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const UI = {
  G: null, V: null, tab: 'market', filter: 'all', openGood: null, busy: false,

  init(game, view) {
    this.G = game; this.V = view;
    view.onSelect = c => this.showCityCard(c);
    this.refreshAll();
  },

  /* ------------------------------ Eventos --------------------------------- */
  /** Se engancha una sola vez al cargar la página (antes de existir la partida). */
  bind() {
    document.addEventListener('click', e => {
      const t = e.target.closest('[data-act]');
      if (!t) return;
      this.action(t.dataset.act, t.dataset, e);
    });
    document.querySelectorAll('.tab').forEach(b => b.addEventListener('click', () => {
      this.tab = b.dataset.tab;
      document.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x === b));
      document.querySelectorAll('.pane').forEach(p => p.classList.toggle('active', p.id === 'pane-' + this.tab));
      this.refreshPanes();
    }));
    document.querySelectorAll('.mobile-tabs button').forEach(b => b.addEventListener('click', () => {
      document.querySelectorAll('.mobile-tabs button').forEach(x => x.classList.toggle('active', x === b));
      const m = b.dataset.mtab;
      $('sideLeft').classList.toggle('open', m === 'left');
      document.querySelector('.side.right').classList.toggle('open', m === 'right');
    }));
    $('btnWait').onclick = () => this.wait(1);
    $('btnSave').onclick = () => { if (this.G) { this.G.save(); this.toast('Partida guardada.', 'good'); } };
    $('btnHelp').onclick = () => this.help();
    $('modalClose').onclick = () => this.closeModal();
    $('modalWrap').addEventListener('click', e => { if (e.target === $('modalWrap')) this.closeModal(); });
    $('btnCenter').onclick = () => this.V.centerOn(this.G.city.x, this.G.city.y);
    $('btnRoutes').onclick = e => { this.V.showRoutes = !this.V.showRoutes; e.currentTarget.classList.toggle('off', !this.V.showRoutes); };
    $('btnRivals').onclick = e => { this.V.showRivals = !this.V.showRivals; e.currentTarget.classList.toggle('off', !this.V.showRivals); };
    document.addEventListener('keydown', e => {
      if (e.target.tagName === 'INPUT') return;
      if (e.key === 'Escape') { this.closeModal(); return; }
      if (!this.G) return;
      if (e.key === ' ') { e.preventDefault(); this.wait(1); }
      if (e.key === 'm') this.selectTab('market');
      if (e.key === 'c') this.selectTab('city');
      if (e.key === 'i') this.selectTab('empire');
      if (e.key === 'w') this.selectTab('world');
    });
  },
  selectTab(t) { const b = document.querySelector(`.tab[data-tab="${t}"]`); if (b) b.click(); },

  action(act, d, ev) {
    const G = this.G;
    if (act === 'modal-close') { this.closeModal(); return; }
    if (act === 'help') { this.help(); return; }
    if (!G) return;
    switch (act) {
      case 'travel': this.travelTo(+d.city); break;
      case 'select-city': {
        const c = G.world.cities[+d.city];
        this.V.selected = c; this.V.centerOn(c.x, c.y); this.showCityCard(c);
        break;
      }
      case 'good': this.openGood = this.openGood === d.g ? null : d.g; this.renderMarket(); break;
      case 'buy': this.doBuy(d.g, this.qtyOf(d.g)); break;
      case 'sell': this.doSell(d.g, this.qtyOf(d.g)); break;
      case 'buymax': this.doBuy(d.g, G.maxBuy(d.g)); break;
      case 'sellmax': this.doSell(d.g, Math.floor(G.p.cargo[d.g] || 0)); break;
      case 'qty': {
        const inp = document.querySelector(`input[data-qty="${d.g}"]`);
        if (inp) { inp.value = d.v === 'max' ? G.maxBuy(d.g) : d.v; }
        break;
      }
      case 'store': this.doStore(d.g); break;
      case 'take': this.doTake(d.g); break;
      case 'explore': this.doExplore(); break;
      case 'buymap': this.res(G.buyMap()); break;
      case 'shipyard': this.shipyard(); break;
      case 'bank': this.bank(); break;
      case 'tavern': this.tavern(); break;
      case 'factory': this.factoryModal(); break;
      case 'warehouse': this.warehouseModal(); break;
      case 'build': this.res(G.buildFactory(d.r)); this.factoryModal(); break;
      case 'sellfac': this.res(G.sellFactory(+d.i)); break;
      case 'buyveh': this.res(G.buyVehicle(d.v)); this.shipyard(); break;
      case 'sellveh': this.res(G.sellVehicle(d.v)); this.refreshAll(); break;
      case 'guards': this.res(G.hireGuards(+d.n)); this.tavern(); break;
      case 'insure': this.res(G.buyInsurance()); this.tavern(); break;
      case 'raid': this.doRaid(); break;
      case 'loan': this.res(G.takeLoan(+d.n)); this.bank(); break;
      case 'repay': this.res(G.repayLoan(+d.i, +d.n)); this.bank(); break;
      case 'buildwh': this.res(G.buildWarehouse()); this.warehouseModal(); break;
      case 'accept': {
        const city = G.city;
        const k = city.contracts.find(x => x.id === d.k);
        if (k) { this.res(G.acceptContract(k)); this.toast(`Contrato aceptado: ${k.qty} ${GOOD[k.good].name} → ${G.world.cities[k.to].name}`, 'good'); }
        break;
      }
      case 'deliver': {
        const k = G.p.contracts.find(x => x.id === d.k);
        if (k) this.res(G.deliverContract(k));
        break;
      }
      case 'wait': this.wait(+d.n); break;
      case 'help': this.help(); break;
      case 'closecard': $('cityCard').classList.add('hidden'); this.V.selected = null; break;
      case 'modal-close': this.closeModal(); break;
    }
  },

  qtyOf(g) {
    const inp = document.querySelector(`input[data-qty="${g}"]`);
    return inp ? Math.max(0, Math.floor(+inp.value || 0)) : 1;
  },
  res(r) {
    if (!r) return;
    if (r.err) { this.toast(r.err, 'bad'); return; }
    if (r.msg) this.toast(r.msg, 'good');
    this.refreshAll();
  },

  /* ------------------------------- Toasts --------------------------------- */
  toast(msg, kind) {
    const el = document.createElement('div');
    el.className = 'toast ' + (kind || '');
    el.innerHTML = msg;
    $('toasts').appendChild(el);
    setTimeout(() => { el.style.transition = 'opacity .4s'; el.style.opacity = '0'; setTimeout(() => el.remove(), 420); }, 3600);
    while ($('toasts').children.length > 5) $('toasts').firstChild.remove();
  },

  /* -------------------------------- Modal --------------------------------- */
  modal(title, body, foot) {
    $('modalTitle').innerHTML = title;
    $('modalBody').innerHTML = body;
    $('modalFoot').innerHTML = foot || '<button class="btn" data-act="modal-close">Cerrar</button>';
    $('modalWrap').classList.remove('hidden');
  },
  closeModal() { $('modalWrap').classList.add('hidden'); },

  /* ------------------------------ Refrescos -------------------------------- */
  refreshAll() { this.renderTop(); this.renderLeft(); this.refreshPanes(); this.showCityCard(this.V.selected); },
  refreshPanes() {
    if (this.tab === 'market') this.renderMarket();
    if (this.tab === 'city') this.renderCity();
    if (this.tab === 'empire') this.renderEmpire();
    if (this.tab === 'world') this.renderWorld();
  },

  renderTop() {
    const G = this.G;
    $('tDate').textContent = dateStr(G.day);
    $('tGold').textContent = fmt(G.p.gold) + ' ⦿';
    $('tNet').textContent = fmt(G.netWorth());
    const cap = Math.max(G.capacity('land'), G.capacity('sea'));
    $('tCargo').textContent = `${Math.round(G.cargoWeight())}/${Math.round(cap)}`;
    $('tTitle').textContent = G.title();
  },

  renderLeft() {
    const G = this.G, p = G.p;
    // flota
    const fl = Object.keys(p.vehicles).map(v =>
      `<span class="v" title="${VEHICLE[v].name}">${VEHICLE[v].icon} ${p.vehicles[v]}</span>`).join('');
    $('fleetSummary').innerHTML = fl +
      (p.guards ? `<span class="v" title="Guardias">🛡️ ${p.guards}</span>` : '') +
      (p.insured ? '<span class="v" title="Carga asegurada">📋</span>' : '');
    const w = G.cargoWeight(), cap = Math.max(G.capacity('land'), G.capacity('sea'));
    const bar = $('cargoBar');
    bar.style.width = clamp(w / cap * 100, 0, 100) + '%';
    bar.classList.toggle('full', w / cap > 0.92);
    $('cargoTxt').textContent = `${Math.round(w)} / ${Math.round(cap)} de carga · tierra ${Math.round(G.capacity('land'))} · mar ${Math.round(G.capacity('sea'))}`;

    // bodega
    const gs = Object.keys(p.cargo).filter(g => p.cargo[g] >= 0.5);
    $('cargoCount').textContent = gs.length ? gs.length + ' bienes' : '';
    const c = G.city;
    $('cargoList').innerHTML = gs.length ? gs.map(g => {
      const n = Math.floor(p.cargo[g]);
      const val = sellPriceAt(c, g) * n;
      const avg = p.avgCost && p.avgCost[g] && p.avgCost[g].n > 0 ? p.avgCost[g].total / p.avgCost[g].n : null;
      const delta = avg ? (sellPriceAt(c, g) - avg) / avg : null;
      return `<div class="li"><span class="ic">${GOOD[g].icon}</span>
        <span class="nm">${GOOD[g].name}</span>
        <span class="qt">${n}</span>
        <span class="mt ${delta === null ? '' : delta > 0.02 ? 'up' : delta < -0.02 ? 'down' : ''}">${fmt(val)}</span></div>`;
    }).join('') : '<div class="empty">Bodega vacía. Compra algo barato.</div>';

    // contratos
    $('contractCount').textContent = p.contracts.length ? p.contracts.length + '/5' : '';
    $('contractList').innerHTML = p.contracts.length ? p.contracts.map(k => {
      const to = G.world.cities[k.to];
      const left = k.deadline - G.day;
      const have = Math.floor(p.cargo[k.good] || 0);
      return `<div class="li" data-act="select-city" data-city="${k.to}" style="cursor:pointer">
        <span class="ic">${GOOD[k.good].icon}</span>
        <span class="nm">${k.qty}× ${GOOD[k.good].name} → ${esc(to.name)}<br><span class="mt">${have}/${k.qty} a bordo · ${fmt(k.reward)} ⦿</span></span>
        <span class="qt ${left < 6 ? 'down' : ''}">${left}d</span></div>`;
    }).join('') : '<div class="empty">Sin contratos activos.</div>';
  },

  /* ------------------------------- Mercado --------------------------------- */
  renderMarket() {
    const G = this.G, c = G.city;
    const filters = [['all', 'Todo'], ['0', 'Materias'], ['1', 'Elaborados'], ['2', 'Manufacturas'], ['mine', 'Mi bodega'], ['deal', 'Oportunidades']];
    let rows = '';
    for (const good of GOODS) {
      const g = good.id;
      if (this.filter === '0' || this.filter === '1' || this.filter === '2') { if (String(good.tier) !== this.filter) continue; }
      if (this.filter === 'mine' && !(G.p.cargo[g] >= 0.5)) continue;
      const bp = buyPriceAt(c, g), sp = sellPriceAt(c, g) * (c.banned[g] ? 1.85 : 1 - c.tax);
      const base = good.base;
      const ratio = bp / base;
      if (this.filter === 'deal' && !(ratio < 0.78 || (G.p.cargo[g] >= 1 && this.bestSellDelta(g) > 0.15))) continue;
      const trend = c.price[g] - (c.lastPrice[g] || c.price[g]);
      const tclass = trend > 0.02 ? 'up' : trend < -0.02 ? 'down' : 'flat';
      const tarrow = trend > 0.02 ? '▲' : trend < -0.02 ? '▼' : '·';
      const mine = Math.floor(G.p.cargo[g] || 0);
      const cheap = ratio < 0.75, dear = ratio > 1.4;
      rows += `<tr class="g ${this.openGood === g ? 'sel' : ''}" data-act="good" data-g="${g}">
        <td class="tier${good.tier}"><span class="gname">${good.icon} ${good.name}
          ${c.banned[g] ? '<span class="pill">prohibido</span>' : ''}
          ${c.banned[g] ? '' : cheap ? '<span class="pill deal">barato</span>' : dear ? '<span class="pill">caro</span>' : ''}</span></td>
        <td class="${cheap ? 'up' : ''}">${c.banned[g] ? '—' : fmt(bp)}</td>
        <td class="${dear ? 'down' : ''}">${fmt(sp)}</td>
        <td class="mini">${fmt(c.stock[g])}</td>
        <td class="${mine ? '' : 'flat'}">${mine || '–'}</td>
        <td class="${tclass}">${tarrow}</td></tr>`;
      if (this.openGood === g) rows += this.tradeRow(g);
    }
    $('pane-market').innerHTML = `
      <div class="mkt-head">
        <div><h2>${esc(c.name)}</h2>
        <div class="where">${BIOMES[c.biome].name} · ${fmt(c.pop)} hab · impuesto ${(c.tax * 100).toFixed(1)}% · ${c.coastal ? 'puerto' : 'interior'}</div></div>
      </div>
      <div class="filters">${filters.map(f => `<button data-f="${f[0]}" class="${this.filter === f[0] ? 'active' : ''}">${f[1]}</button>`).join('')}</div>
      <table class="mkt">
        <thead><tr><th>Bien</th><th>Compra</th><th>Venta</th><th>Stock</th><th>Tuyo</th><th></th></tr></thead>
        <tbody>${rows || '<tr><td colspan="6" class="mini" style="padding:14px">Nada que mostrar con este filtro.</td></tr>'}</tbody>
      </table>`;
    $('pane-market').querySelectorAll('.filters button').forEach(b => b.onclick = e => {
      e.stopPropagation(); this.filter = b.dataset.f; this.renderMarket();
    });
  },

  tradeRow(g) {
    const G = this.G, c = G.city;
    const mine = Math.floor(G.p.cargo[g] || 0);
    const max = G.maxBuy(g);
    const spark = this.sparkline(c.priceHist[g]);
    const where = this.whereToSell(g);
    const wh = G.p.warehouses[G.p.at];
    return `<tr class="trade-row"><td colspan="6"><div class="trade-box">
      ${spark}
      <div class="qty">
        <input type="number" min="1" step="1" value="${Math.max(1, Math.min(10, max || 1))}" data-qty="${g}">
        <button class="btn tiny" data-act="qty" data-g="${g}" data-v="10">10</button>
        <button class="btn tiny" data-act="qty" data-g="${g}" data-v="50">50</button>
        <button class="btn tiny" data-act="qty" data-g="${g}" data-v="max">Máx</button>
        <span class="mini">cabe ${max}</span>
      </div>
      <div class="qty">
        <button class="btn tiny primary" data-act="buy" data-g="${g}" ${c.banned[g] ? 'disabled' : ''}>Comprar</button>
        <button class="btn tiny" data-act="sell" data-g="${g}" ${mine ? '' : 'disabled'}>Vender</button>
        <button class="btn tiny" data-act="sellmax" data-g="${g}" ${mine ? '' : 'disabled'}>Vender todo (${mine})</button>
        ${wh ? `<button class="btn tiny ghost" data-act="store" data-g="${g}" ${mine ? '' : 'disabled'}>→ Almacén</button>
                <button class="btn tiny ghost" data-act="take" data-g="${g}" ${(wh.stock[g] || 0) ? '' : 'disabled'}>← Almacén (${Math.floor(wh.stock[g] || 0)})</button>` : ''}
      </div>
      ${c.banned[g] ? '<div class="mini" style="color:#f3b2ae">Bien prohibido aquí: no se puede comprar, y venderlo da un 85% extra… con riesgo de confiscación.</div>' : ''}
      <div>
        <div class="mini" style="margin-bottom:4px">Precios que recuerdas (venta neta estimada)</div>
        <div class="where-list">${where}</div>
      </div>
    </div></td></tr>`;
  },

  sparkline(hist) {
    if (!hist || hist.length < 3) return '<div class="mini">Sin histórico de precios todavía.</div>';
    const h = hist.slice(-46);
    const min = Math.min(...h), max = Math.max(...h), rng = Math.max(0.001, max - min);
    const pts = h.map((v, i) => `${(i / (h.length - 1) * 100).toFixed(2)},${(30 - (v - min) / rng * 28).toFixed(2)}`).join(' ');
    const up = h[h.length - 1] >= h[0];
    return `<div><svg class="spark" viewBox="0 0 100 32" preserveAspectRatio="none">
      <polyline points="${pts}" fill="none" stroke="${up ? '#3FB950' : '#F85149'}" stroke-width="1.4" vector-effect="non-scaling-stroke"/>
    </svg><div class="mini">${h.length} días · mín ${fmt(min)} · máx ${fmt(max)}</div></div>`;
  },

  /** Precios recordados en otras ciudades. */
  whereToSell(g) {
    const G = this.G, mem = G.p.memory || {};
    const here = G.city;
    const out = [];
    for (const cid in mem) {
      const m = mem[cid];
      if (+cid === G.p.at) continue;
      const city = G.world.cities[cid];
      if (!city || !city.known) continue;
      const price = m.price[g];
      if (!price) continue;
      const age = G.day - m.day;
      const r = G.routeTo(city.id);
      out.push({ city, price, age, days: r ? Math.round(r.days) : null, black: !!city.banned[g] });
    }
    out.sort((a, b) => b.price - a.price);
    const cur = sellPriceAt(here, g) * (here.banned[g] ? 1.85 : 1 - here.tax);
    const top = out.slice(0, 7).map(o => {
      const d = (o.price - cur) / cur;
      return `<div class="w" data-act="select-city" data-city="${o.city.id}">
        <span>${esc(o.city.name)}${o.black ? ' 🕯️' : ''} <span class="mini">${o.days !== null ? o.days + 'd' : '?'} · hace ${o.age}d</span></span>
        <span class="${d > 0.03 ? 'up' : d < -0.03 ? 'down' : 'flat'}">${fmt(o.price)} ⦿ ${pct(d)}</span></div>`;
    }).join('');
    return top || '<div class="mini">Aún no has visitado otros mercados.</div>';
  },
  bestSellDelta(g) {
    const G = this.G, mem = G.p.memory || {}, c = G.city;
    const cur = sellPriceAt(c, g) * (c.banned[g] ? 1.85 : 1 - c.tax);
    let best = cur;
    for (const cid in mem) if (mem[cid].price[g]) best = Math.max(best, mem[cid].price[g]);
    return (best - cur) / cur;
  },

  /* -------------------------------- Ciudad --------------------------------- */
  renderCity() {
    const G = this.G, c = G.city;
    const evs = c.events.map(e => `<span class="evtag ${['guerra', 'peste', 'hambruna', 'sequia', 'erupcion', 'revolucion', 'impuestos', 'minaagotada', 'plagaganado'].includes(e.id) ? 'bad' : 'good'}">${e.icon} ${e.name} · ${e.daysLeft}d</span>`).join('') || '<span class="mini">Sin sucesos activos.</span>';
    const sp = c.specialties.map(s => `<span class="evtag">${SPECIALTY[s].icon} ${SPECIALTY[s].name}</span>`).join('');
    const banned = Object.keys(c.banned);
    const ks = c.contracts.map(k => {
      const to = G.world.cities[k.to];
      const have = Math.floor(G.p.cargo[k.good] || 0);
      return `<div class="opt">
        <span>${GOOD[k.good].icon}</span>
        <div class="t"><b>${k.qty}× ${GOOD[k.good].name} → ${esc(to.name)}</b>
        <small>${k.days} días · paga ${fmt(k.reward)} ⦿ · multa ${fmt(k.penalty)} ⦿ · llevas ${have}</small></div>
        <button class="btn tiny primary" data-act="accept" data-k="${k.id}">Aceptar</button></div>`;
    }).join('') || '<div class="mini">No hay contratos ahora mismo.</div>';
    const deliver = G.p.contracts.filter(k => k.to === c.id).map(k =>
      `<div class="opt"><span>${GOOD[k.good].icon}</span><div class="t"><b>Entregar ${k.qty}× ${GOOD[k.good].name}</b>
      <small>llevas ${Math.floor(G.p.cargo[k.good] || 0)} · paga ${fmt(k.reward)} ⦿ · ${k.deadline - G.day} días</small></div>
      <button class="btn tiny primary" data-act="deliver" data-k="${k.id}" ${(G.p.cargo[k.good] || 0) >= k.qty ? '' : 'disabled'}>Entregar</button></div>`).join('');

    $('pane-city').innerHTML = `
      <div class="block">
        <h3>${esc(c.name)}</h3>
        <div class="kv"><span>Población</span><b>${fmt(c.pop)}</b></div>
        <div class="kv"><span>Riqueza</span><b>${(c.wealth * 100).toFixed(0)}</b></div>
        <div class="kv"><span>Impuesto</span><b>${(c.tax * 100).toFixed(1)}%</b></div>
        <div class="kv"><span>Descontento</span><b class="${c.unrest > 0.5 ? 'down' : ''}">${(c.unrest * 100).toFixed(0)}%</b></div>
        <div class="kv"><span>Tu prestigio aquí</span><b class="${c.playerRep < 0 ? 'down' : 'up'}">${c.playerRep.toFixed(0)}</b></div>
        <div class="evrow" style="margin-top:8px">${sp}</div>
        ${banned.length ? `<div class="mini">Prohibido: ${banned.map(b => GOOD[b].icon + ' ' + GOOD[b].name).join(', ')}</div>` : ''}
      </div>
      <div class="block"><h3>Sucesos</h3><div class="evrow">${evs}</div></div>
      <div class="block"><h3>Servicios</h3>
        <div class="grid2">
          <button class="btn tiny" data-act="tavern">🍺 Taberna</button>
          <button class="btn tiny" data-act="factory">🏭 Talleres</button>
          <button class="btn tiny" ${c.shipyard ? '' : 'disabled'} data-act="shipyard">⚓ ${c.shipyard ? 'Astillero' : 'Sin astillero'}</button>
          <button class="btn tiny" ${c.bank ? '' : 'disabled'} data-act="bank">🏦 ${c.bank ? 'Banco' : 'Sin banco'}</button>
          <button class="btn tiny" data-act="warehouse">📦 Almacén</button>
          <button class="btn tiny" data-act="buymap">🗺️ Comprar mapa</button>
        </div>
        <button class="btn tiny wide" style="margin-top:6px" data-act="explore">🧭 Organizar expedición (3-8 días)</button>
      </div>
      ${deliver ? `<div class="block"><h3>Entregas pendientes aquí</h3>${deliver}</div>` : ''}
      <div class="block"><h3>Contratos disponibles</h3>${ks}</div>`;
  },

  /* -------------------------------- Imperio -------------------------------- */
  renderEmpire() {
    const G = this.G, p = G.p;
    const veh = Object.keys(p.vehicles).map(v => {
      const V = VEHICLE[v];
      return `<div class="opt"><span>${V.icon}</span><div class="t"><b>${V.name} ×${p.vehicles[v]}</b>
        <small>${V.cap} carga · vel ${V.speed.toFixed(2)} · mant. ${V.up}/día · ${V.terrain === 'sea' ? 'mar' : 'tierra'}</small></div>
        ${v === 'mochila' ? '' : `<button class="btn tiny" data-act="sellveh" data-v="${v}">Vender ${fmt(V.cost * 0.6)}</button>`}</div>`;
    }).join('');
    const fac = p.buildings.map((b, bi) => {
      const r = RECIPE[b.recipe], c = G.world.cities[b.city];
      const ins = Object.keys(r.in).map(g => `${r.in[g]}${GOOD[g].icon}`).join(' + ');
      const outs = Object.keys(r.out).map(g => `${r.out[g]}${GOOD[g].icon}`).join(' + ');
      return `<div class="opt"><span>${r.icon}</span><div class="t"><b>${r.name} · ${esc(c.name)} · nv.${b.level}</b>
        <small>${ins} → ${outs} ×${b.level * FACTORY_BATCH}/día · ${b.idle ? 'parada (' + (b.why || 'inactiva') + ')' : 'produciendo'} · ${b.profit >= 0 ? '+' : ''}${fmt(b.profit || 0)} ⦿/día</small></div>
        <button class="btn tiny" data-act="select-city" data-city="${b.city}">Ver</button>
        <button class="btn tiny danger" data-act="sellfac" data-i="${bi}" title="Vender el taller por la mitad de lo invertido">Vender</button></div>`;
    }).join('') || '<div class="mini">Aún no tienes talleres. Construye uno en el panel de Ciudad.</div>';
    const whs = Object.keys(p.warehouses).map(cid => {
      const w = p.warehouses[cid], c = G.world.cities[cid];
      let used = 0, val = 0;
      for (const g in w.stock) { used += w.stock[g] * GOOD[g].w; val += w.stock[g] * c.price[g]; }
      const items = Object.keys(w.stock).map(g => `${GOOD[g].icon}${Math.floor(w.stock[g])}`).join(' ') || 'vacío';
      return `<div class="opt"><span>📦</span><div class="t"><b>${esc(c.name)}</b>
        <small>${Math.round(used)}/${w.cap} · ${items} · valor ${fmt(val)} ⦿</small></div>
        <button class="btn tiny" data-act="select-city" data-city="${cid}">Ver</button></div>`;
    }).join('') || '<div class="mini">Sin almacenes.</div>';
    const loans = p.loans.map((l, i) => `<div class="opt"><span>🏦</span><div class="t"><b>${fmt(l.amount)} ⦿</b>
      <small>${(l.rate * 100).toFixed(2)}% diario · desde el día ${l.day}</small></div>
      <button class="btn tiny" data-act="repay" data-i="${i}" data-n="${Math.ceil(l.amount)}">Pagar</button></div>`).join('') || '<div class="mini">Sin deudas. Bien.</div>';

    $('pane-empire').innerHTML = `
      <div class="block">
        <h3>Balance</h3>
        <div class="kv"><span>Oro</span><b class="gold">${fmt(p.gold)} ⦿</b></div>
        <div class="kv"><span>Valor de la carga</span><b>${fmt(Object.keys(p.cargo).reduce((s, g) => s + p.cargo[g] * G.city.price[g], 0))}</b></div>
        <div class="kv"><span>Deuda</span><b class="${G.debt() ? 'down' : ''}">${fmt(G.debt())}</b></div>
        <div class="kv"><span>Mantenimiento</span><b>${fmt(G.upkeep())} ⦿/día</b></div>
        <div class="kv"><span>Patrimonio neto</span><b class="gold">${fmt(G.netWorth())}</b></div>
        <div class="kv"><span>Título</span><b>${G.title()}</b></div>
        <div class="kv"><span>Reputación / notoriedad</span><b>${p.rep.toFixed(0)} / ${(p.noto * 100).toFixed(0)}</b></div>
      </div>
      <div class="block"><h3>Flota</h3>${veh}</div>
      <div class="block"><h3>Talleres y fábricas</h3>${fac}</div>
      <div class="block"><h3>Almacenes</h3>${whs}</div>
      <div class="block"><h3>Préstamos</h3>${loans}</div>
      <div class="block"><h3>Estadísticas</h3>
        <div class="kv"><span>Días en el camino</span><b>${G.stats.days}</b></div>
        <div class="kv"><span>Distancia recorrida</span><b>${fmt(G.stats.km)} leguas</b></div>
        <div class="kv"><span>Unidades compradas / vendidas</span><b>${fmt(G.stats.bought)} / ${fmt(G.stats.sold)}</b></div>
        <div class="kv"><span>Beneficio acumulado</span><b class="${G.stats.profit >= 0 ? 'up' : 'down'}">${fmt(G.stats.profit)}</b></div>
        <div class="kv"><span>Decomisos / emboscadas</span><b>${G.stats.caught} / ${G.stats.raids}</b></div>
      </div>`;
  },

  /* --------------------------------- Mundo --------------------------------- */
  renderWorld() {
    const G = this.G;
    const news = G.newsLog.slice(0, 40).map(n => `<div class="newsitem ${n.kind === 'bad' ? 'bad' : n.kind === 'good' ? 'good' : ''}">
      <span class="ic">${n.icon}</span><span class="tx">${esc(n.text)}</span><span class="dy">d${n.day}</span></div>`).join('');
    const lb = G.ai.leaderboard();
    const mine = G.netWorth();
    const all = lb.map(x => ({ name: x.name, who: x.who, nw: x.nw, icon: x.style.icon }));
    all.push({ name: 'Tú', who: G.title(), nw: mine, me: true, icon: '⚖️' });
    all.sort((a, b) => b.nw - a.nw);
    const myPos = all.findIndex(x => x.me) + 1;
    const rank = all.slice(0, 12).map((x, i) => `<div class="rank ${x.me ? 'me' : ''}">
      <span class="n">${i + 1}</span><span>${x.icon}</span>
      <span class="nm">${esc(x.name)} <span class="mini">${esc(x.who)}</span></span>
      <span class="nw">${fmt(x.nw)}</span></div>`).join('');

    // oportunidades: comprar aquí, vender donde recuerdas
    const opps = this.opportunities().slice(0, 8).map(o => `<div class="opt">
      <span>${GOOD[o.g].icon}</span><div class="t"><b>${GOOD[o.g].name} → ${esc(o.city.name)}${o.black ? ' <span class="pill">contrabando</span>' : ''}</b>
      <small>compra ${fmt(o.buy)} · venta recordada ${fmt(o.sell)} · ${pct(o.margin)} · ${o.days}d · hace ${o.age}d</small></div>
      <button class="btn tiny" data-act="select-city" data-city="${o.city.id}">Ruta</button></div>`).join('')
      || '<div class="mini">Visita más ciudades para comparar precios.</div>';

    $('pane-world').innerHTML = `
      <div class="block"><h3>Oportunidades desde aquí</h3>${opps}</div>
      <div class="block"><h3>Los más ricos <span class="hint">tu puesto: ${myPos}/${all.length}</span></h3>${rank}</div>
      <div class="block"><h3>Crónicas del mundo</h3>${news || '<div class="mini">Silencio en los caminos.</div>'}</div>`;
  },

  opportunities() {
    const G = this.G, c = G.city, mem = G.p.memory || {};
    const out = [];
    for (const good of GOODS) {
      const g = good.id;
      if (c.stock[g] < 10 || c.banned[g]) continue;
      const bp = buyPriceAt(c, g);
      for (const cid in mem) {
        if (+cid === G.p.at) continue;
        const city = G.world.cities[cid];
        const sell = mem[cid].price[g];
        if (!sell || !city) continue;
        const margin = (sell - bp) / bp;
        if (margin < 0.12) continue;
        const r = G.routeTo(city.id);
        if (!r) continue;
        const days = Math.max(1, Math.round(r.days));
        out.push({ g, city, buy: bp, sell, margin, days, age: G.day - mem[cid].day, score: margin / days, black: !!city.banned[g] });
      }
    }
    out.sort((a, b) => b.score - a.score);
    return out;
  },

  /* ---------------------------- Tarjeta de ciudad --------------------------- */
  showCityCard(c) {
    const el = $('cityCard');
    if (!c) { el.classList.add('hidden'); this.V.plan = null; return; }
    const G = this.G;
    el.classList.remove('hidden');
    if (c.id === G.p.at) {
      this.V.plan = null;
      el.innerHTML = `<h4>${esc(c.name)}</h4>
        <div class="meta">Estás aquí · ${BIOMES[c.biome].name} · ${fmt(c.pop)} hab</div>
        <div class="acts"><button class="btn tiny" data-act="closecard">Cerrar</button></div>`;
      return;
    }
    const r = G.routeTo(c.id);
    const mem = (G.p.memory || {})[c.id];
    const evs = c.events.map(e => `<span class="evtag">${e.icon} ${e.name}</span>`).join('');
    let route = '<div class="mini" style="color:#f3b2ae">Sin ruta conocida. Necesitas un barco o explorar más.</div>';
    if (r) {
      const days = Math.max(1, Math.round(r.days));
      const sea = r.edges.some(ei => G.world.edges[ei].type === 'sea');
      const w = G.cargoWeight();
      const capOk = sea ? w <= G.capacity('sea') : w <= G.capacity('land');
      route = `<div class="kv"><span>Viaje</span><b>${days} días</b></div>
        <div class="kv"><span>Vía</span><b>${sea ? '⛵ mar' : '🐴 tierra'} · ${r.path.length - 1} etapas</b></div>
        <div class="kv"><span>Riesgo</span><b class="${r.risk > 0.25 ? 'down' : r.risk > 0.1 ? '' : 'up'}">${(r.risk * 100).toFixed(0)}%</b></div>
        ${capOk ? '' : '<div class="mini" style="color:#f3b2ae">Tu carga no cabe en el transporte de esa ruta.</div>'}
        <div class="acts"><button class="btn tiny primary" data-act="travel" data-city="${c.id}" ${capOk ? '' : 'disabled'}>Viajar</button>
        <button class="btn tiny" data-act="closecard">Cerrar</button></div>`;
    }
    el.innerHTML = `<h4>${esc(c.name)}</h4>
      <div class="meta">${BIOMES[c.biome].name} · ${c.visited ? fmt(c.pop) + ' hab' : 'sin visitar'} ${c.coastal ? '· puerto' : ''}</div>
      ${evs ? `<div class="evrow">${evs}</div>` : ''}
      ${mem ? `<div class="kv"><span>Precios recordados</span><b>hace ${G.day - mem.day}d</b></div>` : '<div class="mini">No conoces sus precios.</div>'}
      ${route}`;
    this.V.plan = r;
  },

  /* -------------------------------- Acciones -------------------------------- */
  travelTo(cid) {
    if (this.busy) return;
    const G = this.G;
    const r = G.routeTo(cid);
    if (!r) { this.toast('No hay ruta hacia allí.', 'bad'); return; }
    this.busy = true;
    const res = G.travelTo(cid);
    if (res.err) { this.busy = false; this.toast(res.err, 'bad'); return; }
    this.V.plan = null;
    this.V.animateTravel(res.route.path, () => {
      this.busy = false;
      this.V.centerOn(G.city.x, G.city.y);
      this.arrival(res);
    });
    this.renderTop();
  },

  arrival(res) {
    const G = this.G, c = G.city;
    this.recordMemory();
    this.V.fogDirty = true;
    this.refreshAll();
    const changes = this.priceHighlights(c);
    const body = `
      <p>Llegas a <b>${esc(c.name)}</b> tras <b>${res.days} días</b> de camino.</p>
      ${res.log.length ? '<h4>En el camino</h4><ul>' + res.log.map(l => `<li>${l}</li>`).join('') + '</ul>' : ''}
      ${c.events.length ? '<h4>Situación</h4><div class="evrow">' + c.events.map(e => `<span class="evtag">${e.icon} ${e.name} · ${e.daysLeft}d</span>`).join('') + '</div>' : ''}
      <h4>Mercado</h4>${changes}`;
    this.modal(`${c.events.length ? c.events[0].icon + ' ' : '🏙️ '}${esc(c.name)}`, body,
      '<button class="btn primary" data-act="modal-close">Al mercado</button>');
  },

  priceHighlights(c) {
    const G = this.G;
    const list = GOODS.map(good => {
      const g = good.id;
      const bp = buyPriceAt(c, g), ratio = bp / good.base;
      return { g, good, bp, ratio, mine: Math.floor(G.p.cargo[g] || 0), sp: sellPriceAt(c, g) * (1 - c.tax) };
    });
    const cheap = list.filter(x => x.ratio < 0.8).sort((a, b) => a.ratio - b.ratio).slice(0, 4);
    const dear = list.filter(x => x.ratio > 1.3).sort((a, b) => b.ratio - a.ratio).slice(0, 4);
    const sellNow = list.filter(x => x.mine > 0).map(x => {
      const avg = G.p.avgCost && G.p.avgCost[x.g] && G.p.avgCost[x.g].n > 0 ? G.p.avgCost[x.g].total / G.p.avgCost[x.g].n : null;
      const d = avg ? (x.sp - avg) / avg : 0;
      return `<li>${x.good.icon} ${x.good.name} ×${x.mine} → ${fmt(x.sp * x.mine)} ⦿ ${avg ? `<span class="${d > 0 ? 'up' : 'down'}">(${pct(d)})</span>` : ''}</li>`;
    }).join('');
    return `<div class="grid2">
      <div><b>Barato aquí</b><ul>${cheap.map(x => `<li>${x.good.icon} ${x.good.name} · ${fmt(x.bp)} <span class="up">${pct(x.ratio - 1)}</span></li>`).join('') || '<li class="mini">nada destacable</li>'}</ul></div>
      <div><b>Caro aquí</b><ul>${dear.map(x => `<li>${x.good.icon} ${x.good.name} · ${fmt(x.bp)} <span class="down">${pct(x.ratio - 1)}</span></li>`).join('') || '<li class="mini">nada destacable</li>'}</ul></div>
    </div>${sellNow ? `<h4>Puedes vender</h4><ul>${sellNow}</ul>` : ''}`;
  },

  recordMemory() {
    const G = this.G, c = G.city;
    if (!G.p.memory) G.p.memory = {};
    const price = {};   // precio neto que realmente cobrarías aquí
    for (const g of GOOD_IDS) price[g] = sellPriceAt(c, g) * (c.banned[g] ? 1.85 : 1 - c.tax);
    G.p.memory[c.id] = { day: G.day, price };
  },

  wait(n) {
    if (this.busy) return;
    this.G.advanceDays(n);
    this.recordMemory();
    this.refreshAll();
    this.toast(`Pasan ${n} día${n > 1 ? 's' : ''}.`);
  },

  doBuy(g, n) {
    const r = this.G.buy(g, n);
    if (r.err) return this.toast(r.err, 'bad');
    this.toast(`Compras ${n} ${GOOD[g].name} por ${fmt(r.cost)} ⦿ (${fmt(r.unit)}/u).`, 'good');
    this.refreshAll();
  },
  doSell(g, n) {
    const r = this.G.sell(g, n);
    if (r.err) return this.toast(r.err, 'bad');
    if (r.caught) { this.toast(r.msg, 'bad'); this.refreshAll(); return; }
    this.toast(`Vendes ${n} ${GOOD[g].name} por ${fmt(r.rev)} ⦿ (${fmt(r.unit)}/u). ${r.note || ''}`, 'good');
    this.refreshAll();
  },
  doStore(g) { const r = this.G.storeGood(g, this.qtyOf(g)); if (r.err) this.toast(r.err, 'bad'); this.refreshAll(); },
  doTake(g) { const r = this.G.takeGood(g, this.qtyOf(g)); if (r.err) this.toast(r.err, 'bad'); this.refreshAll(); },

  doExplore() {
    const r = this.G.explore();
    if (r.err) return this.toast(r.err, 'bad');
    this.V.fogDirty = true;
    this.recordMemory();
    this.refreshAll();
    this.modal('🧭 Expedición', `<p>La expedición dura <b>${r.days} días</b> y cuesta ${fmt(r.cost)} ⦿.</p>
      ${r.found.length ? '<h4>Descubrimientos</h4><ul>' + r.found.map(c => `<li><b>${esc(c.name)}</b> — ${BIOMES[c.biome].name.toLowerCase()}${c.coastal ? ', puerto' : ''}</li>`).join('') + '</ul>'
        : '<p>Solo encuentras tierra vacía y caminos polvorientos… pero el mapa crece.</p>'}`);
  },

  doRaid() {
    const r = this.G.raidCaravan();
    if (r.err) return this.toast(r.err, 'bad');
    this.refreshAll();
    this.modal('🏴‍☠️ Emboscada', `<p>${r.msg}</p><p class="mini">Tu notoriedad crece; algunas ciudades te lo tendrán en cuenta.</p>`);
  },

  /* --------------------------------- Modales -------------------------------- */
  shipyard() {
    const G = this.G, c = G.city;
    const list = VEHICLES.filter(v => v.era <= G.p.era && (v.terrain === 'land' || c.shipyard)).map(v => {
      const price = Math.round(v.cost * (1 + c.tax));
      const can = G.p.gold >= price && v.cost > 0;
      return `<div class="opt ${can ? '' : 'dis'}"><span>${v.icon}</span>
        <div class="t"><b>${v.name}</b><small>carga ${v.cap} · velocidad ${v.speed.toFixed(2)} · mant. ${v.up}/día · ${v.terrain === 'sea' ? 'mar' : 'tierra'}</small></div>
        ${v.cost > 0 ? `<button class="btn tiny ${can ? 'primary' : ''}" data-act="buyveh" data-v="${v.id}" ${can ? '' : 'disabled'}>${fmt(price)} ⦿</button>` : '<span class="mini">inicial</span>'}</div>`;
    }).join('');
    this.modal('⚓ ' + (c.shipyard ? 'Astillero y cuadras' : 'Cuadras'),
      `<p class="mini">Oro: ${fmt(G.p.gold)} ⦿ · capacidad tierra ${Math.round(G.capacity('land'))} · mar ${Math.round(G.capacity('sea'))}</p>${list}
       ${c.shipyard ? '' : '<p class="mini">Los barcos solo se compran en ciudades con astillero.</p>'}`);
  },

  bank() {
    const G = this.G;
    const max = Math.max(0, Math.round(G.netWorth() * 0.6 + 500 - G.debt()));
    const opts = [500, 2000, 10000, 50000].filter(n => n <= max).map(n =>
      `<div class="opt"><span>💰</span><div class="t"><b>Préstamo de ${fmt(n)} ⦿</b><small>interés ~0.12% diario</small></div>
      <button class="btn tiny primary" data-act="loan" data-n="${n}">Pedir</button></div>`).join('') || '<div class="mini">El banco no te concede nada más por ahora.</div>';
    const debts = G.p.loans.map((l, i) => `<div class="opt"><span>📜</span><div class="t"><b>${fmt(l.amount)} ⦿</b>
      <small>${(l.rate * 100).toFixed(2)}%/día</small></div>
      <button class="btn tiny" data-act="repay" data-i="${i}" data-n="${Math.ceil(Math.min(l.amount, G.p.gold))}">Pagar ${fmt(Math.min(l.amount, G.p.gold))}</button></div>`).join('');
    this.modal('🏦 Banca de ' + esc(G.city.name),
      `<p class="mini">Oro ${fmt(G.p.gold)} ⦿ · patrimonio ${fmt(G.netWorth())} ⦿ · deuda ${fmt(G.debt())} ⦿</p>
       <h4>Crédito disponible: ${fmt(max)} ⦿</h4>${opts}
       ${debts ? '<h4>Tus deudas</h4>' + debts : ''}`);
  },

  tavern() {
    const G = this.G, c = G.city;
    const rumors = this.rumors();
    this.modal('🍺 Taberna de ' + esc(c.name), `
      <h4>Rumores</h4><ul>${rumors}</ul>
      <h4>Escolta</h4>
      <div class="opt"><span>🛡️</span><div class="t"><b>Contratar guardias</b><small>140 ⦿ cada uno · 2.5 ⦿/día · reducen asaltos. Tienes ${G.p.guards}.</small></div>
        <button class="btn tiny" data-act="guards" data-n="1">+1</button>
        <button class="btn tiny" data-act="guards" data-n="5">+5</button></div>
      <div class="opt"><span>📋</span><div class="t"><b>Seguro de carga</b><small>${G.p.insured ? 'Ya contratado' : 'Cubre parte de las pérdidas por asalto'}</small></div>
        <button class="btn tiny" data-act="insure" ${G.p.insured ? 'disabled' : ''}>${fmt(400 + G.cargoWeight() * 3)} ⦿</button></div>
      <h4>Asuntos turbios</h4>
      <div class="opt"><span>🏴‍☠️</span><div class="t"><b>Emboscar una caravana rival</b>
        <small>Requiere 5+ guardias. Botín alto, reputación por los suelos.</small></div>
        <button class="btn tiny danger" data-act="raid" ${G.p.guards >= 5 ? '' : 'disabled'}>Emboscar</button></div>`);
  },

  rumors() {
    const G = this.G, c = G.city;
    const out = [];
    // eventos conocidos en ciudades cercanas
    const near = G.world.cities.filter(x => x.id !== c.id && dist(x.x, x.y, c.x, c.y) < 55).sort((a, b) => dist(a.x, a.y, c.x, c.y) - dist(b.x, b.y, c.x, c.y));
    for (const x of near) {
      if (out.length >= 5) break;
      if (x.events.length && rnd() < 0.9) {
        const e = x.events[0];
        if (!x.known) { x.known = true; this.V.fogDirty = true; G.world.reveal(x.x, x.y, 5); }
        out.push(`${e.icon} Dicen que en <b>${esc(x.name)}</b> hay ${e.name.toLowerCase()} (${e.daysLeft} días más).`);
      }
    }
    const e2 = G.world.edges.filter(e => e.blocked > 0 || e.danger > 0.18).slice(0, 2);
    for (const e of e2) out.push(`⚠️ La ruta ${esc(G.world.cities[e.a].name)} — ${esc(G.world.cities[e.b].name)} ${e.blocked ? 'está cortada' : 'es peligrosa'}.`);
    if (!out.length) out.push('Nadie sabe nada interesante. Solo cerveza aguada.');
    return out.map(o => `<li>${o}</li>`).join('');
  },

  factoryModal() {
    const G = this.G, c = G.city;
    const list = RECIPES.map(r => {
      const b = G.p.buildings.find(x => x.city === c.id && x.recipe === r.id);
      const cost = Math.round(r.cost * (1 + c.tax) * (b ? Math.pow(1.7, b.level) : 1));
      const ins = Object.keys(r.in).map(g => `${r.in[g]}× ${GOOD[g].icon}${GOOD[g].name}`).join(' + ');
      const outs = Object.keys(r.out).map(g => `${r.out[g]}× ${GOOD[g].icon}${GOOD[g].name}`).join(' + ');
      // margen local estimado
      let cin = 0, cout = 0;
      for (const g in r.in) cin += costToBuy(c, g, r.in[g] * FACTORY_BATCH);
      for (const g in r.out) cout += revenueToSell(c, g, r.out[g] * FACTORY_BATCH);
      const marg = (cout - cin) - 10;
      const can = G.p.gold >= cost;
      return `<div class="opt ${can ? '' : 'dis'}"><span>${r.icon}</span>
        <div class="t"><b>${r.name}${b ? ` · nivel ${b.level}` : ''}</b>
        <small>${ins} → ${outs} · ×${FACTORY_BATCH} lotes/día · margen neto hoy <span class="${marg > 0 ? 'up' : 'down'}">${marg > 0 ? '+' : ''}${fmt(marg)} ⦿/día</span></small></div>
        <button class="btn tiny ${can ? 'primary' : ''}" data-act="build" data-r="${r.id}" ${can ? '' : 'disabled'}>${b ? 'Ampliar' : 'Construir'} ${fmt(cost)}</button></div>`;
    }).join('');
    this.modal('🏭 Talleres de ' + esc(c.name),
      `<p class="mini">Las fábricas compran insumos y venden la producción cada día automáticamente. El margen depende de los precios locales, así que cambia con el mundo.</p>${list}`);
  },

  warehouseModal() {
    const G = this.G, c = G.city, w = G.p.warehouses[c.id];
    if (!w) {
      this.modal('📦 Almacén', `<p>No tienes almacén en ${esc(c.name)}. Un almacén te permite guardar mercancía y especular sin cargarla.</p>
        <div class="opt"><span>📦</span><div class="t"><b>Construir almacén</b><small>350 de capacidad</small></div>
        <button class="btn tiny primary" data-act="buildwh">3.000 ⦿</button></div>`);
      return;
    }
    let used = 0; for (const g in w.stock) used += w.stock[g] * GOOD[g].w;
    const rows = Object.keys(w.stock).map(g => `<div class="opt"><span>${GOOD[g].icon}</span>
      <div class="t"><b>${GOOD[g].name} ×${Math.floor(w.stock[g])}</b><small>valor local ${fmt(sellPriceAt(c, g) * w.stock[g])} ⦿</small></div></div>`).join('') || '<div class="mini">Vacío.</div>';
    this.modal('📦 Almacén de ' + esc(c.name),
      `<p class="mini">Ocupado ${Math.round(used)}/${w.cap}. Mueve mercancía desde la tabla del mercado.</p>${rows}
       <div class="opt"><span>➕</span><div class="t"><b>Ampliar almacén</b><small>+350 de capacidad</small></div>
       <button class="btn tiny primary" data-act="buildwh">2.200 ⦿</button></div>`);
  },

  help() {
    this.modal('Cómo se juega', `
      <p>Eres un comerciante. Compra barato, vende caro… pero el mundo no se queda quieto: guerras, pestes, minas y ferias mueven los precios cada día.</p>
      <h4>Lo básico</h4>
      <ul>
        <li><b>Mercado</b>: pulsa un bien para desplegar la compra/venta, su histórico y dónde recuerdas mejores precios.</li>
        <li><b>Mapa</b>: arrastra para moverte, rueda para zoom. Pulsa una ciudad y luego <i>Viajar</i>.</li>
        <li><b>Recuerdas los precios</b> de las ciudades que visitas: cuanto más viejo el dato, menos fiable.</li>
        <li><b>Niebla</b>: explora o compra mapas para descubrir ciudades nuevas.</li>
      </ul>
      <h4>Crecer</h4>
      <ul>
        <li>Compra mulas, carretas y barcos: más capacidad y más velocidad.</li>
        <li>Construye <b>talleres</b> (trigo → harina → pan) que generan ingresos cada día.</li>
        <li>Acepta <b>contratos</b> con plazo para ganancias seguras.</li>
        <li>Usa el <b>banco</b> para apalancarte… con cuidado con los intereses.</li>
      </ul>
      <h4>Otros caminos</h4>
      <ul>
        <li><b>Contrabando</b>: los bienes prohibidos se pagan un 85% más, pero pueden confiscarte la carga.</li>
        <li><b>Corsario</b>: con 5+ guardias puedes emboscar caravanas rivales.</li>
        <li><b>Especulador</b>: compra todo el stock de un bien y estrangula la oferta local.</li>
      </ul>
      <p class="mini">Atajos: espacio = esperar 1 día · M/C/I/W = pestañas.</p>`);
  },
};
