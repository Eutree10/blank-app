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
      case 'good': {
        this.openGood = this.openGood === d.g ? null : d.g;
        const g = this.openGood;
        if (g) this.groupOpen[GOOD[g].tier] = true;      // que no quede oculto tras un grupo plegado
        this.selectTab('market');
        this.renderMarket();
        if (g) {
          const row = $('pane-market').querySelector(`tr.g[data-g="${g}"]`);
          if (row) row.scrollIntoView({ block: 'nearest' });
        }
        break;
      }
      case 'grp': this.groupOpen[d.t] = !this.groupOpen[d.t]; this.renderMarket(); break;
      case 'cargo': this.cargoModal(d.g); break;
      case 'sheet': this.goodSheet(d.g); break;
      case 'cq': this.setCargoQty(d.v); break;
      case 'cqsell': this.cargoSell(); break;
      case 'cqstore': this.cargoStore(); break;
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
    $('tNet').textContent = '≈ ' + fmt(G.netWorth()) + (G.debt() ? ' (deuda ' + fmt(G.debt()) + ')' : '');
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
      return `<div class="li click" data-act="cargo" data-g="${g}" title="Vender o guardar ${GOOD[g].name}">
        <span class="ic">${GOOD[g].icon}</span>
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
  /** Datos de una fila de mercado: precio, desviación sobre la media y contexto. */
  goodRow(g) {
    const G = this.G, c = G.city, good = GOOD[g];
    const banned = !!c.banned[g];
    const bp = buyPriceAt(c, g);
    const sp = sellPriceAt(c, g) * (banned ? 1.85 : 1 - taxP(c));
    const dev = (banned ? sp : bp) / good.base - 1;       // cuánto se aleja de lo que vale normalmente
    const trend = c.price[g] - (c.lastPrice[g] || c.price[g]);
    return {
      g, good, banned, bp, sp, dev,
      mine: Math.floor(G.p.cargo[g] || 0),
      stock: Math.floor(c.stock[g]),
      cheap: !banned && dev < -0.18,
      dear: dev > 0.35,
      trend: trend > 0.02 ? 1 : trend < -0.02 ? -1 : 0,
    };
  },

  renderMarket() {
    const G = this.G, c = G.city;
    const filters = [['all', 'Todo'], ['0', 'Materias'], ['1', 'Elaborados'], ['2', 'Manufacturas'], ['mine', 'Mi bodega'], ['deal', 'Gangas']];
    if (!this.groupOpen) this.groupOpen = { 0: true, 1: true, 2: true };

    const all = GOODS.map(x => this.goodRow(x.id));
    const visible = all.filter(r => {
      if (this.filter === 'mine') return r.mine > 0;
      if (this.filter === 'deal') return r.cheap || (r.mine > 0 && this.bestSellDelta(r.g) > 0.12);
      if (this.filter === '0' || this.filter === '1' || this.filter === '2') return String(r.good.tier) === this.filter;
      return true;
    });

    // --- destacado: lo más barato de la plaza, con destino sugerido
    let deals = '';
    if (this.filter === 'all' || this.filter === 'deal') {
      const best = all.filter(r => r.cheap && r.stock > 8).sort((a, b) => a.dev - b.dev).slice(0, 3);
      if (best.length) {
        deals = `<div class="deals">
          <h4>Barato aquí <span class="mini">precio muy por debajo de lo normal</span></h4>
          ${best.map(r => {
            const to = this.bestMarketFor(r.g);
            return `<button class="dealcard" data-act="good" data-g="${r.g}">
              <span class="di">${r.good.icon}</span>
              <span class="dn">${r.good.name}<small>${to ? `→ ${esc(to.city.name)} ${to.days}d · ${pct(to.margin)}` : 'aún no sabes dónde venderlo caro'}</small></span>
              <span class="dp">${fmt(r.bp)} ⦿<small class="up">${pct(r.dev)}</small><small class="flat">la unidad</small></span>
            </button>`;
          }).join('')}
        </div>`;
      }
    }

    // --- lo que llevas, para venderlo sin buscarlo
    let hold = '';
    const carried = all.filter(r => r.mine > 0);
    if (carried.length && this.filter !== 'mine') {
      hold = `<div class="deals hold">
        <h4>En tu bodega <span class="mini">pulsa para vender</span></h4>
        ${carried.map(r => {
          const avg = G.p.avgCost && G.p.avgCost[r.g] && G.p.avgCost[r.g].n > 0 ? G.p.avgCost[r.g].total / G.p.avgCost[r.g].n : null;
          const prof = avg === null ? null : (r.sp - avg) / avg;
          const nota = prof === null ? 'vendiendo aquí'
            : (prof >= 0 ? 'ganarías ' : 'perderías ') + Math.round(Math.abs(prof) * 100) + '% sobre lo que pagaste';
          return `<button class="dealcard" data-act="cargo" data-g="${r.g}">
            <span class="di">${r.good.icon}</span>
            <span class="dn">${r.good.name} <b>×${r.mine}</b><small>${nota}</small></span>
            <span class="dp ${prof === null ? '' : prof >= 0 ? 'up' : 'down'}">${fmt(r.sp * r.mine)} ⦿</span>
          </button>`;
        }).join('')}
      </div>`;
    }

    // --- tabla agrupada por categoría
    const TIERS = [
      { t: 0, name: 'Materias primas', hint: 'de la tierra y el mar' },
      { t: 1, name: 'Elaborados', hint: 'pasan por un taller' },
      { t: 2, name: 'Manufacturas y lujo', hint: 'lo que más margen deja' },
    ];
    const grouped = this.filter === 'all';
    let rows = '';
    const rowHtml = r => {
      const tag = r.banned ? '<span class="pill">proh.</span>' : '';
      return `<tr class="g ${this.openGood === r.g ? 'sel' : ''} ${r.cheap ? 'isdeal' : ''}" data-act="good" data-g="${r.g}">
        <td><span class="gname"><span class="gi">${r.good.icon}</span><span class="gt">${r.good.name}</span>${tag}</span></td>
        <td class="${r.cheap ? 'up strong' : ''}">${r.banned ? '—' : fmt(r.bp)}</td>
        <td class="${r.dear ? 'down' : ''}">${fmt(r.sp)}</td>
        <td class="dev ${r.dev < -0.18 ? 'up' : r.dev > 0.35 ? 'down' : 'flat'}">${pct(r.dev)}</td>
        <td class="${r.mine ? '' : 'flat'}">${r.mine || '–'}</td>
        <td class="${r.trend > 0 ? 'up' : r.trend < 0 ? 'down' : 'flat'}">${r.trend > 0 ? '▲' : r.trend < 0 ? '▼' : '·'}</td></tr>`
        + (this.openGood === r.g ? this.tradeRow(r.g) : '');
    };

    if (grouped) {
      for (const T of TIERS) {
        const list = visible.filter(r => r.good.tier === T.t);
        if (!list.length) continue;
        const nDeals = list.filter(r => r.cheap).length;
        const open = this.groupOpen[T.t];
        rows += `<tr class="grp" data-act="grp" data-t="${T.t}"><td colspan="6"><span class="gh">
          <span class="caret">${open ? '▾' : '▸'}</span>
          <span class="gtitle">${T.name}</span>
          <span class="mini">${T.hint} · ${list.length}</span>
          ${nDeals ? `<span class="pill deal">${nDeals} barato${nDeals > 1 ? 's' : ''}</span>` : ''}
        </span></td></tr>`;
        if (open) rows += list.map(rowHtml).join('');
      }
    } else {
      rows = visible.map(rowHtml).join('');
    }

    $('pane-market').innerHTML = `
      <div class="mkt-head">
        <div><h2>${esc(c.name)}</h2>
        <div class="where">${CITY_TRAIT[c.trait] ? CITY_TRAIT[c.trait].icon + ' ' + CITY_TRAIT[c.trait].name + ' · ' : ''}${fmt(c.pop)} hab · impuesto ${(taxP(c) * 100).toFixed(1)}%</div></div>
      </div>
      ${G.vetoed(c) ? '<div class="warnbox">⛔ <b>Te han vetado en esta ciudad.</b> No te compran ni te venden nada. Gánate su perdón entregando contratos en otras plazas… o no vuelvas.</div>' : ''}
      <div class="filters">
        ${filters.map(f => `<button data-f="${f[0]}" class="${this.filter === f[0] ? 'active' : ''}">${f[1]}</button>`).join('')}
        <button class="viewtog" id="btnStalls">${this.stallView ? '☰ Ver tabla' : '🏪 Ver puestos'}</button>
      </div>
      ${deals}${hold}
      ${this.stallView ? `<div class="stalls">${this.renderStalls(all)}</div>` : ''}
      <table class="mkt" ${this.stallView ? 'style="display:none"' : ''}>
        <colgroup><col class="c-name"><col class="c-num"><col class="c-num"><col class="c-num"><col class="c-mine"><col class="c-tr"></colgroup>
        <thead><tr><th>Bien</th>
          <th title="Lo que pagas tú por cada unidad que compras aquí">Cuesta</th>
          <th title="Lo que recibes tú por cada unidad que vendes aquí">Pagan</th>
          <th title="Diferencia con lo que suele valer este bien"><span class="thl">vs normal</span><span class="ths">±%</span></th>
          <th title="Unidades que llevas en la bodega">Tuyo</th><th></th></tr></thead>
        <tbody>${rows || '<tr><td colspan="6" class="mini" style="padding:14px">Nada que mostrar con este filtro.</td></tr>'}</tbody>
      </table>`;
    $('pane-market').querySelectorAll('.filters button[data-f]').forEach(b => b.onclick = e => {
      e.stopPropagation(); this.filter = b.dataset.f; this.renderMarket();
    });
    const tog = $('btnStalls');
    if (tog) tog.onclick = e => { e.stopPropagation(); this.stallView = !this.stallView; this.renderMarket(); };
  },

  /* ------------------------- El mercado por puestos ------------------------ */
  STALLS: [
    { name: 'Granero', icon: '🌾', goods: ['grano', 'harina', 'pan'] },
    { name: 'Pescadería', icon: '🐟', goods: ['pescado', 'sal'] },
    { name: 'Maderero', icon: '🪵', goods: ['madera', 'tablones', 'muebles'] },
    { name: 'Fragua', icon: '🔩', goods: ['mineral', 'carbon', 'hierro', 'herram', 'espadas', 'armadura'] },
    { name: 'Telares', icon: '🧵', goods: ['lana', 'pieles', 'tela', 'cuero', 'ropa'] },
    { name: 'Especiero', icon: '🌶️', goods: ['especias', 'hierbas', 'incienso', 'medicina'] },
    { name: 'Bodega', icon: '🍷', goods: ['uva', 'vino'] },
    { name: 'Joyería', icon: '💎', goods: ['gemas', 'joyas'] },
    { name: 'Cantera', icon: '🪨', goods: ['piedra'] },
  ],

  stallKeeper(c, stall) {
    const h = hashStr(c.name + stall.name);
    return MERCH_FIRST[h % MERCH_FIRST.length] + ' ' + MERCH_LAST[(h >> 5) % MERCH_LAST.length];
  },
  stallLine(c, rows) {
    const cheap = rows.find(r => r.cheap), dear = rows.find(r => r.dear);
    const crisis = c.events.find(e => ['hambruna', 'peste', 'guerra', 'sequia'].includes(e.id));
    if (crisis && rows.some(r => GOOD[r.g].tag === 'alimento' || GOOD[r.g].tag === 'medicina'))
      return `«Con esto de ${crisis.name.toLowerCase()}, lo que traigas se vende solo.»`;
    if (cheap) return `«Me sobra ${GOOD[cheap.g].name.toLowerCase()}, llévatelo casi regalado.»`;
    if (dear) return `«De ${GOOD[dear.g].name.toLowerCase()} queda poco, y lo que queda se paga.»`;
    return '«Precio de siempre, ni un cobre menos.»';
  },

  renderStalls(all) {
    const G = this.G, c = G.city;
    return this.STALLS.map(st => {
      const rows = st.goods.map(g => all.find(r => r.g === g)).filter(Boolean);
      if (!rows.length) return '';
      return `<div class="stall">
        <div class="stallhead">
          <span class="si">${st.icon}</span>
          <div class="sn"><b>${st.name}</b><small>${esc(this.stallKeeper(c, st))}</small></div>
        </div>
        <div class="stallsay">${this.stallLine(c, rows)}</div>
        <div class="stallgoods">
          ${rows.map(r => `<button class="sg ${r.cheap ? 'cheap' : ''} ${r.dear ? 'dear' : ''}" data-act="good" data-g="${r.g}">
            <span class="sgi">${r.good.icon}</span>
            <span class="sgn">${r.good.name}</span>
            <span class="sgp">${r.banned ? '🕯️' : fmt(r.bp)}<small class="${r.dev < -0.18 ? 'up' : r.dev > 0.35 ? 'down' : 'flat'}">${pct(r.dev)}</small></span>
            ${r.mine ? `<span class="sgm">llevas ${r.mine}</span>` : ''}
          </button>`).join('')}
        </div>
      </div>`;
    }).join('');
  },

  /** Mejor mercado recordado para un bien, con margen y distancia. */
  bestMarketFor(g) {
    const G = this.G, mem = G.p.memory || {};
    const bp = buyPriceAt(G.city, g);
    let best = null;
    for (const cid in mem) {
      if (+cid === G.p.at) continue;
      const city = G.world.cities[cid], sell = mem[cid].price[g];
      if (!city || !sell) continue;
      const margin = (sell - bp) / bp;
      if (margin < 0.08) continue;
      const r = G.routeTo(city.id);
      if (!r) continue;
      const days = Math.max(1, Math.round(r.days));
      if (!best || margin / days > best.margin / best.days) best = { city, margin, days };
    }
    return best;
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
        <span class="mini">cabe ${max} · hay ${fmt(c.stock[g])} en plaza</span>
      </div>
      <div class="qty">
        <button class="btn tiny primary" data-act="buy" data-g="${g}" ${c.banned[g] ? 'disabled' : ''}>Comprar</button>
        <button class="btn tiny" data-act="sell" data-g="${g}" ${mine ? '' : 'disabled'}>Vender</button>
        <button class="btn tiny" data-act="sellmax" data-g="${g}" ${mine ? '' : 'disabled'}>Vender todo (${mine})</button>
        ${wh ? `<button class="btn tiny ghost" data-act="store" data-g="${g}" ${mine ? '' : 'disabled'}>→ Almacén</button>
                <button class="btn tiny ghost" data-act="take" data-g="${g}" ${(wh.stock[g] || 0) ? '' : 'disabled'}>← Almacén (${Math.floor(wh.stock[g] || 0)})</button>` : ''}
      </div>
      ${c.banned[g] ? `<div class="mini" style="color:#f3b2ae">Prohibido aquí: no se compra, y venderlo da un +85% con un
        <b>${Math.round(G.smuggleRisk(c) * 100)}% de riesgo</b> de que te confisquen la carga.</div>` : ''}
      <div>
        <div class="mini" style="margin-bottom:5px">Qué pasa con ${GOOD[g].name} en las plazas que conoces</div>
        ${this.marketMiniTable(g, 5)}
      </div>
      <button class="btn tiny wide" data-act="sheet" data-g="${g}">📊 Ficha completa y mejor operación</button>
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

  /** Tabla compacta: qué te pagan y qué te cuesta el bien en cada plaza que recuerdas. */
  marketMiniTable(g, limit) {
    const G = this.G;
    const mk = this.marketsFor(g).sort((a, b) => (b.sell || 0) - (a.sell || 0));
    if (mk.length < 2) return '<div class="mini">Solo conoces este mercado. Viaja para poder comparar.</div>';
    const bestSell = Math.max(...mk.map(m => m.sell || 0));
    const rows = mk.slice(0, limit).map(m => `
      <tr class="${m.here ? 'here' : ''}" ${m.here ? '' : `data-act="select-city" data-city="${m.city.id}" style="cursor:pointer"`}>
        <td>${m.here ? '<b>Aquí</b>' : esc(m.city.name)}${m.banned ? ' 🕯️' : ''}</td>
        <td class="${m.sell === bestSell ? 'gold strong' : ''}">${m.sell ? fmt(m.sell) : '—'}</td>
        <td class="flat">${m.buy > 0 ? fmt(m.buy) : '—'}</td>
        <td class="mini">${m.here ? '—' : m.days === null ? 'sin ruta' : m.days + 'd'}</td>
        <td class="mini ${m.age > 45 ? 'stale' : ''}">${m.here ? 'ahora' : m.age + 'd'}</td>
      </tr>`).join('');
    return `<table class="sheet compact">
      <thead><tr>
        <th>Plaza</th>
        <th title="Lo que recibes por cada unidad que vendes allí">Te pagan</th>
        <th title="Lo que te costaría cada unidad si la compras allí">Te cuesta</th>
        <th>Viaje</th><th title="Antigüedad del dato">Dato</th>
      </tr></thead><tbody>${rows}</tbody></table>
      <div class="mini">Precios <b>por unidad</b>. Los de otras plazas son los que viste al pasar por allí.</div>`;
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
    const cur = sellPriceAt(here, g) * (here.banned[g] ? 1.85 : 1 - taxP(here));
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
    const cur = sellPriceAt(c, g) * (c.banned[g] ? 1.85 : 1 - taxP(c));
    let best = cur;
    for (const cid in mem) if (mem[cid].price[g]) best = Math.max(best, mem[cid].price[g]);
    return (best - cur) / cur;
  },

  /* -------------------------------- Ciudad --------------------------------- */
  renderCity() {
    const G = this.G, c = G.city;
    const T = CITY_TRAIT[c.trait];
    const st = standing(c);
    const mem = (c.memories || []).slice(0, 4);
    const evs = c.events.map(e => `<span class="evtag ${['guerra', 'peste', 'hambruna', 'sequia', 'erupcion', 'revolucion', 'impuestos', 'minaagotada', 'plagaganado'].includes(e.id) ? 'bad' : 'good'}">${e.icon} ${e.name} · ${e.daysLeft}d</span>`).join('') || '<span class="mini">Sin sucesos activos.</span>';
    const sp = c.specialties.map(s => `<span class="evtag">${SPECIALTY[s].icon} ${SPECIALTY[s].name}</span>`).join('');
    const banned = Object.keys(c.banned);
    const ks = c.contracts.map(k => {
      const to = G.world.cities[k.to];
      const have = Math.floor(G.p.cargo[k.good] || 0);
      if (k.mega) {
        return `<div class="opt mega">
          <span>👑</span>
          <div class="t"><b>Gran encargo: ${fmt(k.qty)} de ${GOOD[k.good].name} ${GOOD[k.good].icon}</b>
          <small>${k.what} · ${k.days} días · paga <b>${fmt(k.reward)} ⦿</b> · se entrega por partes</small></div>
          <button class="btn tiny primary" data-act="accept" data-k="${k.id}">Aceptar</button></div>`;
      }
      return `<div class="opt">
        <span>${GOOD[k.good].icon}</span>
        <div class="t"><b>${k.qty}× ${GOOD[k.good].name} → ${esc(to.name)}</b>
        <small>${k.days} días · paga ${fmt(k.reward)} ⦿ · multa ${fmt(k.penalty)} ⦿ · llevas ${have}</small></div>
        <button class="btn tiny primary" data-act="accept" data-k="${k.id}">Aceptar</button></div>`;
    }).join('') || '<div class="mini">No hay contratos ahora mismo.</div>';
    const deliver = G.p.contracts.filter(k => k.to === c.id).map(k => {
      const have = Math.floor(G.p.cargo[k.good] || 0);
      if (k.mega) {
        const p = clamp(k.delivered / k.qty, 0, 1) * 100;
        return `<div class="opt mega"><span>👑</span><div class="t">
          <b>Gran encargo: ${GOOD[k.good].icon} ${GOOD[k.good].name}</b>
          <small>${fmt(k.delivered)} de ${fmt(k.qty)} entregados · llevas ${have} · quedan ${k.deadline - G.day} días</small>
          <div class="prog"><div class="prog-fill" style="width:${p}%"></div></div></div>
          <button class="btn tiny primary" data-act="deliver" data-k="${k.id}" ${have > 0 ? '' : 'disabled'}>Descargar ${have}</button></div>`;
      }
      return `<div class="opt"><span>${GOOD[k.good].icon}</span><div class="t"><b>Entregar ${k.qty}× ${GOOD[k.good].name}</b>
      <small>llevas ${have} · paga ${fmt(k.reward)} ⦿ · ${k.deadline - G.day} días</small></div>
      <button class="btn tiny primary" data-act="deliver" data-k="${k.id}" ${(G.p.cargo[k.good] || 0) >= k.qty ? '' : 'disabled'}>Entregar</button></div>`;
    }).join('');

    $('pane-city').innerHTML = `
      ${T ? `<div class="traitbox">
        <div class="traithead"><span class="ti">${T.icon}</span><b>${T.name}</b></div>
        <p>${T.expect}</p>
      </div>` : ''}
      <div class="block">
        <h3>${esc(c.name)}</h3>
        <div class="kv"><span>Población</span><b>${fmt(c.pop)}</b></div>
        <div class="kv"><span>Riqueza</span><b>${(c.wealth * 100).toFixed(0)}</b></div>
        <div class="kv"><span>Impuesto para ti</span><b>${(taxP(c) * 100).toFixed(1)}%${Math.abs(taxP(c) - c.tax) > 0.002 ? ` <span class="mini">(normal ${(c.tax * 100).toFixed(1)}%)</span>` : ''}</b></div>
        <div class="kv"><span>Descontento</span><b class="${c.unrest > 0.5 ? 'down' : ''}">${(c.unrest * 100).toFixed(0)}%</b></div>
        <div class="kv"><span>Cómo te ven aquí</span><b class="${st.color}">${st.icon} ${st.name} (${(c.playerRep || 0).toFixed(0)})</b></div>
        <div class="evrow" style="margin-top:8px">${sp}</div>
        ${banned.length ? `<div class="mini">Prohibido: ${banned.map(b => GOOD[b].icon + ' ' + GOOD[b].name).join(', ')} · te pillarían con un ${Math.round(G.smuggleRisk(c) * 100)}% de probabilidad</div>` : ''}
      </div>
      ${mem.length ? `<div class="block"><h3>Lo que recuerdan de ti</h3>
        ${mem.map(m => `<div class="memline"><span class="mq">«${esc(m.text)}»</span><span class="mini">${yearsAgo(G, m.day)}</span></div>`).join('')}
      </div>` : ''}
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

    const role = fameRole(p);
    const fameRows = FAME_KINDS.filter(f => (p.fame || {})[f.id] > 0)
      .sort((a, b) => p.fame[b.id] - p.fame[a.id])
      .map(f => {
        const v = p.fame[f.id];
        const lvl = clamp(Math.floor(Math.log(v / 6) / Math.log(2.4)) + 1, 0, 5);
        return `<div class="famerow"><span class="fi">${f.icon}</span>
          <span class="fn">${f.name}<small>${f.desc}</small></span>
          <span class="fs">${fameStars(lvl)}</span></div>`;
      }).join('') || '<div class="mini">Todavía nadie habla de ti. Comercia, cumple contratos… o rompe alguna ley.</div>';
    const mines = (p.mines || []).length;

    $('pane-empire').innerHTML = `
      <div class="block fameblock">
        <h3>Tu fama</h3>
        <div class="famehead"><span class="bigicon">${role.icon}</span>
          <div><b>${role.name}</b><div class="stars">${fameStars(role.level)}</div>
          <div class="mini">${role.desc}</div></div></div>
        ${fameRows}
      </div>
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
      ${mines ? `<div class="block"><h3>Minas propias</h3>
        <div class="opt"><span>⛏️</span><div class="t"><b>${mines} mina${mines > 1 ? 's' : ''} en explotación</b>
        <small>Rinden mineral y gemas cada mes; se venden solas en la ciudad más cercana.</small></div></div></div>` : ''}
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

    const we = G.worldEvent;
    const weBlock = we ? `<div class="worldev">
      <div class="wehead"><span class="wi">${we.icon}</span><b>${we.name}</b><span class="mini">${we.daysLeft} días</span></div>
      <p>${esc(we.line)}</p>
      <div class="mini">${esc(we.aside)} · Afecta a ${we.cities.length} ciudades.</div>
      <div class="prog"><div class="prog-fill" style="width:${100 - clamp(we.daysLeft / we.total, 0, 1) * 100}%"></div></div>
    </div>` : '';

    $('pane-world').innerHTML = `
      ${weBlock}
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
    const T = CITY_TRAIT[c.trait];
    const st = standing(c);
    el.innerHTML = `<h4>${esc(c.name)}</h4>
      <div class="meta">${BIOMES[c.biome].name} · ${c.visited ? fmt(c.pop) + ' hab' : 'sin visitar'} ${c.coastal ? '· puerto' : ''}</div>
      ${T && c.visited ? `<div class="traitmini">${T.icon} <b>${T.name}</b> — ${T.expect}</div>` : ''}
      ${c.visited && st.id !== 'neutral' ? `<div class="kv"><span>Te ven como</span><b class="${st.color}">${st.icon} ${st.name}</b></div>` : ''}
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
    if (G.pendingWorldNews) { const w = G.pendingWorldNews; G.pendingWorldNews = null; this.worldEventModal(w, () => this.arrivalModal(res)); return; }
    this.arrivalModal(res);
  },

  arrivalModal(res) {
    const G = this.G, c = G.city;
    const T = CITY_TRAIT[c.trait];
    const greet = cityGreeting(G, c);
    const changes = this.priceHighlights(c);
    const sites = (res.sites || []).map(s => `<li><b>${s.def.icon} ${s.def.name}</b> — ${s.def.text}
      ${s.gold ? `<b class="up">+${fmt(s.gold)} ⦿</b>` : ''}
      ${Object.keys(s.goods || {}).length ? '· ' + Object.keys(s.goods).map(g => `${s.goods[g]} ${GOOD[g].name}`).join(', ') : ''}
      ${s.def.text2 ? `<br><span class="mini">${s.def.text2}</span>` : ''}</li>`).join('');
    const body = `
      <p>Llegas a <b>${esc(c.name)}</b> tras <b>${res.days} días</b> de camino.</p>
      ${greet ? `<div class="greet">${esc(greet)}</div>` : ''}
      ${T ? `<div class="traitmini">${T.icon} <b>${T.name}</b> — ${T.expect}</div>` : ''}
      ${sites ? `<h4>Hallazgos del camino</h4><ul>${sites}</ul>` : ''}
      ${res.log.length ? '<h4>En el camino</h4><ul>' + res.log.map(l => `<li>${l}</li>`).join('') + '</ul>' : ''}
      ${c.events.length ? '<h4>Situación</h4><div class="evrow">' + c.events.map(e => `<span class="evtag">${e.icon} ${e.name} · ${e.daysLeft}d</span>`).join('') + '</div>' : ''}
      <h4>Mercado</h4>${changes}`;
    this.modal(`${c.events.length ? c.events[0].icon + ' ' : '🏙️ '}${esc(c.name)}`, body,
      '<button class="btn primary" data-act="modal-close">Al mercado</button>');
  },

  /** Un gran acontecimiento merece su propia pantalla. */
  worldEventModal(w, then) {
    const G = this.G;
    const names = w.cities.map(id => G.world.cities[id]).filter(c => c.known).slice(0, 8).map(c => esc(c.name));
    this.modal(`${w.icon} ${w.name}`, `
      <div class="worldev big">
        <p class="lead">${esc(w.line)}</p>
        <p>${esc(w.aside)}</p>
        <div class="mini">Durará unos <b>${Math.round(w.daysLeft / 30)} meses</b> y alcanza a <b>${w.cities.length} ciudades</b>${names.length ? `, entre ellas ${names.join(', ')}` : ''}.</div>
      </div>`, '<button class="btn primary" id="weOk">Seguir</button>');
    const btn = $('weOk');
    if (btn) btn.onclick = () => { this.closeModal(); if (then) setTimeout(then, 120); };
  },

  priceHighlights(c) {
    const G = this.G;
    const list = GOODS.map(good => {
      const g = good.id;
      const bp = buyPriceAt(c, g), ratio = bp / good.base;
      return {
        g, good, bp, ratio, mine: Math.floor(G.p.cargo[g] || 0),
        sp: sellPriceAt(c, g) * (c.banned[g] ? 1.85 : 1 - taxP(c)), banned: !!c.banned[g],
      };
    });
    const cheap = list.filter(x => x.ratio < 0.8 && !x.banned).sort((a, b) => a.ratio - b.ratio).slice(0, 4);
    const dear = list.filter(x => x.ratio > 1.3).sort((a, b) => b.ratio - a.ratio).slice(0, 4);

    // lo que llevas: precio por unidad, total y ganancia clara frente a lo pagado
    const carried = list.filter(x => x.mine > 0);
    let sellTable = '';
    if (carried.length) {
      let totalGain = 0, known = false;
      const rows = carried.map(x => {
        const ac = G.p.avgCost && G.p.avgCost[x.g] && G.p.avgCost[x.g].n > 0 ? G.p.avgCost[x.g].total / G.p.avgCost[x.g].n : null;
        const total = x.sp * x.mine;
        const gain = ac === null ? null : total - ac * x.mine;
        if (gain !== null) { totalGain += gain; known = true; }
        return `<tr>
          <td>${x.good.icon} ${x.good.name}${x.banned ? ' <span class="pill">proh.</span>' : ''}</td>
          <td>${x.mine}</td>
          <td>${fmt(x.sp)}</td>
          <td class="strong">${fmt(total)}</td>
          <td class="${gain === null ? 'flat' : gain >= 0 ? 'up' : 'down'}">${gain === null ? '—' : (gain >= 0 ? '+' : '') + fmt(gain)}</td>
          <td><button class="btn tiny" data-act="cargo" data-g="${x.g}">Vender</button></td>
        </tr>`;
      }).join('');
      sellTable = `<h4>Lo que llevas, vendido aquí</h4>
        <table class="sheet">
          <thead><tr><th>Bien</th><th>Llevas</th><th title="Lo que te pagan por cada unidad">Te pagan/u</th><th title="Total por todas las unidades, ya sin impuestos">Total</th><th title="Frente a lo que pagaste por esa mercancía">Ganas</th><th></th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
        <div class="mini">«Total» es lo que recibes por todas las unidades, ya con impuestos descontados. «Ganas» lo compara con lo que pagaste por esa mercancía.
        ${known ? `En conjunto, vender todo aquí te deja <b class="${totalGain >= 0 ? 'up' : 'down'}">${totalGain >= 0 ? '+' : ''}${fmt(totalGain)} ⦿</b>.` : ''}</div>`;
    }

    return `<div class="grid2">
      <div><b>Barato para comprar</b><ul>${cheap.map(x => `<li>${x.good.icon} ${x.good.name} · ${fmt(x.bp)} ⦿ <span class="up">${pct(x.ratio - 1)}</span></li>`).join('') || '<li class="mini">nada destacable</li>'}</ul></div>
      <div><b>Se paga caro</b><ul>${dear.map(x => `<li>${x.good.icon} ${x.good.name} · ${fmt(x.sp)} ⦿ <span class="down">${pct(x.ratio - 1)}</span></li>`).join('') || '<li class="mini">nada destacable</li>'}</ul></div>
    </div>${sellTable}`;
  },

  recordMemory() {
    const G = this.G, c = G.city;
    if (!G.p.memory) G.p.memory = {};
    const price = {}, buy = {};   // lo que cobrarías y lo que te costaría aquí
    for (const g of GOOD_IDS) {
      price[g] = sellPriceAt(c, g) * (c.banned[g] ? 1.85 : 1 - taxP(c));
      buy[g] = c.banned[g] ? 0 : buyPriceAt(c, g);   // 0 = no se vende abiertamente
    }
    G.p.memory[c.id] = { day: G.day, price, buy };
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

  /* ------------------- Ficha de un bien: dónde comprar y vender ------------- */
  /** Todos los mercados que recuerdas para un bien, con ruta y antigüedad. */
  marketsFor(g) {
    const G = this.G, mem = G.p.memory || {};
    const out = [];
    for (const cid in mem) {
      const city = G.world.cities[cid], m = mem[cid];
      if (!city) continue;
      const here = +cid === G.p.at;
      const r = here ? null : G.routeTo(city.id);
      out.push({
        city, here,
        buy: here ? (city.banned[g] ? 0 : buyPriceAt(city, g)) : (m.buy ? m.buy[g] : 0),
        sell: here ? sellPriceAt(city, g) * (city.banned[g] ? 1.85 : 1 - taxP(city)) : m.price[g],
        age: here ? 0 : G.day - m.day,
        days: here ? 0 : (r ? Math.max(1, Math.round(r.days)) : null),
        banned: !!city.banned[g],
      });
    }
    return out;
  },

  goodSheet(g) {
    const G = this.G, c = G.city, good = GOOD[g];
    const mk = this.marketsFor(g);
    const cheapest = mk.filter(m => m.buy > 0).sort((a, b) => a.buy - b.buy)[0];
    const dearest = mk.filter(m => m.sell > 0).sort((a, b) => b.sell - a.sell)[0];

    // mejor operación partiendo de aquí: comprar ahora y vender donde recuerdas
    let best = null;
    if (!c.banned[g] && c.stock[g] > 4) {
      const bp = buyPriceAt(c, g);
      const cap = Math.max(G.capacity('land'), G.capacity('sea'));
      const space = Math.floor((cap - G.cargoWeight()) / good.w);
      for (const m of mk) {
        if (m.here || !m.sell || m.days === null) continue;
        const qty = Math.min(space, G.maxBuy(g), Math.floor(c.stock[g] * 0.6));
        if (qty < 1) continue;
        const cost = costToBuy(c, g, qty);
        const gain = m.sell * qty - cost;
        if (gain <= 0) continue;
        const perDay = gain / m.days;
        if (!best || perDay > best.perDay) best = { m, qty, cost, gain, perDay };
      }
    }

    const risk = c.banned[g] ? G.smuggleRisk(c) : null;
    const dev = buyPriceAt(c, g) / good.base - 1;

    const rows = mk.sort((a, b) => (b.sell || 0) - (a.sell || 0)).map(m => `
      <tr class="${m.here ? 'here' : ''}">
        <td>${m.here ? '<b>Aquí</b> · ' : ''}${esc(m.city.name)}${m.banned ? ' <span class="pill">proh.</span>' : ''}</td>
        <td class="${cheapest && m.city.id === cheapest.city.id ? 'up strong' : ''}">${m.buy > 0 ? fmt(m.buy) : '—'}</td>
        <td class="${dearest && m.city.id === dearest.city.id ? 'gold strong' : ''}">${m.sell ? fmt(m.sell) : '—'}</td>
        <td class="mini">${m.here ? '—' : m.days === null ? 'sin ruta' : m.days + 'd'}</td>
        <td class="mini ${m.age > 45 ? 'stale' : ''}" ${m.age > 45 ? 'title="Dato antiguo: el precio ha podido cambiar mucho"' : ''}>${m.here ? 'ahora' : 'hace ' + m.age + 'd'}</td>
      </tr>`).join('');

    this.modal(`${good.icon} ${good.name}`, `
      <div class="sheet-top">
        <div class="sheet-cell"><label>Precio normal</label><b>${fmt(good.base)} ⦿</b></div>
        <div class="sheet-cell"><label>Aquí te cuesta</label><b class="${dev < -0.18 ? 'up' : ''}">${c.banned[g] ? '—' : fmt(buyPriceAt(c, g)) + ' ⦿'}</b></div>
        <div class="sheet-cell"><label>Aquí te pagan</label><b class="gold">${fmt(sellPriceAt(c, g) * (c.banned[g] ? 1.85 : 1 - taxP(c)))} ⦿</b></div>
        <div class="sheet-cell"><label>vs normal</label><b class="${dev < -0.18 ? 'up' : dev > 0.35 ? 'down' : 'flat'}">${pct(dev)}</b></div>
        <div class="sheet-cell"><label>En plaza</label><b>${fmt(c.stock[g])}</b></div>
        <div class="sheet-cell"><label>Llevas</label><b>${Math.floor(G.p.cargo[g] || 0)}</b></div>
      </div>
      ${risk !== null ? `<div class="warnbox">🕯️ <b>Prohibido en ${esc(c.name)}.</b> No se puede comprar aquí.
        Venderlo da un <b>+85%</b>, pero hay un <b>${Math.round(risk * 100)}% de que te pillen</b> en cada venta:
        confiscan la mercancía y te multan. Baja con buena reputación y sube con la notoriedad.</div>` : ''}

      ${best ? `<div class="opbox">
        <h4>Mejor operación desde aquí</h4>
        <p>Compra <b>${best.qty}</b> aquí por <b>${fmt(best.cost)} ⦿</b> y véndelo en
        <b>${esc(best.m.city.name)}</b> (${best.m.days} días): <b class="up">+${fmt(best.gain)} ⦿</b>
        ≈ ${fmt(best.perDay)} ⦿/día.${best.m.banned ? ' Ojo: allí es contrabando.' : ''}</p>
        <div class="mini">Estimado con el precio que recuerdas de hace ${best.m.age} días. Puede haber cambiado.</div>
        <button class="btn tiny" data-act="select-city" data-city="${best.m.city.id}">Ver ruta en el mapa</button>
      </div>` : '<div class="mini" style="margin:10px 0">Todavía no conoces ningún mercado donde te salga a cuenta llevar esto. Visita más ciudades.</div>'}

      <h4>Mercados que recuerdas</h4>
      ${mk.length > 1 ? `<table class="sheet">
        <thead><tr><th>Plaza</th>
          <th title="Lo que te costaría cada unidad si la compras allí">Te cuesta</th>
          <th title="Lo que te pagarían por cada unidad que vendas allí">Te pagan</th>
          <th>Viaje</th><th title="Antigüedad del dato">Dato</th></tr></thead>
        <tbody>${rows}</tbody></table>
        <div class="mini">Todo <b>por unidad</b>. En verde, donde más barato puedes comprarlo; en dorado, donde mejor te lo pagan.
        Los precios de otras plazas son los que anotaste al pasar por allí.</div>`
        : '<div class="mini">Solo conoces este mercado. Viaja para poder comparar.</div>'}
      ${this.sparkline(c.priceHist[g])}`,
      `${Math.floor(G.p.cargo[g] || 0) > 0 ? `<button class="btn" data-act="cargo" data-g="${g}">Vender lo que llevo</button>` : ''}
       <button class="btn primary" data-act="modal-close">Cerrar</button>`);
  },

  /* ----------------------- Bodega: vender un artículo ----------------------- */
  cargoModal(g) {
    const G = this.G;
    const have = Math.floor(G.p.cargo[g] || 0);
    if (have <= 0) return;
    this.cg = g;
    this.cq = have;                       // por defecto, vender todo
    this.modal(`${GOOD[g].icon} ${GOOD[g].name}`, '<div id="cargoPane"></div>',
      '<button class="btn" data-act="modal-close">Cerrar</button>');
    this.renderCargoPane();
  },
  setCargoQty(v) {
    const have = Math.floor(this.G.p.cargo[this.cg] || 0);
    let n;
    if (v === 'all') n = have;
    else if (v === 'half') n = Math.max(1, Math.floor(have / 2));
    else n = +v;
    this.cq = clamp(Math.floor(n), 1, have);
    this.renderCargoPane();
  },
  renderCargoPane() {
    const G = this.G, g = this.cg, c = G.city;
    const have = Math.floor(G.p.cargo[g] || 0);
    if (have <= 0) { this.closeModal(); this.refreshAll(); return; }
    this.cq = clamp(this.cq, 1, have);
    const n = this.cq;
    const banned = !!c.banned[g];
    const gross = revenueToSell(c, g, n);
    const net = banned ? gross * 1.85 : gross * (1 - taxP(c));
    const unit = net / n;
    const avg = G.p.avgCost && G.p.avgCost[g] && G.p.avgCost[g].n > 0 ? G.p.avgCost[g].total / G.p.avgCost[g].n : null;
    const profit = avg === null ? null : net - avg * n;
    const wh = G.p.warehouses[G.p.at];

    $('cargoPane').innerHTML = `
      <div class="kv"><span>En bodega</span><b>${have} unidades · ${Math.round(have * GOOD[g].w)} de carga</b></div>
      ${avg !== null ? `<div class="kv"><span>Lo pagaste a</span><b>${fmt(avg)} ⦿ la unidad</b></div>` : ''}
      <div class="kv"><span>Aquí en ${esc(c.name)} <b>te pagan</b></span><b class="gold">${fmt(unit)} ⦿ la unidad</b></div>
      ${banned ? `<div class="warnbox small">🕯️ Mercado negro: cobras un <b>+85%</b>, pero hay un
          <b>${Math.round(G.smuggleRisk(c) * 100)}%</b> de que te pillen en esta venta y pierdas la mercancía más una multa.</div>`
        : `<div class="mini">Ya descontado el ${(taxP(c) * 100).toFixed(1)}% de impuesto.</div>`}

      <div class="sellbox">
        <div class="sellqty">
          <button class="btn tiny" data-act="cq" data-v="${n - 1}" ${n <= 1 ? 'disabled' : ''}>−</button>
          <input type="number" id="cargoQty" min="1" max="${have}" value="${n}">
          <button class="btn tiny" data-act="cq" data-v="${n + 1}" ${n >= have ? 'disabled' : ''}>+</button>
          <span class="mini">de ${have}</span>
        </div>
        <input type="range" id="cargoRange" min="1" max="${have}" value="${n}" class="slider">
        <div class="qty">
          <button class="btn tiny" data-act="cq" data-v="1">1</button>
          <button class="btn tiny" data-act="cq" data-v="10" ${have < 10 ? 'disabled' : ''}>10</button>
          <button class="btn tiny" data-act="cq" data-v="half">Mitad</button>
          <button class="btn tiny" data-act="cq" data-v="all">Todo</button>
        </div>
        <div class="selltotal">
          <span>Te pagan por <b>${n}</b><small>a ${fmt(unit)} ⦿ la unidad</small></span>
          <b class="gold big">${fmt(net)} ⦿</b>
        </div>
        ${profit !== null ? `<div class="kv"><span>Ganancia sobre lo que pagaste</span>
          <b class="${profit >= 0 ? 'up' : 'down'}">${profit >= 0 ? '+' : ''}${fmt(profit)} ⦿</b></div>` : ''}
        <div class="qty">
          <button class="btn primary wide" data-act="cqsell">Vender ${n} ${GOOD[g].name}</button>
          ${wh ? `<button class="btn" data-act="cqstore">→ Almacén</button>` : ''}
        </div>
      </div>
      <div style="margin-top:12px">
        <div class="mini" style="margin-bottom:5px">Qué pasa con ${GOOD[g].name} en las plazas que conoces</div>
        ${this.marketMiniTable(g, 6)}
      </div>
      <button class="btn tiny wide" style="margin-top:10px" data-act="sheet" data-g="${g}">📊 Ficha completa y mejor operación</button>`;

    const inp = $('cargoQty'), rng = $('cargoRange');
    const sync = v => { this.cq = clamp(Math.floor(+v || 1), 1, have); this.renderCargoPane(); };
    inp.addEventListener('change', e => sync(e.target.value));
    rng.addEventListener('input', e => {
      this.cq = clamp(Math.floor(+e.target.value), 1, have);
      inp.value = this.cq;
      const gr = revenueToSell(c, g, this.cq);
      const nt = banned ? gr * 1.85 : gr * (1 - taxP(c));
      $('cargoPane').querySelector('.selltotal').innerHTML =
        `<span>Recibes por <b>${this.cq}</b></span><b class="gold big">${fmt(nt)} ⦿</b>`;
    });
    rng.addEventListener('change', e => sync(e.target.value));
  },
  cargoSell() {
    const g = this.cg, n = this.cq;
    const r = this.G.sell(g, n);
    if (r.err) return this.toast(r.err, 'bad');
    if (r.caught) { this.toast(r.msg, 'bad'); this.closeModal(); this.refreshAll(); return; }
    this.toast(`Vendes ${n} ${GOOD[g].name} por ${fmt(r.rev)} ⦿ (${fmt(r.unit)}/u). ${r.note || ''}`, 'good');
    this.refreshAll();
    if ((this.G.p.cargo[g] || 0) < 1) this.closeModal(); else { this.cq = Math.floor(this.G.p.cargo[g]); this.renderCargoPane(); }
  },
  cargoStore() {
    const r = this.G.storeGood(this.cg, this.cq);
    if (r.err) return this.toast(r.err, 'bad');
    this.toast(`Guardas ${this.cq} ${GOOD[this.cg].name} en el almacén.`, 'good');
    this.refreshAll();
    if ((this.G.p.cargo[this.cg] || 0) < 1) this.closeModal(); else { this.cq = Math.floor(this.G.p.cargo[this.cg]); this.renderCargoPane(); }
  },

  /* --------------------------------- Modales -------------------------------- */
  shipyard() {
    const G = this.G, c = G.city;
    const list = VEHICLES.filter(v => v.era <= G.p.era && (v.terrain === 'land' || c.shipyard)).map(v => {
      const price = Math.round(v.cost * (1 + taxP(c)));
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
    // voces de rivales que se acuerdan de ti
    const here = G.ai.merchants.filter(m => m.alive && m.at === c.id && m.memory && m.memory.length);
    for (const m of here.slice(0, 2)) {
      const line = rivalLine(m);
      if (line) out.push(line);
    }
    // lo que la ciudad recuerda
    const mem = (c.memories || []).filter(m => m.w >= 2);
    if (mem.length) { const m = pick(mem); out.push(`«${esc(m.text)}» — te lo recuerdan ${yearsAgo(G, m.day)}.`); }
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
      const cost = Math.round(r.cost * (1 + taxP(c)) * (b ? Math.pow(1.7, b.level) : 1));
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
        <li><b>Mercado</b>: pulsa un bien para desplegar la compra/venta. Dentro, <b>«Dónde conviene comprarlo y venderlo»</b>
          abre su ficha: todos los mercados que recuerdas y la mejor operación posible desde aquí, con la ganancia estimada.</li>
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
      <h4>El mundo te recuerda</h4>
      <ul>
        <li>Cada ciudad tiene un <b>carácter</b> (pesquera, minera, corte, santa, militar…): al entrar ya sabes qué se compra barato y qué se paga caro.</li>
        <li>Tu <b>fama</b> se construye con lo que haces: honrado, benefactor, contrabandista, corsario, especulador o mercader imperial. Cambia impuestos, precios, contratos y hasta si te dejan entrar.</li>
        <li>Las ciudades <b>recuerdan hechos concretos</b> y te los echan en cara años después. Vender comida barata en una hambruna no se olvida. Acaparar el hierro, tampoco.</li>
        <li>Cada varios meses ocurre un <b>gran acontecimiento</b> que reordena una región entera durante estaciones.</li>
        <li>Los <b>grandes encargos</b> piden cientos de unidades y se entregan por partes: no caben en una carreta.</li>
        <li>Explorando encuentras <b>ruinas, pecios, minas y oasis</b>: oro inmediato o ventajas permanentes.</li>
      </ul>
      <h4>Otros caminos</h4>
      <ul>
        <li><b>Contrabando</b>: los bienes prohibidos no se compran en la ciudad que los prohíbe, pero venderlos allí paga
          un 85% más. La ficha del bien te dice el porcentaje exacto de que te pillen: baja con buena reputación y sube con tu notoriedad.</li>
        <li><b>Corsario</b>: con 5+ guardias puedes emboscar caravanas rivales.</li>
        <li><b>Especulador</b>: compra todo el stock de un bien y estrangula la oferta local.</li>
      </ul>
      <p class="mini">Atajos: espacio = esperar 1 día · M/C/I/W = pestañas.</p>`);
  },
};
