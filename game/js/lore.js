/* =========================================================================
   Merchant's Odyssey — fama, memoria y generaciones
   El mundo recuerda lo que hiciste, y lo cuenta cuando vuelves.
   ========================================================================= */
'use strict';

/* ------------------------------- Fama ------------------------------------ */
/** Suma puntos a una faceta de tu fama y deja constancia si es notable. */
function addFame(G, kind, amount) {
  if (!G.p.fame) G.p.fame = {};
  G.p.fame[kind] = (G.p.fame[kind] || 0) + amount;
}
/** La faceta dominante: cómo te llama el mundo. */
function fameRole(p) {
  const f = p.fame || {};
  let best = null, total = 0;
  for (const k in f) { total += Math.max(0, f[k]); if (!best || f[k] > f[best]) best = k; }
  if (!best || f[best] < 5) return { id: 'novato', name: 'Desconocido', icon: '·', desc: 'Nadie ha oído hablar de ti todavía.', level: 0 };
  const def = FAME[best];
  const level = clamp(Math.floor(Math.log(f[best] / 6) / Math.log(2.4)) + 1, 1, 5);
  return { id: best, name: def.name, icon: def.icon, desc: def.desc, level, score: f[best] };
}
function fameStars(level) { return '★'.repeat(level) + '☆'.repeat(Math.max(0, 5 - level)); }

/** Cómo te trata una ciudad concreta según lo que recuerda de ti. */
function standing(c) {
  const r = c.playerRep || 0;
  if (r <= -40) return { id: 'vetado', name: 'Vetado', icon: '⛔', color: 'down' };
  if (r <= -12) return { id: 'malvisto', name: 'Mal visto', icon: '😠', color: 'down' };
  if (r < 12) return { id: 'neutral', name: 'Desconocido', icon: '·', color: 'flat' };
  if (r < 40) return { id: 'apreciado', name: 'Apreciado', icon: '🙂', color: 'up' };
  if (r < 90) return { id: 'respetado', name: 'Respetado', icon: '🤝', color: 'up' };
  return { id: 'ilustre', name: 'Ciudadano ilustre', icon: '🏅', color: 'gold' };
}
/** Descuento sobre el impuesto local por tu reputación (o recargo si te odian). */
function repTaxFactor(c) {
  const r = clamp(c.playerRep || 0, -60, 120);
  return clamp(1 - r / 300, 0.6, 1.35);
}
/** Impuesto que te aplica a ti esta ciudad, ya con tu reputación dentro. */
function taxP(c) { return clamp(c.tax * repTaxFactor(c), 0.004, 0.35); }

/* ------------------------------ Memoria ---------------------------------- */
/* Cada ciudad guarda hechos concretos: qué le trajiste y cuándo. Con los años
   los recuerdan y te lo dicen a la cara.                                     */
function remember(G, city, text, weight, tag) {
  if (!city.memories) city.memories = [];
  city.memories.unshift({ day: G.day, text, w: weight || 1, tag: tag || '' });
  if (city.memories.length > 12) city.memories.pop();
}
function yearsAgo(G, day) {
  const y = (G.day - day) / 360;
  if (y < 1) return 'hace unos meses';
  if (y < 2) return 'hace un año';
  return `hace ${Math.floor(y)} años`;
}
/** Una frase que la ciudad te dedica al llegar, si tiene algo que recordar. */
function cityGreeting(G, city) {
  const st = standing(city);
  const mem = (city.memories || []).filter(m => m.w >= 2);
  if (mem.length && rnd() < 0.8) {
    const m = pick(mem);
    return `«${m.text}» — se comenta en ${city.name}, ${yearsAgo(G, m.day)}.`;
  }
  if (st.id === 'vetado') return `En ${city.name} te reciben con la guardia de por medio.`;
  if (st.id === 'ilustre') return `En ${city.name} te saludan por tu nombre antes de que bajes de la carreta.`;
  if (st.id === 'respetado') return `Los tenderos de ${city.name} te guardan sitio en el muelle.`;
  if (st.id === 'malvisto') return `Nadie te ofrece ayuda para descargar en ${city.name}.`;
  return null;
}

/* --------------------------- Generaciones -------------------------------- */
/* Los rivales envejecen, se retiran y dejan la casa a un heredero que hereda
   el apellido, el capital… y lo que su padre pensaba de ti.                  */
function ageMerchants(G) {
  const A = G.ai;
  for (const m of A.merchants) {
    if (!m.alive) continue;
    if (m.age === undefined) m.age = rint(28, 58);
    m.age += 1 / 360;
    if (m.age >= (m.retireAt || (m.retireAt = rint(63, 76)))) succeed(G, m);
  }
}
function succeed(G, m) {
  const heirFirst = pick(MERCH_FIRST);
  const last = m.name.split(' ').slice(1).join(' ') || pick(MERCH_LAST);
  const oldName = m.name;
  m.generation = (m.generation || 1) + 1;
  m.name = heirFirst + ' ' + last;
  m.age = rint(24, 36);
  m.retireAt = rint(63, 76);
  m.gold *= 0.8;                                   // repartos, dotes y funerales
  // la memoria se hereda, pero difuminada
  m.memory = (m.memory || []).map(x => ({ ...x, inherited: true, from: oldName }));
  if (m.knownByPlayer) {
    G.news(`${oldName} se retira. ${m.name} toma las riendas de ${m.company}.`, 'rival', null, '⚱️');
  }
}
/** Un rival recuerda algo que le hiciste. */
function rivalRemember(m, text, tone) {
  if (!m.memory) m.memory = [];
  m.memory.unshift({ text, tone: tone || 0 });
  if (m.memory.length > 6) m.memory.pop();
  m.opinion = (m.opinion || 0) + (tone || 0);
}
/** Frase de un rival sobre ti, heredada o vivida. */
function rivalLine(m) {
  if (!m.memory || !m.memory.length) return null;
  const x = pick(m.memory);
  if (x.inherited) return `«Mi ${rnd() < 0.5 ? 'padre' : 'madre'}, ${x.from}, me habló de ti: ${x.text.toLowerCase()}» — ${m.name}, ${m.company}.`;
  return `«${x.text}» — ${m.name}, ${m.company}.`;
}
