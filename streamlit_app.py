"""Life RPG — offline-first habit tracker with XP, coins, life and levels.

Phone-style Streamlit app with a fixed bottom tab bar:
Home · Hábitos · Tienda · Historial · Ajustes.
"""

from datetime import date, datetime

import streamlit as st

import game

st.set_page_config(page_title="Life RPG", page_icon="🎮", layout="centered")

TABS = [
    ("home", "🏠", "Home"),
    ("habits", "✅", "Hábitos"),
    ("shop", "🛒", "Tienda"),
    ("history", "📜", "Historial"),
    ("settings", "⚙️", "Ajustes"),
]
TAB_KEYS = [t[0] for t in TABS]


# --- State bootstrap -------------------------------------------------------

def get_state():
    if "state" not in st.session_state:
        st.session_state.state = game.load_state()
    return st.session_state.state


def current_tab() -> str:
    tab = st.query_params.get("tab", "home")
    return tab if tab in TAB_KEYS else "home"


# --- Styling ---------------------------------------------------------------

def inject_css():
    st.markdown(
        """
        <style>
        /* Constrain to a phone-like column and leave room for bottom bar */
        .block-container {
            max-width: 520px;
            padding-top: 1.2rem;
            padding-bottom: 6rem;
        }
        header[data-testid="stHeader"] { background: transparent; }
        #MainMenu, footer { visibility: hidden; }

        /* Stat cards */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 6px;
        }
        .stat-card {
            background: linear-gradient(145deg, #1e2530, #262f3d);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 14px 16px;
            color: #e8ecf3;
        }
        .stat-card .label { font-size: 0.72rem; opacity: 0.65; text-transform: uppercase; letter-spacing: .04em; }
        .stat-card .value { font-size: 1.5rem; font-weight: 700; margin-top: 2px; }

        .hero {
            background: linear-gradient(145deg, #4c2d8f, #7b3fbf);
            border-radius: 20px;
            padding: 18px 20px;
            color: #fff;
            margin-bottom: 14px;
        }
        .hero .lvl { font-size: 2.2rem; font-weight: 800; line-height: 1; }
        .hero .sub { opacity: 0.85; font-size: 0.85rem; }

        .bar-wrap { background: rgba(0,0,0,0.25); border-radius: 999px; height: 12px; overflow: hidden; margin-top: 10px; }
        .bar-fill { background: linear-gradient(90deg, #ffd54a, #ff9d3f); height: 100%; border-radius: 999px; }

        .life-wrap { background: rgba(0,0,0,0.25); border-radius: 999px; height: 12px; overflow: hidden; margin-top: 8px; }
        .life-fill { background: linear-gradient(90deg, #ff5e7e, #ff2d55); height: 100%; border-radius: 999px; }

        /* Bottom tab bar */
        .tabbar {
            position: fixed;
            left: 50%; transform: translateX(-50%);
            bottom: 0;
            width: 100%; max-width: 520px;
            display: flex;
            background: rgba(20,24,32,0.96);
            backdrop-filter: blur(8px);
            border-top: 1px solid rgba(255,255,255,0.08);
            padding: 6px 4px calc(6px + env(safe-area-inset-bottom));
            z-index: 999;
        }
        .tabbar a {
            flex: 1;
            text-align: center;
            text-decoration: none;
            color: #8b95a5;
            font-size: 0.66rem;
            padding: 4px 0;
            border-radius: 12px;
        }
        .tabbar a .ico { display: block; font-size: 1.35rem; line-height: 1.4; }
        .tabbar a.active { color: #fff; background: rgba(123,63,191,0.28); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_tabbar(active: str):
    links = ""
    for key, icon, label in TABS:
        cls = "active" if key == active else ""
        links += (f'<a class="{cls}" href="?tab={key}" target="_self">'
                  f'<span class="ico">{icon}</span>{label}</a>')
    st.markdown(f'<div class="tabbar">{links}</div>', unsafe_allow_html=True)


# --- Tab: Home -------------------------------------------------------------

def render_home(state):
    p = state["player"]
    st.markdown("### 🎮 Life RPG")

    needed = game.xp_to_level(p["level"])
    maxed = p["level"] >= game.MAX_LEVEL
    pct = 100 if maxed else min(100, int(100 * p["xp"] / needed))
    xp_line = "¡Nivel máximo!" if maxed else f'{p["xp"]} / {needed} XP'

    st.markdown(
        f"""
        <div class="hero">
            <div class="sub">Nivel</div>
            <div class="lvl">{p['level']} <span style="font-size:1rem;opacity:.7">/ {game.MAX_LEVEL}</span></div>
            <div class="bar-wrap"><div class="bar-fill" style="width:{pct}%"></div></div>
            <div class="sub" style="margin-top:6px">{xp_line}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    life_pct = max(0, min(100, int(100 * p["life"] / game.INITIAL_LIFE)))
    st.markdown(
        f"""
        <div class="stat-grid">
            <div class="stat-card"><div class="label">🪙 Monedas</div><div class="value">{p['coins']}</div></div>
            <div class="stat-card"><div class="label">⭐ XP del nivel</div><div class="value">{p['xp']}</div></div>
        </div>
        <div class="stat-card" style="margin-bottom:14px">
            <div class="label">❤️ Vida</div>
            <div class="value">{p['life']} <span style="font-size:.8rem;opacity:.6">/ {game.INITIAL_LIFE}</span></div>
            <div class="life-wrap"><div class="life-fill" style="width:{life_pct}%"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Marca tus hábitos del día en la pestaña **Hábitos**. "
               "Ganás XP y monedas con los buenos; los malos te quitan vida.")

    logs = state["logs"][:5]
    if logs:
        st.markdown("#### Actividad reciente")
        for entry in logs:
            st.markdown(_log_line(entry), unsafe_allow_html=True)


# --- Tab: Habits -----------------------------------------------------------

def render_habits(state):
    st.markdown("### ✅ Hábitos")
    good = [h for h in state["habits"] if h.get("active") and h["type"] == "good"]
    bad = [h for h in state["habits"] if h.get("active") and h["type"] == "bad"]

    st.markdown("#### 🌱 Buenos hábitos")
    if not good:
        st.caption("No hay buenos hábitos activos. Agregá algunos en Ajustes.")
    for h in good:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(
                f"**{h['icon']} {h['name']}**  \n"
                f"<span style='opacity:.65;font-size:.8rem'>+{h['xpReward']} XP · +{h['coinReward']} 🪙</span>",
                unsafe_allow_html=True)
        with c2:
            if st.button("Marcar", key=f"mark_{h['id']}", use_container_width=True):
                res = game.mark_habit(state, h["id"])
                msg = f"+{res['d_xp']} XP · +{res['d_coins']} 🪙"
                if res["levels_gained"]:
                    st.balloons()
                    msg += f" · 🎉 ¡Subiste {res['levels_gained']} nivel(es)!"
                st.toast(f"{h['icon']} {h['name']}: {msg}")
                st.rerun()

    st.markdown("#### ⚠️ Malos hábitos")
    if not bad:
        st.caption("No hay malos hábitos activos.")
    for h in bad:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(
                f"**{h['icon']} {h['name']}**  \n"
                f"<span style='opacity:.65;font-size:.8rem;color:#ff8a9c'>-{h['lifePenalty']} ❤️</span>",
                unsafe_allow_html=True)
        with c2:
            if st.button("Marcar", key=f"mark_{h['id']}", use_container_width=True):
                res = game.mark_habit(state, h["id"])
                st.toast(f"{h['icon']} {h['name']}: {res['d_life']} ❤️")
                st.rerun()


# --- Tab: Shop -------------------------------------------------------------

def render_shop(state):
    st.markdown("### 🛒 Tienda")
    st.markdown(
        f"<div class='stat-card' style='margin-bottom:12px'>"
        f"<div class='label'>🪙 Tus monedas</div>"
        f"<div class='value'>{state['player']['coins']}</div></div>",
        unsafe_allow_html=True)

    items = [s for s in state["shop"] if s.get("active")]
    if not items:
        st.caption("La tienda está vacía. Agregá items en Ajustes.")

    today = date.today().isoformat()
    for it in items:
        c1, c2 = st.columns([3, 1])
        detail = f"{it['price']} 🪙"
        if it.get("effect") == "life":
            detail += f" · +{it['lifeAmount']} ❤️"
        bought_life_today = (it.get("effect") == "life"
                             and state["player"].get("lastLifeBuyDate") == today)
        with c1:
            st.markdown(
                f"**{it['icon']} {it['name']}**  \n"
                f"<span style='opacity:.65;font-size:.8rem'>{detail}</span>",
                unsafe_allow_html=True)
        with c2:
            can_afford = state["player"]["coins"] >= it["price"]
            disabled = not can_afford or bought_life_today
            label = "Comprado" if bought_life_today else "Comprar"
            if st.button(label, key=f"buy_{it['id']}", use_container_width=True, disabled=disabled):
                res = game.buy_item(state, it["id"])
                if res["ok"]:
                    extra = f" · +{res['d_life']} ❤️" if res["d_life"] else ""
                    st.toast(f"{it['icon']} Compraste {it['name']} ({res['d_coins']} 🪙{extra})")
                else:
                    st.toast("No se pudo comprar.")
                st.rerun()
        if bought_life_today:
            st.caption("Solo podés comprar vida una vez por día.")


# --- Tab: History ----------------------------------------------------------

def _log_line(entry) -> str:
    icons = {"habit": "✅", "shop": "🛒", "punishment": "💪"}
    ico = icons.get(entry["category"], "•")
    parts = []
    if entry["deltaXp"]:
        parts.append(f"{entry['deltaXp']:+d} XP")
    if entry["deltaCoins"]:
        parts.append(f"{entry['deltaCoins']:+d} 🪙")
    if entry["deltaLife"]:
        parts.append(f"{entry['deltaLife']:+d} ❤️")
    deltas = " · ".join(parts) if parts else "—"
    try:
        ts = datetime.fromisoformat(entry["timestamp"]).strftime("%d/%m %H:%M")
    except (ValueError, KeyError):
        ts = entry.get("timestamp", "")
    note = entry.get("note") or entry["category"]
    return (f"<div class='stat-card' style='margin-bottom:8px'>"
            f"<b>{ico} {note}</b>"
            f"<div style='opacity:.6;font-size:.78rem'>{ts} · {deltas}</div></div>")


def render_history(state):
    st.markdown("### 📜 Historial")
    logs = state["logs"]
    if not logs:
        st.caption("Todavía no hay actividad. ¡Empezá marcando hábitos!")
        return
    for entry in logs[:100]:
        st.markdown(_log_line(entry), unsafe_allow_html=True)
    if len(logs) > 100:
        st.caption(f"Mostrando 100 de {len(logs)} entradas.")


# --- Tab: Settings ---------------------------------------------------------

def render_settings(state):
    st.markdown("### ⚙️ Ajustes")

    with st.expander("➕ Agregar hábito"):
        with st.form("add_habit", clear_on_submit=True):
            name = st.text_input("Nombre")
            icon = st.text_input("Icono (emoji)", value="⭐")
            htype = st.selectbox("Tipo", ["good", "bad"],
                                 format_func=lambda x: "Bueno" if x == "good" else "Malo")
            col1, col2 = st.columns(2)
            xp = col1.number_input("XP (si bueno)", min_value=0, value=30, step=5)
            coins = col2.number_input("Monedas (si bueno)", min_value=0, value=10, step=5)
            penalty = st.number_input("Penalización de vida (si malo)", min_value=0,
                                      value=game.DEFAULT_LIFE_PENALTY, step=10)
            if st.form_submit_button("Agregar hábito"):
                if name.strip():
                    state["habits"].append({
                        "id": game._new_id(), "name": name.strip(), "type": htype,
                        "xpReward": int(xp), "coinReward": int(coins),
                        "lifePenalty": int(penalty), "icon": icon or "⭐", "active": True,
                    })
                    game.save_state(state)
                    st.toast("Hábito agregado")
                    st.rerun()
                else:
                    st.warning("Poné un nombre.")

    with st.expander("🗂️ Administrar hábitos"):
        for h in state["habits"]:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"{h['icon']} **{h['name']}** "
                        f"<span style='opacity:.5'>({'bueno' if h['type']=='good' else 'malo'})</span>",
                        unsafe_allow_html=True)
            new_active = c2.toggle("Activo", value=h.get("active", True), key=f"act_{h['id']}")
            if new_active != h.get("active", True):
                h["active"] = new_active
                game.save_state(state)
                st.rerun()
            if c3.button("🗑️", key=f"del_{h['id']}"):
                state["habits"] = [x for x in state["habits"] if x["id"] != h["id"]]
                game.save_state(state)
                st.rerun()

    with st.expander("🛒 Agregar item de tienda"):
        with st.form("add_item", clear_on_submit=True):
            iname = st.text_input("Nombre del item")
            iicon = st.text_input("Icono (emoji)", value="🎁")
            price = st.number_input("Precio (monedas)", min_value=0, value=100, step=10)
            effect = st.selectbox("Efecto", ["none", "life"],
                                  format_func=lambda x: "Ninguno" if x == "none" else "Dar vida")
            life_amt = st.number_input("Cantidad de vida (si aplica)", min_value=0, value=200, step=50)
            if st.form_submit_button("Agregar item"):
                if iname.strip():
                    state["shop"].append({
                        "id": game._new_id(), "name": iname.strip(), "price": int(price),
                        "effect": effect, "lifeAmount": int(life_amt),
                        "icon": iicon or "🎁", "active": True,
                    })
                    game.save_state(state)
                    st.toast("Item agregado")
                    st.rerun()
                else:
                    st.warning("Poné un nombre.")

    with st.expander("🗂️ Administrar tienda"):
        for it in state["shop"]:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"{it['icon']} **{it['name']}** "
                        f"<span style='opacity:.5'>({it['price']} 🪙)</span>",
                        unsafe_allow_html=True)
            new_active = c2.toggle("Activo", value=it.get("active", True), key=f"sact_{it['id']}")
            if new_active != it.get("active", True):
                it["active"] = new_active
                game.save_state(state)
                st.rerun()
            if c3.button("🗑️", key=f"sdel_{it['id']}"):
                state["shop"] = [x for x in state["shop"] if x["id"] != it["id"]]
                game.save_state(state)
                st.rerun()

    st.divider()
    st.markdown("#### Datos")
    col1, col2 = st.columns(2)
    if col1.button("♻️ Reiniciar progreso", use_container_width=True,
                   help="Borra nivel, XP, monedas, vida e historial (mantiene hábitos y tienda)."):
        st.session_state.state = game.reset_player_only(state)
        st.toast("Progreso reiniciado")
        st.rerun()
    if col2.button("💥 Restablecer todo", use_container_width=True,
                   help="Vuelve a los valores de fábrica (hábitos, tienda y progreso)."):
        st.session_state.state = game.reset_progress(state)
        st.toast("Todo restablecido")
        st.rerun()


# --- Punishment dialog -----------------------------------------------------

@st.dialog("💀 Vida en 0")
def punishment_dialog(state):
    st.markdown("### Debes completar un castigo")
    st.markdown("Tu vida llegó a **0**. Para continuar, completá:")
    st.markdown(f"## 💪 {game.PUNISHMENT_TEXT}")
    st.warning("No podés seguir jugando hasta confirmar el castigo.")
    if st.button("✅ Confirmar castigo hecho", use_container_width=True, type="primary"):
        game.complete_punishment(state)
        st.rerun()


# --- Main ------------------------------------------------------------------

def main():
    inject_css()
    state = get_state()
    tab = current_tab()

    # Mandatory punishment: reopens every run until confirmed.
    if game.needs_punishment(state):
        punishment_dialog(state)

    if tab == "home":
        render_home(state)
    elif tab == "habits":
        render_habits(state)
    elif tab == "shop":
        render_shop(state)
    elif tab == "history":
        render_history(state)
    elif tab == "settings":
        render_settings(state)

    render_tabbar(tab)


if __name__ == "__main__":
    main()
