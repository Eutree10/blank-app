/* Ruleta de rarezas — lógica de la app.
   Sin dependencias, sin build, todo el estado en localStorage. */

(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const el = {
    wheel: document.querySelector(".wheel"),
    word: $("topicWord"),
    hook: $("topicHook"),
    cat: $("catLabel"),
    spin: $("spinBtn"),
    chips: $("chips"),
    pool: $("poolCount"),
    result: $("result"),
    resultCat: $("resultCat"),
    resultDesc: $("resultDesc"),
    questions: $("resultQuestions"),
    links: $("resultLinks"),
    save: $("saveBtn"),
    empty: $("emptyNote"),
    listBtn: $("listBtn"),
    listCount: $("listCount"),
    drawer: $("drawer"),
    scrim: $("scrim"),
    closeDrawer: $("closeDrawer"),
    savedList: $("savedList"),
    reset: $("resetBtn")
  };

  const CATEGORIES = [...new Set(TOPICS.map((t) => t.c))];
  const KEY_SAVED = "ruleta.saved.v1";
  const KEY_SEEN = "ruleta.seen.v1";
  const KEY_CATS = "ruleta.cats.v1";

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const store = {
    read(key, fallback) {
      try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
      } catch {
        return fallback;
      }
    },
    write(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch {
        /* modo privado o cuota llena: la app sigue funcionando en memoria */
      }
    }
  };

  const state = {
    active: new Set(store.read(KEY_CATS, CATEGORIES).filter((c) => CATEGORIES.includes(c))),
    seen: new Set(store.read(KEY_SEEN, [])),
    saved: store.read(KEY_SAVED, []),
    current: null,
    spinning: false
  };

  if (state.active.size === 0) state.active = new Set(CATEGORIES);

  // ── Selección ───────────────────────────────────────────────────────────
  const pool = () => TOPICS.filter((t) => state.active.has(t.c));

  function pick() {
    const candidates = pool();
    if (candidates.length === 0) return null;
    // Prioriza lo que aún no ha salido; cuando se agota, empieza otra vuelta.
    let fresh = candidates.filter((t) => !state.seen.has(t.t) && t.t !== state.current?.t);
    if (fresh.length === 0) {
      state.seen = new Set();
      store.write(KEY_SEEN, []);
      fresh = candidates.filter((t) => t.t !== state.current?.t);
    }
    if (fresh.length === 0) fresh = candidates;
    return fresh[Math.floor(Math.random() * fresh.length)];
  }

  // ── Ruleta ──────────────────────────────────────────────────────────────
  function spin() {
    if (state.spinning) return;
    const target = pick();
    if (!target) return;

    state.spinning = true;
    el.spin.disabled = true;
    el.result.hidden = true;
    el.wheel.classList.add("is-spinning");
    el.hook.textContent = "";

    const names = pool().map((t) => t.t);
    const total = reducedMotion ? 3 : 22;
    let step = 0;

    const tick = () => {
      if (step < total) {
        el.word.textContent = names[Math.floor(Math.random() * names.length)];
        el.cat.textContent = "Girando";
        step++;
        // Deceleración: rápido al principio, cada vez más lento al final.
        const progress = step / total;
        const delay = reducedMotion ? 60 : 38 + Math.pow(progress, 3.2) * 300;
        setTimeout(tick, delay);
      } else {
        land(target);
      }
    };
    tick();
  }

  function land(topic) {
    state.spinning = false;
    state.current = topic;
    el.spin.disabled = false;
    el.wheel.classList.remove("is-spinning");

    el.word.textContent = topic.t;
    el.cat.textContent = topic.c;
    el.hook.textContent = topic.h;
    el.spin.querySelector(".btn-label").textContent = "Girar otra vez";

    state.seen.add(topic.t);
    store.write(KEY_SEEN, [...state.seen]);

    renderResult(topic);
  }

  // ── Tarjeta ─────────────────────────────────────────────────────────────
  const SOURCES = [
    { name: "Wikipedia", url: (q) => `https://es.wikipedia.org/w/index.php?search=${encodeURIComponent(q)}` },
    { name: "Google", url: (q) => `https://www.google.com/search?q=${encodeURIComponent(q)}` },
    { name: "YouTube", url: (q) => `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}` },
    { name: "Académico", url: (q) => `https://scholar.google.com/scholar?q=${encodeURIComponent(q)}` }
  ];

  const ARROW =
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">' +
    '<path d="M5 11 11 5M6 5h5v5"/></svg>';

  function renderResult(topic) {
    el.resultCat.textContent = topic.c;
    el.resultDesc.textContent = topic.d;

    el.questions.replaceChildren(
      ...topic.q.map((q, i) => {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "thread";
        btn.innerHTML =
          `<span class="thread-num">${String(i + 1).padStart(2, "0")}</span>` +
          `<span class="thread-text"></span>` +
          `<span class="thread-go" aria-hidden="true">↗</span>`;
        btn.querySelector(".thread-text").textContent = q;
        btn.title = "Buscar esta pregunta";
        btn.addEventListener("click", () => {
          window.open(SOURCES[1].url(`${topic.t} ${q}`), "_blank", "noopener");
        });
        li.appendChild(btn);
        return li;
      })
    );

    el.links.replaceChildren(
      ...SOURCES.map((s) => {
        const a = document.createElement("a");
        a.className = "link";
        a.href = s.url(topic.t);
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.innerHTML = `<span></span>${ARROW}`;
        a.firstChild.textContent = s.name;
        return a;
      })
    );

    syncSaveBtn();
    el.result.hidden = false;
  }

  // ── Guardados ───────────────────────────────────────────────────────────
  const isSaved = (title) => state.saved.includes(title);

  function toggleSave() {
    if (!state.current) return;
    const title = state.current.t;
    state.saved = isSaved(title) ? state.saved.filter((t) => t !== title) : [title, ...state.saved];
    store.write(KEY_SAVED, state.saved);
    syncSaveBtn();
    renderSaved();
  }

  function syncSaveBtn() {
    const saved = state.current && isSaved(state.current.t);
    el.save.textContent = saved ? "Guardado ✓" : "Guardar";
    el.save.classList.toggle("is-saved", !!saved);
    el.listCount.textContent = String(state.saved.length);
  }

  function renderSaved() {
    el.listCount.textContent = String(state.saved.length);

    if (state.saved.length === 0) {
      const p = document.createElement("p");
      p.className = "saved-empty";
      p.textContent = "Aún no has guardado ningún tema. Gira la ruleta y pulsa «Guardar».";
      el.savedList.replaceChildren(p);
      return;
    }

    el.savedList.replaceChildren(
      ...state.saved.map((title) => {
        const topic = TOPICS.find((t) => t.t === title);
        const row = document.createElement("div");
        row.className = "saved";
        if (!topic) return row;

        const main = document.createElement("div");
        main.className = "saved-main";
        const open = document.createElement("button");
        open.type = "button";
        open.className = "saved-title";
        open.textContent = topic.t;
        open.addEventListener("click", () => {
          land(topic);
          closeDrawer();
          window.scrollTo({ top: 0, behavior: reducedMotion ? "auto" : "smooth" });
        });
        const cat = document.createElement("span");
        cat.className = "saved-cat";
        cat.textContent = topic.c;
        main.append(open, cat);

        const del = document.createElement("button");
        del.type = "button";
        del.className = "icon-btn";
        del.setAttribute("aria-label", `Quitar ${topic.t} de la lista`);
        del.textContent = "✕";
        del.addEventListener("click", () => {
          state.saved = state.saved.filter((t) => t !== title);
          store.write(KEY_SAVED, state.saved);
          renderSaved();
          syncSaveBtn();
        });

        row.append(main, del);
        return row;
      })
    );
  }

  // ── Filtros ─────────────────────────────────────────────────────────────
  function renderChips() {
    el.chips.replaceChildren(
      ...CATEGORIES.map((c) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "chip";
        b.textContent = c;
        b.setAttribute("aria-pressed", String(state.active.has(c)));
        b.addEventListener("click", () => {
          if (state.active.has(c)) state.active.delete(c);
          else state.active.add(c);
          if (state.active.size === 0) state.active = new Set(CATEGORIES);
          store.write(KEY_CATS, [...state.active]);
          renderChips();
          syncPool();
        });
        return b;
      })
    );
  }

  function syncPool() {
    const n = pool().length;
    el.pool.textContent = String(n);
    el.spin.disabled = n === 0 || state.spinning;
    el.empty.hidden = n !== 0;
  }

  // ── Cajón ───────────────────────────────────────────────────────────────
  function openDrawer() {
    el.drawer.hidden = false;
    el.scrim.hidden = false;
    el.listBtn.setAttribute("aria-expanded", "true");
    el.closeDrawer.focus();
  }
  function closeDrawer() {
    el.drawer.hidden = true;
    el.scrim.hidden = true;
    el.listBtn.setAttribute("aria-expanded", "false");
  }

  // ── Eventos ─────────────────────────────────────────────────────────────
  el.spin.addEventListener("click", spin);
  el.save.addEventListener("click", toggleSave);
  el.listBtn.addEventListener("click", () => (el.drawer.hidden ? openDrawer() : closeDrawer()));
  el.closeDrawer.addEventListener("click", closeDrawer);
  el.scrim.addEventListener("click", closeDrawer);

  el.reset.addEventListener("click", () => {
    state.seen = new Set();
    store.write(KEY_SEEN, []);
    el.reset.textContent = "Historial reiniciado";
    setTimeout(() => (el.reset.textContent = "Reiniciar historial"), 1800);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !el.drawer.hidden) return closeDrawer();
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;
    if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.code === "Space" || e.key === "Enter") {
      if (e.target.closest("button, a")) return; // deja que el botón haga su trabajo
      e.preventDefault();
      spin();
    }
  });

  // ── Arranque ────────────────────────────────────────────────────────────
  renderChips();
  syncPool();
  renderSaved();
})();
