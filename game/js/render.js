/* =========================================================================
   Merchant's Odyssey — render del mapa (pixel art sobre canvas)
   ========================================================================= */
'use strict';

const PX = 2; // píxeles por tile en el buffer base

class MapView {
  constructor(canvas, game) {
    this.cv = canvas;
    this.ctx = canvas.getContext('2d');
    this.game = game;
    this.cam = { x: 0, y: 0, z: 7 };
    this.hover = null;
    this.selected = null;
    this.showRoutes = true;
    this.showRivals = true;
    this.travelAnim = null;
    this.time = 0;
    this.buildBase();
    this.fogDirty = true;
    this.bindEvents();
    this.centerOn(game.city.x, game.city.y);
  }

  /* ------------------------ Buffers pre-renderizados ---------------------- */
  buildBase() {
    const W = this.game.world;
    const c = document.createElement('canvas');
    c.width = W.w * PX; c.height = W.h * PX;
    const g = c.getContext('2d');
    const img = g.createImageData(c.width, c.height);
    const d = img.data;
    for (let y = 0; y < W.h; y++) {
      for (let x = 0; x < W.w; x++) {
        const i = W.idx(x, y);
        const b = BIOMES[W.biomeKeys[W.biome[i]]];
        const variant = (hashStr(x + ':' + y) % 3);
        let col = b.col[variant];
        // sombreado por altura
        let [r, gg, bb] = hex2rgb(col);
        const e = W.elev[i];
        const sh = clamp(1 + (e - 0.12) * 0.55, 0.75, 1.35);
        if (W.land[i]) { r *= sh; gg *= sh; bb *= sh; }
        // línea de costa
        if (W.land[i]) {
          let coast = false;
          for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
            const nx = x + dx, ny = y + dy;
            if (W.inBounds(nx, ny) && !W.land[W.idx(nx, ny)]) coast = true;
          }
          if (coast) { r = r * 0.72 + 40; gg = gg * 0.72 + 30; bb = bb * 0.7 + 18; }
        }
        for (let py = 0; py < PX; py++) for (let px = 0; px < PX; px++) {
          const o = ((y * PX + py) * c.width + (x * PX + px)) * 4;
          const n = ((hashStr(x + '_' + y + '_' + px + '_' + py) % 100) - 50) / 50 * 6;
          d[o] = clamp(r + n, 0, 255); d[o + 1] = clamp(gg + n, 0, 255); d[o + 2] = clamp(bb + n, 0, 255); d[o + 3] = 255;
        }
      }
    }
    g.putImageData(img, 0, 0);
    this.base = c;

    const f = document.createElement('canvas');
    f.width = W.w; f.height = W.h;
    this.fog = f;
  }

  updateFog() {
    const W = this.game.world;
    const g = this.fog.getContext('2d');
    const img = g.createImageData(W.w, W.h);
    const d = img.data;
    for (let i = 0; i < W.known.length; i++) {
      const o = i * 4;
      if (W.known[i]) { d[o + 3] = 0; continue; }
      // niebla opaca con grano: lo desconocido no insinúa la forma del mundo
      const n = (hashStr('f' + i) % 9);
      d[o] = 12 + n; d[o + 1] = 11 + n; d[o + 2] = 9 + n; d[o + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    this.fogDirty = false;
  }

  /* ------------------------------ Cámara ---------------------------------- */
  centerOn(tx, ty) {
    const r = this.cv.getBoundingClientRect();
    this.cam.x = tx - (r.width / this.cam.z) / 2;
    this.cam.y = ty - (r.height / this.cam.z) / 2;
    this.clampCam();
  }
  minZoom() {
    const W = this.game.world, r = this.cv.getBoundingClientRect();
    // el mundo cubre siempre el ancho del visor: nunca se ve el vacío a los lados
    return clamp(r.width / W.w, 2.2, 9);
  }
  clampCam() {
    const W = this.game.world, r = this.cv.getBoundingClientRect();
    this.cam.z = Math.max(this.cam.z, this.minZoom());
    const vw = r.width / this.cam.z, vh = r.height / this.cam.z;
    this.cam.x = vw >= W.w ? (W.w - vw) / 2 : clamp(this.cam.x, 0, W.w - vw);
    this.cam.y = vh >= W.h ? (W.h - vh) / 2 : clamp(this.cam.y, 0, W.h - vh);
  }
  s2w(px, py) {
    const r = this.cv.getBoundingClientRect();
    return { x: this.cam.x + (px - r.left) / this.cam.z, y: this.cam.y + (py - r.top) / this.cam.z };
  }
  w2s(x, y) { return { x: (x - this.cam.x) * this.cam.z, y: (y - this.cam.y) * this.cam.z }; }

  /* ------------------------------ Eventos --------------------------------- */
  bindEvents() {
    const cv = this.cv;
    let drag = null;
    cv.addEventListener('mousedown', e => { drag = { x: e.clientX, y: e.clientY, cx: this.cam.x, cy: this.cam.y, moved: 0 }; });
    window.addEventListener('mouseup', e => {
      if (drag && drag.moved < 5) this.click(e.clientX, e.clientY);
      drag = null;
    });
    window.addEventListener('mousemove', e => {
      if (drag) {
        drag.moved += Math.abs(e.movementX) + Math.abs(e.movementY);
        this.cam.x = drag.cx - (e.clientX - drag.x) / this.cam.z;
        this.cam.y = drag.cy - (e.clientY - drag.y) / this.cam.z;
        this.clampCam();
        cv.style.cursor = 'grabbing';
      } else cv.style.cursor = this.cityAt(e.clientX, e.clientY) ? 'pointer' : 'grab';
      this.hover = this.cityAt(e.clientX, e.clientY);
      this.mouse = { x: e.clientX, y: e.clientY };
    });
    cv.addEventListener('wheel', e => {
      e.preventDefault();
      const before = this.s2w(e.clientX, e.clientY);
      this.cam.z = clamp(this.cam.z * (e.deltaY < 0 ? 1.18 : 1 / 1.18), this.minZoom(), 18);
      const after = this.s2w(e.clientX, e.clientY);
      this.cam.x += before.x - after.x; this.cam.y += before.y - after.y;
      this.clampCam();
    }, { passive: false });

    // táctil
    let touch = null;
    cv.addEventListener('touchstart', e => {
      if (e.touches.length === 1) touch = { x: e.touches[0].clientX, y: e.touches[0].clientY, cx: this.cam.x, cy: this.cam.y, moved: 0, t: performance.now() };
      else if (e.touches.length === 2) touch = { pinch: Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY), z: this.cam.z };
    }, { passive: true });
    cv.addEventListener('touchmove', e => {
      if (!touch) return;
      if (touch.pinch && e.touches.length === 2) {
        const d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
        this.cam.z = clamp(touch.z * (d / touch.pinch), this.minZoom(), 18); this.clampCam();
      } else if (e.touches.length === 1) {
        touch.moved += 3;
        this.cam.x = touch.cx - (e.touches[0].clientX - touch.x) / this.cam.z;
        this.cam.y = touch.cy - (e.touches[0].clientY - touch.y) / this.cam.z;
        this.clampCam();
      }
      e.preventDefault();
    }, { passive: false });
    cv.addEventListener('touchend', e => {
      if (touch && !touch.pinch && touch.moved < 8) this.click(touch.x, touch.y);
      touch = null;
    });
  }

  cityAt(px, py) {
    const r = 14;
    let best = null, bd = r;
    for (const c of this.game.world.cities) {
      if (!c.known) continue;
      const s = this.w2s(c.x, c.y);
      const d = Math.hypot(s.x - (px - this.cv.getBoundingClientRect().left), s.y - (py - this.cv.getBoundingClientRect().top));
      if (d < bd) { bd = d; best = c; }
    }
    return best;
  }
  click(px, py) {
    const c = this.cityAt(px, py);
    if (c) { this.selected = c; if (this.onSelect) this.onSelect(c); }
    else { this.selected = null; if (this.onSelect) this.onSelect(null); }
  }

  animateTravel(path, cb) {
    const pts = path.map(i => this.game.world.cities[i]);
    this.travelAnim = { pts, t: 0, dur: 900 + path.length * 180, cb, start: performance.now() };
  }

  /* ------------------------------- Dibujo --------------------------------- */
  draw(dt) {
    const cv = this.cv, ctx = this.ctx, G = this.game, W = G.world;
    const rect = cv.getBoundingClientRect();
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    if (cv.width !== Math.round(rect.width * dpr) || cv.height !== Math.round(rect.height * dpr)) {
      cv.width = Math.round(rect.width * dpr); cv.height = Math.round(rect.height * dpr);
      this.clampCam();
    }
    this.time += dt;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = '#0d0c0a';
    ctx.fillRect(0, 0, rect.width, rect.height);

    const z = this.cam.z;
    const sx = -this.cam.x * z, sy = -this.cam.y * z;
    ctx.drawImage(this.base, 0, 0, this.base.width, this.base.height, sx, sy, W.w * z, W.h * z);

    if (this.fogDirty) this.updateFog();
    ctx.drawImage(this.fog, 0, 0, W.w, W.h, sx, sy, W.w * z, W.h * z);
    ctx.strokeStyle = 'rgba(200,169,106,.16)'; ctx.lineWidth = 1;
    ctx.strokeRect(sx - 0.5, sy - 0.5, W.w * z + 1, W.h * z + 1);

    // --- rutas
    if (this.showRoutes) {
      const w = Math.max(1.2, z * 0.14);
      for (const e of W.edges) {
        const A = W.cities[e.a], B = W.cities[e.b];
        if (!A.known || !B.known) continue;
        const p = this.w2s(A.x, A.y), q = this.w2s(B.x, B.y);
        ctx.setLineDash(e.type === 'sea' ? [z * 0.5, z * 0.4] : []);
        // trazo oscuro debajo para que la ruta se lea sobre cualquier terreno
        ctx.lineWidth = w + 1.6; ctx.strokeStyle = 'rgba(10,9,7,.45)';
        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
        ctx.lineWidth = w;
        ctx.strokeStyle = e.blocked > 0 ? 'rgba(248,81,73,.85)'
          : e.danger > 0.12 ? 'rgba(227,179,65,.7)'
            : e.type === 'sea' ? 'rgba(224,199,150,.5)' : 'rgba(224,199,150,.62)';
        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
      }
      ctx.setLineDash([]);
    }

    // --- ruta planificada
    if (this.plan && this.plan.path) {
      ctx.lineWidth = Math.max(1.6, z * 0.20);
      ctx.strokeStyle = 'rgba(200,169,106,.95)';
      ctx.setLineDash([z * 0.6, z * 0.45]);
      ctx.lineDashOffset = -(this.time * 0.02) % 1000;
      ctx.beginPath();
      this.plan.path.forEach((ci, i) => {
        const c = W.cities[ci], s = this.w2s(c.x, c.y);
        i ? ctx.lineTo(s.x, s.y) : ctx.moveTo(s.x, s.y);
      });
      ctx.stroke(); ctx.setLineDash([]);
    }

    // --- rivales
    if (this.showRivals && z > 3.2) {
      for (const m of G.ai.merchants) {
        if (!m.alive) continue;
        const A = W.cities[m.at];
        if (!A || !A.known) continue;
        let x = A.x, y = A.y;
        if (m.dest >= 0 && W.edges[m.edge]) {
          const B = W.cities[m.dest];
          if (!B.known) continue;
          const e = W.edges[m.edge];
          const total = Math.max(1, Math.round(e.days / m.speed));
          const t = clamp(1 - m.daysLeft / total, 0, 1);
          x = lerp(A.x, B.x, t); y = lerp(A.y, B.y, t);
        }
        const s = this.w2s(x, y);
        ctx.fillStyle = m.style.id === 'pirata' ? 'rgba(248,81,73,.8)' : m.style.id === 'contra' ? 'rgba(227,179,65,.75)' : 'rgba(232,226,210,.55)';
        ctx.fillRect(s.x - 1.5, s.y - 1.5, 3, 3);
      }
    }

    // --- ciudades
    for (const c of W.cities) {
      if (!c.known) continue;
      const s = this.w2s(c.x, c.y);
      if (s.x < -40 || s.y < -40 || s.x > rect.width + 40 || s.y > rect.height + 40) continue;
      const size = clamp(2.6 + Math.log10(Math.max(1000, c.pop)) * 1.4, 4, 11) * clamp(z / 5, 0.7, 1.5);
      const isHere = c.id === G.p.at;
      const sel = this.selected && this.selected.id === c.id;

      // halo de evento
      if (c.events.length) {
        const ev = c.events[0];
        ctx.beginPath();
        ctx.arc(s.x, s.y, size * 1.9 + Math.sin(this.time * 0.004) * 1.5, 0, 7);
        ctx.fillStyle = eventColor(ev.id, 0.16);
        ctx.fill();
      }
      // marcador
      ctx.beginPath();
      const r = size * 0.62;
      ctx.fillStyle = c.visited ? '#C8A96A' : '#8b7f66';
      ctx.strokeStyle = '#0B0A08'; ctx.lineWidth = 1.5;
      if (c.coastal) { // rombo para puertos
        ctx.moveTo(s.x, s.y - r); ctx.lineTo(s.x + r, s.y); ctx.lineTo(s.x, s.y + r); ctx.lineTo(s.x - r, s.y); ctx.closePath();
      } else ctx.rect(s.x - r, s.y - r, r * 2, r * 2);
      ctx.fill(); ctx.stroke();

      if (isHere) {
        ctx.beginPath();
        ctx.arc(s.x, s.y, size * 1.5 + 2 + Math.sin(this.time * 0.005) * 1.5, 0, 7);
        ctx.strokeStyle = '#F5F0E6'; ctx.lineWidth = 1.6; ctx.stroke();
      }
      if (sel) {
        ctx.beginPath();
        ctx.arc(s.x, s.y, size * 1.9, 0, 7);
        ctx.strokeStyle = 'rgba(200,169,106,.9)'; ctx.setLineDash([3, 3]); ctx.lineWidth = 1.2; ctx.stroke(); ctx.setLineDash([]);
      }
      // etiqueta
      // marca de suceso: un punto de color sobre la ciudad (sin emoji, se ve igual en todos lados)
      if (c.events.length) {
        ctx.beginPath();
        ctx.arc(s.x + r + 2.5, s.y - r - 1.5, 2.2, 0, 7);
        ctx.fillStyle = eventColor(c.events[0].id, 0.95);
        ctx.fill();
      }
      if (z > 4 || sel || isHere || (this.hover && this.hover.id === c.id)) {
        ctx.font = `${Math.round(clamp(z * 1.5, 9, 13))}px "IBM Plex Mono", ui-monospace, monospace`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'top';
        ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(6,6,4,.85)';
        ctx.strokeText(c.name, s.x, s.y + r + 3);
        ctx.fillStyle = isHere ? '#F5F0E6' : (c.visited ? '#d8cdb4' : '#9A8F76');
        ctx.fillText(c.name, s.x, s.y + r + 3);
      }
    }

    // --- animación de viaje
    if (this.travelAnim) {
      const a = this.travelAnim;
      const t = clamp((performance.now() - a.start) / a.dur, 0, 1);
      const seg = t * (a.pts.length - 1);
      const i = Math.min(a.pts.length - 2, Math.floor(seg));
      const f = seg - i;
      const A = a.pts[i], B = a.pts[i + 1] || A;
      const s = this.w2s(lerp(A.x, B.x, f), lerp(A.y, B.y, f));
      ctx.beginPath(); ctx.arc(s.x, s.y, 4.5, 0, 7);
      ctx.fillStyle = '#F5F0E6'; ctx.fill();
      ctx.beginPath(); ctx.arc(s.x, s.y, 9, 0, 7);
      ctx.strokeStyle = 'rgba(200,169,106,.6)'; ctx.lineWidth = 1.5; ctx.stroke();
      if (t >= 1) { const cb = a.cb; this.travelAnim = null; if (cb) cb(); }
    }
  }
}

function hex2rgb(h) {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function eventColor(id, a) {
  const map = {
    guerra: `rgba(248,81,73,${a})`, peste: `rgba(150,90,200,${a})`, hambruna: `rgba(227,179,65,${a})`,
    feria: `rgba(63,185,80,${a})`, boom: `rgba(88,166,255,${a})`, minahallada: `rgba(88,166,255,${a})`,
    revolucion: `rgba(248,81,73,${a})`, erupcion: `rgba(255,120,40,${a})`, sequia: `rgba(227,179,65,${a})`,
  };
  return map[id] || `rgba(200,169,106,${a})`;
}
