"""Session analysis — what happened, not just what was recorded."""

from __future__ import annotations

import streamlit as st

from ...engine import Dashboard
from ...formats import fmt_day_long, fmt_num, fmt_pace, fmt_time
from ...store import AppState
from .. import charts, theme
from ..components import feedback_form


def render(dashboard: Dashboard, state: AppState) -> None:
    activity_id = st.session_state.get("selected_activity")
    analysis = dashboard.analysis_for(activity_id) if activity_id else None
    if analysis is None:
        analysis = dashboard.analyses[-1] if dashboard.analyses else None
    if analysis is None:
        theme.screen_header("Sesión", "Sin actividades")
        return

    if st.button("‹ Volver", key="session_back"):
        st.session_state.screen = st.session_state.get("previous_screen", "hoy")
        st.rerun()

    theme.screen_header(
        analysis.title,
        f"{fmt_day_long(analysis.activity.day).capitalize()} · {analysis.workout_type.label}",
    )

    _score_block(analysis)
    _rep_detail(analysis)
    _metrics(analysis)
    _capability_and_advice(analysis)
    _feedback(analysis, state)


def _score_block(analysis) -> None:
    color = theme.score_color(analysis.score * 10)
    flags = "".join(
        f'<div class="rf-muted" style="color:{theme.BAD};margin-top:.35rem">⚠ {flag}</div>'
        for flag in analysis.flags
    )
    theme.card(
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem">'
        f'<div style="flex:1">'
        f'<div class="rf-eyebrow">Qué pasó</div>'
        f'<div class="rf-note">{analysis.verdict}</div>'
        f"{flags}</div>"
        f'<div style="text-align:right">'
        f'<div class="rf-value" style="font-size:2rem;color:{color};line-height:1">'
        f'{fmt_num(analysis.score, 1)}</div>'
        f'<div class="rf-muted" style="font-size:.72rem">de 10</div>'
        f"</div></div>",
        accent=True,
    )
    if analysis.comparison:
        theme.card(
            '<div class="rf-eyebrow">Comparación</div>'
            f'<div class="rf-note">{analysis.comparison}</div>'
        )


def _rep_detail(analysis) -> None:
    if not analysis.reps:
        return
    theme.eyebrow("Evolución del ritmo")
    st.altair_chart(charts.rep_chart(analysis.reps), use_container_width=True)
    st.markdown(
        f'<div class="rf-muted" style="margin:-.5rem 0 1rem 0">'
        f"{theme_shape_label(analysis)}</div>",
        unsafe_allow_html=True,
    )

    with st.expander(f"Ver las {len(analysis.reps)} repeticiones"):
        rows = []
        for rep in analysis.reps:
            recovery = fmt_time(rep.recovery_s) if rep.recovery_s else "—"
            hr = f"{rep.hr:.0f}" if rep.hr else "—"
            rows.append(
                {
                    "#": rep.number,
                    "Distancia": f"{rep.distance_m:.0f} m",
                    "Tiempo": fmt_time(rep.time_s),
                    "Ritmo": fmt_pace(rep.pace_s_km),
                    "Pulso": hr,
                    "Recuperación": recovery,
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)


def theme_shape_label(analysis) -> str:
    from ...analysis.session import SHAPE_LABELS

    label = SHAPE_LABELS.get(analysis.shape, "")
    dispersion = analysis.metrics.get("Dispersión", "")
    drift = analysis.metrics.get("Deriva 1ª/2ª mitad", "")
    parts = [part for part in [label, f"dispersión {dispersion}" if dispersion else "",
                               f"deriva {drift}" if drift else ""] if part]
    return " · ".join(parts)


def _metrics(analysis) -> None:
    theme.eyebrow("Números de la sesión")
    theme.card(theme.rows_html(list(analysis.metrics.items())))


def _capability_and_advice(analysis) -> None:
    if analysis.capability:
        theme.card(
            '<div class="rf-eyebrow">Qué capacidad trabajaste</div>'
            f'<div style="font-size:1rem;font-weight:600;color:{theme.INK}">'
            f"{analysis.capability.value}</div>"
            f'<div class="rf-muted" style="margin-top:.25rem">{analysis.capability_note}</div>'
        )
    if analysis.advice:
        theme.card(
            '<div class="rf-eyebrow">Qué cambiar la próxima vez</div>'
            f'<div class="rf-note">{analysis.advice}</div>'
        )


def _feedback(analysis, state: AppState) -> None:
    existing = state.feedback.get(analysis.activity.id)
    label = "Tu lectura de la sesión" if not existing else "Actualizar tu lectura"
    with st.expander(label, expanded=not existing):
        feedback_form(analysis.activity.id, state, key="session_detail")
