"""Hoy — the only screen that matters most days.

Three answers, in order: how you are, what to do, and why. Everything else on
this screen is an action, not information.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from ...engine import Dashboard
from ...formats import fmt_day_long, fmt_pace_range
from ...models import Feedback
from ...store import AppState, save_state
from .. import theme
from ..components import feedback_form, session_teaser

STATE_COLORS = {
    "recuperado": (theme.GOOD, "#E9F5EE"),
    "listo": (theme.GOOD, "#E9F5EE"),
    "cargado": (theme.WARN, "#FBF2DF"),
    "fatigado": (theme.BAD, theme.RED_SOFT),
}


def render(dashboard: Dashboard, state: AppState) -> None:
    today = date.today()
    theme.screen_header("Hoy", fmt_day_long(today).capitalize())

    _current_state(dashboard)
    _recommended_session(dashboard, state)
    _pending_feedback(dashboard, state)


def _current_state(dashboard: Dashboard) -> None:
    readiness = dashboard.readiness
    color, background = STATE_COLORS.get(readiness.state, (theme.MUTED, "#F1F1EE"))

    drivers = "".join(
        f'<div class="rf-muted" style="margin-top:.3rem">· {driver}</div>'
        for driver in readiness.drivers[:2]
    )
    theme.card(
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
        f'<div style="flex:1">'
        f'<div class="rf-eyebrow">Estado actual</div>'
        f'<div class="rf-note" style="font-size:1rem;font-weight:560;color:{theme.INK};'
        f'line-height:1.4">{readiness.summary}</div>'
        f"{drivers}"
        f"</div>"
        f'<div style="text-align:right;padding-left:.8rem">'
        f'<div class="rf-value" style="font-size:1.6rem;color:{color}">{readiness.score}</div>'
        f'{theme.pill(readiness.state, color, background)}'
        f"</div></div>"
    )


def _recommended_session(dashboard: Dashboard, state: AppState) -> None:
    recommendation = dashboard.recommendation
    if not recommendation:
        theme.card(
            '<div class="rf-eyebrow">Entrenamiento recomendado</div>'
            '<div class="rf-note">Definí una carrera objetivo en <b>Carreras</b> '
            "y la app arma el plan alrededor de esa fecha.</div>"
        )
        return

    session = recommendation.session
    is_rest = session.distance_m == 0

    target = ""
    if session.target_pace_low and session.target_pace_high and not is_rest:
        target = (
            f'<div class="rf-muted" style="margin-top:.5rem">Ritmo objetivo · '
            f"{fmt_pace_range(session.target_pace_low, session.target_pace_high)}</div>"
        )

    theme.card(
        '<div class="rf-eyebrow">Entrenamiento recomendado</div>'
        f'<div class="rf-prescription">{session.structure}</div>'
        f"{target}"
        f'<div class="rf-muted" style="margin-top:.55rem">Objetivo · {session.purpose}</div>',
        accent=True,
    )

    theme.card(
        '<div class="rf-eyebrow">Por qué</div>'
        f'<div class="rf-note">{recommendation.reason}</div>'
    )

    # One primary action; the rest are secondary by design.
    if st.button(
        "Marcar como hecho" if not is_rest else "Marcar descanso",
        type="primary",
        use_container_width=True,
        key="today_done",
    ):
        state.plan_overrides[session.day.isoformat()] = _completed(session)
        save_state(state)
        st.toast("Sesión registrada.")
        st.rerun()

    left, right = st.columns(2)
    with left:
        if st.button("Ver alternativa", use_container_width=True, key="today_alt"):
            st.session_state.show_alternative = not st.session_state.get("show_alternative", False)
    with right:
        if st.button("Registrar molestia", use_container_width=True, key="today_niggle"):
            st.session_state.show_niggle = not st.session_state.get("show_niggle", False)

    if st.session_state.get("show_alternative") and recommendation.alternative:
        alternative = recommendation.alternative
        theme.card(
            '<div class="rf-eyebrow">Alternativa más suave</div>'
            f'<div class="rf-prescription" style="font-size:1.05rem">{alternative.structure}</div>'
            f'<div class="rf-muted" style="margin-top:.5rem">{recommendation.alternative_reason}</div>'
        )

    if st.session_state.get("show_niggle"):
        _niggle_form(dashboard, state)


def _completed(session):
    from dataclasses import replace

    return replace(session, status="hecho")


def _niggle_form(dashboard: Dashboard, state: AppState) -> None:
    with st.form("niggle_form"):
        st.markdown('<div class="rf-eyebrow">Registrar molestia</div>', unsafe_allow_html=True)
        where = st.text_input("¿Dónde?", placeholder="Tibial derecho, aquiles, isquios…")
        severity = st.select_slider(
            "¿Cuánto limita?",
            options=[1, 2, 3],
            value=1,
            format_func=lambda value: {1: "La noto", 2: "Limita", 3: "Me frena"}[value],
        )
        if st.form_submit_button("Guardar", type="primary", use_container_width=True):
            last = dashboard.activities[-1] if dashboard.activities else None
            if last:
                existing = state.feedback.get(last.id) or Feedback(activity_id=last.id)
                existing.niggle = where
                existing.niggle_severity = severity
                state.feedback[last.id] = existing
                save_state(state)
                st.session_state.show_niggle = False
                st.toast("Molestia registrada. El plan la tiene en cuenta.")
                st.rerun()
            else:
                st.warning("No hay actividades para asociar la molestia.")


def _pending_feedback(dashboard: Dashboard, state: AppState) -> None:
    """The three questions, asked only for sessions that have not been rated."""
    unrated = [
        analysis for analysis in dashboard.analyses[-6:]
        if analysis.activity.id not in state.feedback
    ]
    if unrated:
        analysis = unrated[-1]
        st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
        theme.eyebrow("Falta tu lectura de esta sesión")
        session_teaser(analysis, show_score=False)
        feedback_form(analysis.activity.id, state, key="today_feedback")
        return

    if dashboard.analyses:
        st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
        theme.eyebrow("Última sesión")
        analysis = dashboard.analyses[-1]
        session_teaser(analysis)
        if st.button("Ver análisis completo", use_container_width=True, key="today_last"):
            st.session_state.selected_activity = analysis.activity.id
            st.session_state.screen = "sesion"
            st.rerun()
