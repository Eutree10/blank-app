"""Carreras — preparation, prediction and strategy for each goal."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from ...analysis.capability import cumulative_splits, race_strategy
from ...analysis.predict import equivalent_performances, prediction_history
from ...engine import Dashboard, GoalView
from ...formats import fmt_day_short, fmt_num, fmt_pace, fmt_time, parse_time
from ...models import Goal
from ...store import AppState, save_state
from .. import charts, theme, visuals
from ..components import explanation

DISTANCE_OPTIONS = {
    "800 m": 800,
    "1500 m": 1500,
    "2400 m": 2400,
    "3000 m": 3000,
    "5000 m": 5000,
    "10 km": 10000,
    "21,1 km": 21097,
}


def render(dashboard: Dashboard, state: AppState) -> None:
    theme.screen_header("Carreras", "Preparación y predicción por objetivo")

    if not dashboard.goals:
        theme.card(
            '<div style="font-size:1rem;font-weight:600;color:#0E0E10;margin-bottom:.35rem">'
            "Sin carreras cargadas</div>"
            '<div class="rf-muted">Agregá una carrera objetivo y la app arma la preparación, '
            "la predicción y el plan alrededor de esa fecha.</div>"
        )
        _add_goal_form(state)
        return

    labels = [
        f"{view.goal.name} · {view.goal.distance_m / 1000:g} km"
        for view in dashboard.goals
    ]
    tabs = st.tabs(labels)
    for tab, view in zip(tabs, dashboard.goals):
        with tab:
            _goal_detail(view, dashboard, state)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    with st.expander("Agregar otra carrera"):
        _add_goal_form(state)


def _goal_detail(view: GoalView, dashboard: Dashboard, state: AppState) -> None:
    goal, readiness, prediction = view.goal, view.readiness, view.prediction
    is_primary = dashboard.goals and dashboard.goals[0].goal.id == goal.id

    target_html = (
        f'<div class="rf-muted">Objetivo · {fmt_time(goal.target_time_s)} '
        f"({fmt_pace(goal.target_pace_s_km)})</div>"
        if goal.target_time_s
        else '<div class="rf-muted">Sin marca objetivo definida</div>'
    )
    days = goal.days_left
    when = (
        f"En {days} días" if days > 0 else "Hoy" if days == 0 else f"Hace {abs(days)} días"
    )

    theme.card(
        '<div class="rf-eyebrow">Predicción actual</div>'
        f'<div class="rf-hero" style="font-size:2.6rem">'
        f"{fmt_time(prediction.low_s)}–{fmt_time(prediction.high_s)}</div>"
        f'<div class="rf-muted" style="margin-top:.5rem">{prediction.basis}</div>'
        f'<div style="margin-top:.7rem">{target_html}</div>'
        f'<div class="rf-muted">{when} · {goal.race_date.strftime("%d/%m/%Y")} · '
        f"confianza {prediction.confidence:.0%}</div>",
        dark=True,
    )

    # Preparation, broken into the capabilities that decide the result. The
    # rings give the shape at a glance; the bars carry the measurement.
    theme.eyebrow("Preparación")
    # Rings stay on the semantic green/amber/red scale. The limiter is called
    # out by name above instead — the brand accent must not compete with a
    # colour that already means "how good is this".
    rings = "".join(
        '<div style="flex:1">'
        + visuals.ring(score.score, _short_capability(score.capability.value), size=66)
        + "</div>"
        for score in readiness.capabilities
    )
    meters = "".join(
        theme.meter_html(score.capability.value, score.score, caption=score.detail)
        for score in readiness.capabilities
    )
    theme.card(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-bottom:1rem">'
        f'<div><div class="rf-eyebrow" style="margin:0">Global</div>'
        f'<div class="rf-hero" style="font-size:2.1rem;color:'
        f'{theme.score_color(readiness.overall)}">{readiness.overall}'
        f'<span class="rf-hero-unit">%</span></div></div>'
        f'<div style="text-align:right;max-width:52%">'
        f'<div class="rf-muted">Limitante</div>'
        f'<div style="font-size:.92rem;font-weight:600;color:{theme.INK}">'
        f"{readiness.limiter.capability.value}</div></div></div>"
        f'<div style="display:flex;gap:.2rem;margin-bottom:1.1rem">{rings}</div>'
        + meters
    )


    theme.card(
        '<div class="rf-eyebrow">Qué falta</div>'
        f'<div class="rf-note">{readiness.summary}</div>'
    )

    _strategy(view)
    _key_sessions(view, dashboard)
    _prediction_history(view, dashboard)
    _equivalents(dashboard)
    _goal_controls(view, dashboard, state, is_primary)


def _short_capability(name: str) -> str:
    """Capability names are long; the rings need a label that fits under them."""
    return {
        "Resistencia específica": "Específica",
        "Base aeróbica": "Base",
        "Capacidad de cierre": "Cierre",
    }.get(name, name)


def _strategy(view: GoalView) -> None:
    goal, prediction, readiness = view.goal, view.prediction, view.readiness
    splits, note = race_strategy(goal, prediction.central_s, readiness)
    rows = cumulative_splits(splits)
    if not rows:
        return

    theme.eyebrow("Estrategia de carrera")
    theme.card(f'<div class="rf-note">{note}</div>')

    display = rows if len(rows) <= 6 else rows[:3] + rows[-2:]
    theme.card(
        theme.rows_html(
            [
                (label, f"{fmt_time(segment)}  ·  {fmt_time(elapsed)}")
                for label, segment, elapsed in display
            ]
        )
        + f'<div class="rf-muted" style="margin-top:.55rem">Parcial · acumulado. '
        f"Ritmo medio objetivo {fmt_pace(prediction.central_s / (goal.distance_m / 1000))}.</div>"
    )


def _key_sessions(view: GoalView, dashboard: Dashboard) -> None:
    """The sessions still standing between the athlete and the goal."""
    if not dashboard.plan or dashboard.goals[0].goal.id != view.goal.id:
        return
    pending = [
        session
        for week in dashboard.plan
        for session in week.sessions
        if session.key and session.day >= date.today()
    ][:4]
    if not pending:
        return
    theme.eyebrow("Entrenamientos clave pendientes")
    theme.card(
        theme.rows_html(
            [
                (fmt_day_short(session.day), session.title)
                for session in pending
            ]
        )
    )


def _prediction_history(view: GoalView, dashboard: Dashboard) -> None:
    points = prediction_history(view.goal, dashboard.activities, dashboard.zones, points=12)
    if len(points) < 3:
        return
    theme.eyebrow("Evolución de la predicción")
    st.altair_chart(
        charts.prediction_chart(points, view.goal.target_time_s), use_container_width=True
    )
    first, last = points[0][1], points[-1][1]
    change = first - last
    direction = "mejoró" if change > 0 else "retrocedió"
    explanation(
        f"En las últimas {len(points)} semanas tu predicción {direction} "
        f"{fmt_time(abs(change))}, de {fmt_time(first)} a {fmt_time(last)}. "
        "La línea punteada es tu marca objetivo."
    )


def _equivalents(dashboard: Dashboard) -> None:
    with st.expander("Marcas equivalentes con tu nivel actual"):
        rows = equivalent_performances(dashboard.zones.vdot)
        st.markdown(
            theme.rows_html([(label, fmt_time(seconds)) for label, _, seconds in rows]),
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="rf-muted" style="margin-top:.6rem">Derivadas de un VDOT de '
            f"{fmt_num(dashboard.zones.vdot, 1)}. Son equivalencias, no predicciones: "
            "cada distancia necesita su propia preparación específica.</div>",
            unsafe_allow_html=True,
        )


def _goal_controls(view: GoalView, dashboard: Dashboard, state: AppState, is_primary: bool) -> None:
    st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        if not is_primary and st.button(
            "Hacer principal", use_container_width=True, key=f"primary_{view.goal.id}"
        ):
            state.primary_goal_id = view.goal.id
            save_state(state)
            st.toast(f"{view.goal.name} es ahora tu objetivo principal.")
            st.rerun()
    with right:
        if st.button("Eliminar", use_container_width=True, key=f"delete_{view.goal.id}"):
            state.goals = [goal for goal in state.goals if goal.id != view.goal.id]
            if state.primary_goal_id == view.goal.id:
                state.primary_goal_id = None
            save_state(state)
            st.rerun()


def _add_goal_form(state: AppState) -> None:
    with st.form("add_goal"):
        name = st.text_input("Nombre", placeholder="5K de la ciudad")
        columns = st.columns(2)
        with columns[0]:
            distance_label = st.selectbox("Distancia", list(DISTANCE_OPTIONS), index=4)
        with columns[1]:
            race_date = st.date_input("Fecha", value=date.today() + timedelta(days=42))
        columns = st.columns(2)
        with columns[0]:
            target = st.text_input("Marca objetivo", placeholder="16:59")
        with columns[1]:
            terrain = st.selectbox("Terreno", ["pista", "asfalto", "trail"], index=1)
        priority = st.select_slider(
            "Prioridad", options=["A", "B", "C"], value="A",
            help="A es la carrera alrededor de la cual se construye el plan.",
        )
        if st.form_submit_button("Agregar carrera", type="primary", use_container_width=True):
            if not name.strip():
                st.warning("Poné un nombre para identificar la carrera.")
                return
            target_s = parse_time(target) if target else None
            if target and target_s is None:
                st.warning("No pude leer la marca objetivo. Usá el formato 16:59.")
                return
            goal = Goal.new(
                name.strip(),
                float(DISTANCE_OPTIONS[distance_label]),
                race_date,
                target_time_s=target_s,
                priority=priority,
                terrain=terrain,
            )
            state.goals.append(goal)
            save_state(state)
            st.toast(f"{goal.name} agregada.")
            st.rerun()
