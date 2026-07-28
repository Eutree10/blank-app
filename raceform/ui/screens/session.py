"""Session analysis — what happened, not just what was recorded."""

from __future__ import annotations

import statistics

import streamlit as st

from ...engine import Dashboard
from ...formats import fmt_day_long, fmt_num, fmt_pace, fmt_time
from ...store import AppState
from .. import charts, theme, visuals
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
    _headline_numbers(analysis)
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
        _split_detail(analysis)
        return

    theme.eyebrow("Repeticiones")
    mean_pace = statistics.mean(rep.pace_s_km for rep in analysis.reps)
    rows = [
        (
            str(rep.number),
            fmt_time(rep.time_s),
            rep.gap_s_km,
            (rep.pace_s_km - mean_pace) * (rep.distance_m / 1000),
        )
        for rep in analysis.reps
    ]
    theme.card(
        visuals.delta_bars(rows)
        + f'<div class="rf-muted" style="margin-top:.6rem">Barra más larga = repetición más '
        f"rápida. La última columna es la diferencia en segundos contra el promedio "
        f"({fmt_pace(mean_pace)}). {theme_shape_label(analysis)}.</div>"
    )

    with st.expander("Ver la evolución del ritmo"):
        st.altair_chart(charts.rep_chart(analysis.reps), use_container_width=True)
        table = []
        for rep in analysis.reps:
            table.append(
                {
                    "#": rep.number,
                    "Distancia": f"{rep.distance_m:.0f} m",
                    "Tiempo": fmt_time(rep.time_s),
                    "Ritmo": fmt_pace(rep.pace_s_km),
                    "Pulso": f"{rep.hr:.0f}" if rep.hr else "—",
                    "Recuperación": fmt_time(rep.recovery_s) if rep.recovery_s else "—",
                }
            )
        st.dataframe(table, use_container_width=True, hide_index=True)


def _split_detail(analysis) -> None:
    """Kilometre splits for a continuous run, same treatment as reps."""
    splits = [
        lap for lap in (analysis.activity.splits_km or analysis.activity.laps)
        if lap.distance_m > 400
    ]
    if len(splits) < 3:
        return

    theme.eyebrow("Parciales")
    mean_pace = statistics.mean(lap.pace_s_km for lap in splits)
    rows = [
        (
            str(index + 1),
            fmt_pace(lap.pace_s_km, suffix=""),
            lap.pace_s_km,
            (lap.pace_s_km - mean_pace) * (lap.distance_m / 1000),
        )
        for index, lap in enumerate(splits[:20])
    ]
    theme.card(
        visuals.delta_bars(rows)
        + f'<div class="rf-muted" style="margin-top:.6rem">Diferencia en segundos contra tu '
        f"ritmo medio de {fmt_pace(mean_pace)}.</div>"
    )


def theme_shape_label(analysis) -> str:
    from ...analysis.session import SHAPE_LABELS

    label = SHAPE_LABELS.get(analysis.shape, "")
    dispersion = analysis.metrics.get("Dispersión", "")
    drift = analysis.metrics.get("Deriva 1ª/2ª mitad", "")
    parts = [part for part in [label, f"dispersión {dispersion}" if dispersion else "",
                               f"deriva {drift}" if drift else ""] if part]
    return " · ".join(parts)


def _headline_numbers(analysis) -> None:
    """The six numbers a runner checks first, before any of the analysis."""
    activity = analysis.activity
    tiles = [
        ("clock", fmt_time(activity.moving_time_s), "Duración"),
        ("gauge", fmt_pace(activity.pace_s_km, suffix=""), "Ritmo /km"),
    ]
    if activity.average_heartrate:
        tiles.append(("heart", f"{activity.average_heartrate:.0f}", "Pulso medio"))
    tiles.append(("route", fmt_num(activity.km, 2), "Distancia km"))
    if activity.average_cadence:
        tiles.append(("steps", f"{activity.average_cadence:.0f}", "Cadencia"))
    if activity.elevation_gain_m:
        tiles.append(("mountain", f"{activity.elevation_gain_m:.0f}", "Desnivel m"))

    theme.card(visuals.metric_grid(tiles[:6], columns=3))


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
