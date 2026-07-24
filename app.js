/* ============================================================
   PackList — MVP
   Listas de equipaje simples, guardadas localmente en el
   dispositivo (localStorage). Sin login, sin nube.
   ============================================================ */
(function () {
  "use strict";

  var STORAGE_KEY = "packlist.v1";

  /* ---------- Estado + persistencia ---------- */
  var state = load();

  function load() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.lists)) return parsed;
      }
    } catch (e) { /* almacenamiento no disponible o corrupto */ }
    return { lists: [] };
  }

  var saveTimer = null;
  function save() {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
      catch (e) { /* p.ej. modo privado lleno: se ignora silenciosamente */ }
    }, 120);
  }

  // Id único sin depender de crypto (compatibilidad amplia y offline).
  var seq = 0;
  function uid() {
    seq += 1;
    return Date.now().toString(36) + "-" + seq.toString(36) + "-" +
           Math.floor(Math.random() * 1e6).toString(36);
  }

  function findList(id) {
    for (var i = 0; i < state.lists.length; i++) {
      if (state.lists[i].id === id) return state.lists[i];
    }
    return null;
  }

  /* ---------- Referencias al DOM ---------- */
  var $ = function (sel) { return document.querySelector(sel); };
  var viewHome = $("#view-home");
  var viewList = $("#view-list");
  var listsEl = $("#lists");
  var itemsEl = $("#items");
  var nameInput = $("#list-name");
  var detailCount = $("#detail-count");
  var addForm = $("#add-form");
  var addInput = $("#add-input");
  var fab = $("#fab");
  var tplCard = $("#tpl-list-card");
  var tplItem = $("#tpl-item");

  var currentListId = null;

  /* ============================================================
     Navegación entre vistas
     ============================================================ */
  function showHome() {
    currentListId = null;
    viewList.classList.add("is-hidden");
    viewHome.classList.remove("is-hidden");
    fab.classList.remove("is-hidden");
    renderHome();
    setHash("");
  }

  function openList(id, focusName) {
    var list = findList(id);
    if (!list) { showHome(); return; }
    currentListId = id;
    viewHome.classList.add("is-hidden");
    viewList.classList.remove("is-hidden");
    fab.classList.add("is-hidden");
    nameInput.value = list.name || "";
    renderItems();
    setHash(id);
    if (focusName) {
      // Nueva lista: enfoca el nombre para escribir sin fricción.
      setTimeout(function () { nameInput.focus(); }, 50);
    } else {
      window.scrollTo(0, 0);
    }
  }

  function setHash(id) {
    var target = id ? "#/list/" + id : "#/";
    if (location.hash !== target) {
      history.replaceState(null, "", target);
    }
  }

  /* ============================================================
     Render — Home (todas las listas)
     ============================================================ */
  function renderHome() {
    listsEl.textContent = "";

    if (state.lists.length === 0) {
      listsEl.appendChild(emptyState(
        "Aún no tienes listas",
        "Toca el botón + para crear tu primera lista de equipaje."
      ));
      return;
    }

    for (var i = 0; i < state.lists.length; i++) {
      listsEl.appendChild(buildListCard(state.lists[i]));
    }
  }

  function buildListCard(list) {
    var node = tplCard.content.firstElementChild.cloneNode(true);
    var nameEl = node.querySelector(".list-card-name");
    var metaEl = node.querySelector(".list-card-meta");
    var countEl = node.querySelector(".list-card-count");

    var name = (list.name || "").trim();
    if (name) {
      nameEl.textContent = name;
    } else {
      nameEl.textContent = "Sin título";
      nameEl.classList.add("is-empty");
    }

    var total = list.items.length;
    var done = countDone(list);
    metaEl.textContent = total === 0
      ? "Lista vacía"
      : done + " de " + total + " marcados";
    countEl.textContent = done + "/" + total;
    if (total > 0 && done === total) countEl.classList.add("is-complete");

    node.setAttribute("aria-label", (name || "Sin título") + ", " + done + " de " + total + " marcados");

    attachRowGestures(node, {
      onActivate: function () { openList(list.id, false); },
      onDelete: function () { deleteList(list.id); }
    });
    return node;
  }

  /* ============================================================
     Render — Detalle (ítems de una lista)
     ============================================================ */
  function renderItems() {
    var list = findList(currentListId);
    if (!list) return;
    itemsEl.textContent = "";
    updateDetailCount(list);

    if (list.items.length === 0) {
      itemsEl.appendChild(emptyState(
        "Lista vacía",
        "Añade tu primer ítem desde el campo de abajo."
      ));
      return;
    }

    for (var i = 0; i < list.items.length; i++) {
      itemsEl.appendChild(buildItem(list, list.items[i]));
    }
  }

  function buildItem(list, item) {
    var node = tplItem.content.firstElementChild.cloneNode(true);
    var textEl = node.querySelector(".item-text");
    textEl.textContent = item.text;
    if (item.done) node.classList.add("done");
    node.setAttribute("aria-label",
      item.text + (item.done ? ", marcado" : ", sin marcar"));

    attachRowGestures(node, {
      onActivate: function () { toggleItem(list.id, item.id, node); },
      onDelete: function () { deleteItem(list.id, item.id); }
    });
    return node;
  }

  function updateDetailCount(list) {
    var total = list.items.length;
    var done = countDone(list);
    detailCount.textContent = total ? done + "/" + total : "";
    detailCount.classList.toggle("is-complete", total > 0 && done === total);
  }

  function countDone(list) {
    var n = 0;
    for (var i = 0; i < list.items.length; i++) if (list.items[i].done) n++;
    return n;
  }

  function emptyState(title, text) {
    var wrap = document.createElement("div");
    wrap.className = "empty";
    var h = document.createElement("p");
    h.className = "empty-title";
    h.textContent = title;
    var p = document.createElement("p");
    p.className = "empty-text";
    p.textContent = text;
    wrap.appendChild(h);
    wrap.appendChild(p);
    return wrap;
  }

  /* ============================================================
     Mutaciones
     ============================================================ */
  function createList() {
    var list = { id: uid(), name: "", items: [] };
    state.lists.unshift(list);
    save();
    openList(list.id, true);
  }

  function deleteList(id) {
    var idx = -1, removed = null;
    for (var i = 0; i < state.lists.length; i++) {
      if (state.lists[i].id === id) { idx = i; removed = state.lists[i]; break; }
    }
    if (idx === -1) return;
    state.lists.splice(idx, 1);
    save();
    renderHome();
    showToast("Lista eliminada", function () {
      state.lists.splice(Math.min(idx, state.lists.length), 0, removed);
      save();
      renderHome();
    });
  }

  function toggleItem(listId, itemId, node) {
    var list = findList(listId);
    if (!list) return;
    for (var i = 0; i < list.items.length; i++) {
      if (list.items[i].id === itemId) {
        list.items[i].done = !list.items[i].done;
        node.classList.toggle("done", list.items[i].done);
        node.setAttribute("aria-label",
          list.items[i].text + (list.items[i].done ? ", marcado" : ", sin marcar"));
        updateDetailCount(list);
        save();
        return;
      }
    }
  }

  function addItem(text) {
    var list = findList(currentListId);
    if (!list) return;
    var clean = text.trim();
    if (!clean) return;
    list.items.push({ id: uid(), text: clean, done: false });
    save();

    // Si estaba vacía, re-render completo; si no, añade solo la fila nueva.
    if (list.items.length === 1) {
      renderItems();
    } else {
      var node = buildItem(list, list.items[list.items.length - 1]);
      node.classList.add("enter");
      itemsEl.appendChild(node);
      updateDetailCount(list);
    }
  }

  function deleteItem(listId, itemId) {
    var list = findList(listId);
    if (!list) return;
    var idx = -1, removed = null;
    for (var i = 0; i < list.items.length; i++) {
      if (list.items[i].id === itemId) { idx = i; removed = list.items[i]; break; }
    }
    if (idx === -1) return;
    list.items.splice(idx, 1);
    save();
    renderItems(); // reconstruye la vista para descartar la fila animada
    showToast("Ítem eliminado", function () {
      var l = findList(listId);
      if (!l) return;
      l.items.splice(Math.min(idx, l.items.length), 0, removed);
      save();
      renderItems();
    });
  }

  function renameCurrent(value) {
    var list = findList(currentListId);
    if (!list) return;
    list.name = value;
    save();
  }

  /* ============================================================
     Gestos de fila: tap (activar), swipe y pulsación larga (borrar)
     Usa Pointer Events → unifica ratón y táctil.
     ============================================================ */
  function attachRowGestures(row, handlers) {
    var face = row.querySelector(".swipe-face");
    var startX = 0, startY = 0, dx = 0;
    var dragging = false, horizontal = false, decided = false;
    var longTimer = null, longFired = false;
    var pointerId = null;
    var startT = 0;

    var WIDTH = function () { return row.offsetWidth || 320; };
    var DELETE_THRESHOLD = 0.42;   // fracción del ancho para confirmar borrado
    var DIR_LOCK = 10;             // px antes de decidir eje del gesto
    var TAP_SLOP = 8;              // movimiento máx. para contar como tap
    var LONG_MS = 500;

    function clearLong() {
      if (longTimer) { clearTimeout(longTimer); longTimer = null; }
    }

    function onDown(e) {
      if (pointerId !== null) return;
      if (e.pointerType === "mouse" && e.button !== 0) return;
      pointerId = e.pointerId;
      startX = e.clientX; startY = e.clientY;
      dx = 0; dragging = true; horizontal = false; decided = false;
      longFired = false;
      startT = e.timeStamp;
      face.style.transition = "none";

      clearLong();
      longTimer = setTimeout(function () {
        // Pulsación larga sin desplazamiento → eliminar.
        if (dragging && !horizontal && Math.abs(dx) < TAP_SLOP) {
          longFired = true;
          dragging = false;
          releaseCapture();
          animateOutAndDelete();
        }
      }, LONG_MS);
    }

    function onMove(e) {
      if (!dragging || e.pointerId !== pointerId) return;
      var mx = e.clientX - startX;
      var my = e.clientY - startY;

      if (!decided) {
        if (Math.abs(mx) < DIR_LOCK && Math.abs(my) < DIR_LOCK) return;
        decided = true;
        horizontal = Math.abs(mx) > Math.abs(my);
        if (horizontal) {
          clearLong();
          try { face.setPointerCapture(pointerId); } catch (_) {}
        } else {
          // Desplazamiento vertical → deja hacer scroll, cancela el gesto.
          dragging = false;
          clearLong();
          return;
        }
      }

      if (horizontal) {
        clearLong();
        // Solo se desliza hacia la izquierda (borrar); resistencia a la derecha.
        dx = mx < 0 ? mx : mx * 0.25;
        face.style.transform = "translateX(" + dx + "px)";
        e.preventDefault();
      }
    }

    function onUp(e) {
      if (e.pointerId !== pointerId) return;
      clearLong();
      var wasDragging = dragging;
      dragging = false;
      releaseCapture();

      if (longFired) { pointerId = null; return; }

      var moved = Math.abs(dx);
      var dt = e.timeStamp - startT;

      if (horizontal && moved > WIDTH() * DELETE_THRESHOLD) {
        animateOutAndDelete();
      } else if (horizontal) {
        snapBack();
      } else if (wasDragging && moved < TAP_SLOP && dt < 700) {
        // Tap limpio → activar (abrir lista / marcar ítem).
        snapBack();
        handlers.onActivate();
      }
      pointerId = null;
    }

    function onCancel() {
      clearLong();
      dragging = false;
      releaseCapture();
      snapBack();
      pointerId = null;
    }

    function releaseCapture() {
      if (pointerId !== null) {
        try { face.releasePointerCapture(pointerId); } catch (_) {}
      }
    }

    function snapBack() {
      face.style.transition = "transform .18s ease";
      face.style.transform = "translateX(0)";
      dx = 0;
    }

    function animateOutAndDelete() {
      face.style.transition = "transform .18s ease";
      face.style.transform = "translateX(-100%)";
      row.style.height = row.offsetHeight + "px";
      // fuerza reflow para que la transición de altura funcione
      void row.offsetHeight;
      row.classList.add("removing");
      var done = false;
      var finish = function () {
        if (done) return;
        done = true;
        handlers.onDelete();
      };
      row.addEventListener("transitionend", finish, { once: true });
      setTimeout(finish, 300); // respaldo si no dispara transitionend
    }

    face.addEventListener("pointerdown", onDown);
    face.addEventListener("pointermove", onMove);
    face.addEventListener("pointerup", onUp);
    face.addEventListener("pointercancel", onCancel);

    // Accesibilidad: teclado (Enter/Espacio activa; Supr/Backspace borra).
    row.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handlers.onActivate();
      } else if (e.key === "Delete" || e.key === "Backspace") {
        e.preventDefault();
        handlers.onDelete();
      }
    });
  }

  /* ============================================================
     Toast de deshacer
     ============================================================ */
  var toast = $("#toast");
  var toastText = $("#toast-text");
  var toastUndo = $("#toast-undo");
  var toastTimer = null;
  var undoAction = null;

  function showToast(message, onUndo) {
    toastText.textContent = message;
    undoAction = onUndo;
    toast.classList.remove("is-hidden");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(hideToast, 4200);
  }
  function hideToast() {
    toast.classList.add("is-hidden");
    undoAction = null;
    if (toastTimer) { clearTimeout(toastTimer); toastTimer = null; }
  }
  toastUndo.addEventListener("click", function () {
    if (undoAction) undoAction();
    hideToast();
  });

  /* ============================================================
     Enlaces de la interfaz
     ============================================================ */
  fab.addEventListener("click", createList);
  $("#btn-back").addEventListener("click", showHome);

  addForm.addEventListener("submit", function (e) {
    e.preventDefault();
    addItem(addInput.value);
    addInput.value = "";
    addInput.focus(); // permite añadir varios ítems seguidos
  });

  nameInput.addEventListener("input", function () {
    renameCurrent(nameInput.value);
  });
  nameInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); nameInput.blur(); }
  });

  // Botón atrás del navegador / cambios de hash.
  window.addEventListener("popstate", route);
  function route() {
    var m = location.hash.match(/^#\/list\/(.+)$/);
    if (m && findList(m[1])) openList(m[1], false);
    else showHome();
  }

  // Arranque: respeta el enlace profundo si lo hay.
  route();

  /* ---------- Service worker (offline) ---------- */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js").catch(function () { /* opcional */ });
    });
  }
})();
