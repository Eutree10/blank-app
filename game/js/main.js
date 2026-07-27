/* =========================================================================
   Merchant's Odyssey — arranque
   ========================================================================= */
'use strict';

let GAME = null, VIEW = null;

function boot(game) {
  GAME = game;
  $('title').classList.add('hidden');
  $('app').classList.remove('hidden');
  VIEW = new MapView($('map'), game);
  UI.init(game, VIEW);
  if (!game.p.memory) UI.recordMemory();
  VIEW.fogDirty = true;

  let last = performance.now();
  function loop(t) {
    const dt = Math.min(60, t - last); last = t;
    VIEW.draw(dt);
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  setInterval(() => { try { game.save(); } catch (e) { } }, 45000);
  window.addEventListener('beforeunload', () => { try { game.save(); } catch (e) { } });
}

function seedFrom(str) {
  if (!str || !str.trim()) return (Math.random() * 4294967295) >>> 0;
  const n = Number(str);
  if (Number.isFinite(n) && String(n) === str.trim()) return (n >>> 0) || 1;
  return hashStr(str.trim());
}

window.addEventListener('DOMContentLoaded', () => {
  UI.bind();                                  // una sola vez, también en la portada
  const cont = $('btnContinue');
  cont.disabled = !Game.hasSave();
  if (cont.disabled) cont.title = 'No hay ninguna partida guardada';

  $('btnDice').onclick = () => { $('seedInput').value = String((Math.random() * 999999) | 0); };
  $('btnNew').onclick = () => {
    const seed = seedFrom($('seedInput').value);
    $('btnNew').textContent = 'Generando mundo…';
    setTimeout(() => {
      const g = new Game(seed);
      boot(g);
      UI.modal('Merchant\'s Odyssey', `
        <p>Mundo <b>#${seed}</b> generado: ${g.world.cities.length} ciudades, ${g.world.edges.length} rutas y ${g.ai.merchants.length} comerciantes rivales.</p>
        <p>Empiezas en <b>${esc(g.city.name)}</b> con <b>100 ⦿</b> y una mochila de 14 de capacidad.</p>
        <p>Compra algo barato aquí, viaja a una ciudad vecina y véndelo. Repite hasta tener flotas, fábricas y un imperio.</p>
        <p class="mini">Consejo: en el panel <b>Mundo → Oportunidades</b> verás las mejores rutas según los precios que recuerdas.</p>`,
        '<button class="btn" data-act="help">Cómo se juega</button><button class="btn primary" data-act="modal-close">Empezar</button>');
    }, 30);
  };
  $('btnContinue').onclick = () => {
    const g = Game.load();
    if (g && g.outdated) {
      Game.clearSave();
      cont.disabled = true;
      alert('Tu partida guardada es de una versión anterior del mundo (antes de la fama, el carácter de las ciudades y los grandes acontecimientos). Hay que empezar una nueva.');
      return;
    }
    if (!g) { alert('No se pudo cargar la partida.'); return; }
    boot(g);
  };
  $('btnHelp2').onclick = () => {
    UI.help();                              // el modal flota sobre la portada
    $('modalFoot').innerHTML = '<button class="btn primary" id="backTitle">Volver</button>';
    $('backTitle').onclick = () => UI.closeModal();
  };
  $('seedInput').addEventListener('keydown', e => { if (e.key === 'Enter') $('btnNew').click(); });
});
