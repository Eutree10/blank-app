"""Plan — the calendar, and the adaptation engine that keeps it honest."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from ...analysis.plan import adapt_week
from ...engine import Dashboard
from ...formats import WEEKDAYS_SHORT, fmt_num
from ...store import AppState, save_state
from .. import theme
from ..components import WORKOUT_ACCENT

EVENTS = {
    "Me enfermé": "enfermedad",
    "No completé una sesión": "sesion_perdida",
    "Competí sin planificarlo": "carrera_inesperada",
    "Estoy fatigado": "fatiga",
    "Tengo una molestia": "molestia",
    "Entrené más fuerte de lo previsto": "exceso",
}


def render(dashboard: Dashboard, state: AppState) -> None:
    theme.screen_header("Plan", "Tus semanas hasta la carrera")

    if not dashboard.plan:
        theme.card(
            '<div class="rf-muted">Cargá una carrera objetivo en <b>Carreras</b> '
            "para que la app construya el plan.</div>"
        )
        return

    _adaptation_control(dashboard, state)

    for index, week in enumerate(dashboard.plan):
        is_current = week.start <= date.today() < week.start + timedelta(days=7)
        _week_block(week, is_current, expanded=index == 0 or is_current)


def _week_block(week, is_current: bool, expanded: bool) -> None:
    end = week.start + timedelta(days=6)
    marker = theme.pill("en curso") if is_current else ""
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'margin:1.1rem 0 .5rem 0">'
        f'<div><div class="rf-eyebrow" style="margin-bottom:.15rem">'
        f'{week.start.strftime("%d/%m")} – {end.strftime("%d/%m")} · {fmt_num(week.target_km, 0)} km</div>'
        f'<div style="font-size:1rem;font-weight:600;color:{theme.INK};letter-spacing:-.02em">'
        f"Semana {week.index}</div></div>{marker}</div>"
        f'<div class="rf-muted" style="margin:-.35rem 0 .6rem 0">{week.theme}</div>',
        unsafe_allow_html=True,
    )

    rows = []
    for session in week.sessions:
        accent = WORKOUT_ACCENT.get(session.workout_type.value, theme.MUTED)
        is_today = session.day == date.today()
        is_rest = session.distance_m == 0
        done = session.status == "hecho"

        day_label = WEEKDAYS_SHORT[session.day.weekday()]
        detail = session.structure.splitlines()[0]

        title_color = theme.FAINT if is_rest else theme.INK
        weight = 600 if (is_today or session.key) else 520
        check = (
            f'<span style="color:{theme.GOOD};font-size:.8rem;margin-left:.35rem">✓</span>'
            if done else ""
        )
        today_bar = f"border-left:2px solid {theme.RED};padding-left:.6rem;" if is_today else "padding-left:.7rem;"
        note = (
            f'<div class="rf-muted" style="font-size:.74rem;color:{theme.WARN};margin-top:.15rem">'
            f"{session.note}</div>"
            if session.note else ""
        )
        rows.append(
            f'<div style="display:flex;gap:.7rem;padding:.55rem 0;border-bottom:1px solid {theme.LINE};'
            f'{today_bar}">'
            f'<div style="width:2.1rem;flex-shrink:0">'
            f'<div style="font-size:.72rem;font-weight:620;color:{theme.RED if is_today else theme.FAINT};'
            f'text-transform:uppercase;letter-spacing:.04em">{day_label}</div>'
            f'<div class="rf-value" style="font-size:.78rem;color:{theme.FAINT}">'
            f'{session.day.strftime("%d")}</div></div>'
            f'<div style="flex:1;min-width:0">'
            f'<div style="font-size:.9rem;font-weight:{weight};color:{title_color};'
            f'letter-spacing:-.01em">{session.title}{check}</div>'
            f'<div class="rf-muted" style="font-size:.78rem;margin-top:.1rem">{detail}</div>'
            f"{note}</div>"
            f'<div style="width:.4rem;flex-shrink:0;background:{accent};border-radius:2px;'
            f'opacity:{0.9 if session.workout_type.is_quality else 0.25}"></div>'
            f"</div>"
        )

    theme.card("".join(rows))


def _adaptation_control(dashboard: Dashboard, state: AppState) -> None:
    """Tell the app what changed, and it recalculates the rest of the week."""
    week = dashboard.current_week
    if not week:
        return

    with st.expander("Algo cambió esta semana"):
        st.markdown(
            '<div class="rf-muted" style="margin-bottom:.6rem">La app no mueve sesiones de lugar: '
            "recalcula lo que queda de la semana para no juntar estímulos incompatibles.</div>",
            unsafe_allow_html=True,
        )
        label = st.selectbox("¿Qué pasó?", list(EVENTS), key="adapt_event")
        if st.button("Recalcular la semana", type="primary", use_container_width=True):
            adaptation = adapt_week(week, EVENTS[label], dashboard.zones)
            for session in adaptation.week.sessions:
                if session.day >= date.today():
                    state.plan_overrides[session.day.isoformat()] = session
            save_state(state)
            st.session_state.last_adaptation = {
                "explanation": adaptation.explanation,
                "changes": adaptation.changes,
            }
            st.rerun()

    last = st.session_state.get("last_adaptation")
    if last:
        changes = "".join(
            f'<div class="rf-muted" style="margin-top:.25rem">· {change}</div>'
            for change in last["changes"]
        )
        theme.card(
            '<div class="rf-eyebrow">Plan recalculado</div>'
            f'<div class="rf-note">{last["explanation"]}</div>{changes}',
            accent=True,
        )
        if st.button("Restaurar plan original", use_container_width=True, key="reset_plan"):
            state.plan_overrides = {}
            save_state(state)
            st.session_state.pop("last_adaptation", None)
            st.rerun()
