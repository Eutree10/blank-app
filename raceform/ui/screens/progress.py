"""Progreso — the only screen that shows evolution.

Charts live here and nowhere else. Every one is followed by the sentence that
says what changed and why, because a line going down is not an insight.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from ...engine import Dashboard
from ...formats import fmt_num, fmt_pace, fmt_time
from ...models import WorkoutType, week_start
from ...store import AppState
from .. import charts, theme
from ..components import explanation, session_teaser

VIEWS = [
    "Kilometraje",
    "Carga",
    "Ritmos",
    "Series",
    "Pulso",
]


def render(dashboard: Dashboard, state: AppState) -> None:
    theme.screen_header("Progreso", "Cómo evolucionan tus indicadores")

    if len(dashboard.activities) < 5:
        theme.card(
            '<div class="rf-muted">Todavía no hay historial suficiente para mostrar '
            "tendencias. Importá tus actividades desde Perfil.</div>"
        )
        return

    _milestones(dashboard)

    choice = st.segmented_control(
        "Indicador", VIEWS, default="Kilometraje", label_visibility="collapsed"
    ) or "Kilometraje"

    if choice == "Kilometraje":
        _volume(dashboard)
    elif choice == "Carga":
        _load(dashboard)
    elif choice == "Ritmos":
        _paces(dashboard)
    elif choice == "Series":
        _intervals(dashboard)
    else:
        _heart_rate(dashboard)

    _week_detail(dashboard)


def _milestones(dashboard: Dashboard) -> None:
    if not dashboard.milestones:
        return
    theme.eyebrow("Hitos")
    for milestone in dashboard.milestones[:2]:
        theme.card(
            f'<div class="rf-note" style="font-weight:560;color:{theme.INK}">'
            f"{milestone.headline}</div>"
            f'<div class="rf-muted" style="margin-top:.3rem">{milestone.detail}</div>',
            accent=True,
        )


def _volume(dashboard: Dashboard) -> None:
    weeks = dashboard.weeks[-14:]
    selected = st.session_state.get("selected_week")
    st.altair_chart(
        charts.weekly_volume_chart(weeks, highlight=selected), use_container_width=True
    )

    complete = [week for week in weeks if week.start < week_start(date.today())]
    if len(complete) >= 5:
        recent = sum(week.km for week in complete[-4:]) / 4
        earlier = sum(week.km for week in complete[-8:-4]) / max(len(complete[-8:-4]), 1)
        change = recent - earlier
        direction = "más" if change > 0 else "menos"
        explanation(
            f"Promediás {fmt_num(recent, 0)} km en las últimas 4 semanas, "
            f"{fmt_num(abs(change), 0)} km {direction} que el bloque anterior. "
            f"La tirada más larga fue de {fmt_num(max(week.long_run_km for week in complete[-4:]), 1)} km."
        )

    _week_picker(dashboard)


def _load(dashboard: Dashboard) -> None:
    series = dashboard.load.series[-120:]
    st.altair_chart(charts.load_chart(series), use_container_width=True)
    load = dashboard.load
    ramp = load.ramp_rate(28)
    acwr = load.acwr()
    if load.form < -0.15 * max(load.fitness, 1):
        state_note = "Estás en déficit: la fatiga supera lo que venís construyendo."
    elif load.form > 0.05 * max(load.fitness, 1):
        state_note = "Estás fresco: buen momento para un test o una competencia."
    else:
        state_note = "Carga y recuperación en equilibrio."
    risk = (
        "Tu ratio agudo/crónico está alto: el salto de volumen reciente sube el riesgo de lesión."
        if acwr > 1.4
        else "Tu progresión de carga está dentro de un rango seguro."
    )
    explanation(
        f"{state_note} Tu forma cambió {fmt_num(ramp, 0)} puntos en 4 semanas "
        f"y el ratio agudo/crónico es {fmt_num(acwr, 2)}. {risk}"
    )


def _paces(dashboard: Dashboard) -> None:
    easy = [
        analysis.activity for analysis in dashboard.analyses
        if analysis.workout_type is WorkoutType.EASY
    ][-40:]
    if len(easy) < 4:
        st.info("Faltan rodajes registrados para mostrar la tendencia.")
        return
    st.altair_chart(charts.pace_trend_chart(easy, "Ritmo de rodaje"), use_container_width=True)

    half = len(easy) // 2
    early = sum(activity.pace_s_km for activity in easy[:half]) / half
    late = sum(activity.pace_s_km for activity in easy[half:]) / (len(easy) - half)
    change = early - late
    fast_bound = dashboard.zones.easy[0]
    discipline = (
        "Están dentro del rango fácil."
        if late >= fast_bound
        else f"Están por encima del techo fácil ({fmt_pace(fast_bound)}): estás corriendo los rodajes demasiado rápido."
    )
    direction = "más rápidos" if change > 0 else "más lentos"
    explanation(
        f"Tus rodajes son {fmt_num(abs(change), 0)} s/km {direction} que al principio del bloque "
        f"({fmt_pace(early)} → {fmt_pace(late)}). {discipline}"
    )


def _intervals(dashboard: Dashboard) -> None:
    structured = [analysis for analysis in dashboard.analyses if analysis.reps][-20:]
    if len(structured) < 3:
        st.info("Faltan sesiones de series para mostrar la consistencia.")
        return
    st.altair_chart(charts.consistency_chart(structured), use_container_width=True)

    values = []
    for analysis in structured:
        try:
            values.append(float(analysis.metrics["Dispersión"].replace(" %", "").replace(",", ".")))
        except (KeyError, ValueError):
            continue
    if values:
        half = len(values) // 2 or 1
        early = sum(values[:half]) / half
        late = sum(values[half:]) / max(len(values) - half, 1)
        better = late < early
        explanation(
            f"La dispersión entre repeticiones pasó de {fmt_num(early, 1)} % a {fmt_num(late, 1)} %. "
            + (
                "Estás ejecutando las series de forma más pareja, que es la señal de que el ritmo está asimilado."
                if better
                else "Estás ejecutando con más variación: revisá el ritmo de arranque de cada serie."
            )
        )


def _heart_rate(dashboard: Dashboard) -> None:
    with_hr = [
        analysis.activity for analysis in dashboard.analyses
        if analysis.workout_type in {WorkoutType.EASY, WorkoutType.LONG}
        and analysis.activity.average_heartrate
    ][-40:]
    if len(with_hr) < 5:
        st.info("Faltan actividades con frecuencia cardíaca.")
        return
    st.altair_chart(charts.hr_chart(with_hr), use_container_width=True)
    half = len(with_hr) // 2
    early_hr = sum(a.average_heartrate for a in with_hr[:half]) / half
    late_hr = sum(a.average_heartrate for a in with_hr[half:]) / (len(with_hr) - half)
    early_pace = sum(a.pace_s_km for a in with_hr[:half]) / half
    late_pace = sum(a.pace_s_km for a in with_hr[half:]) / (len(with_hr) - half)
    faster = early_pace - late_pace
    lower = early_hr - late_hr
    # Thresholds match what the sentence displays: claiming "less pulse" when
    # both figures round to the same number reads as a contradiction.
    if faster > 1 and lower > 1.5:
        note = "Corrés más rápido con menos pulso: la eficiencia aeróbica mejoró."
    elif faster > 1:
        note = "Corrés más rápido a igual pulso: hay progreso aeróbico."
    elif lower > 1.5:
        note = "Mismo ritmo con menos pulso: mejor economía o más frescura."
    else:
        note = "Sin cambios claros en la relación pulso/ritmo en este bloque."
    explanation(
        f"Pulso medio en aeróbico: {early_hr:.0f} → {late_hr:.0f} ppm, "
        f"con ritmos de {fmt_pace(early_pace)} → {fmt_pace(late_pace)}. {note}"
    )


def _week_picker(dashboard: Dashboard) -> None:
    weeks = [week for week in dashboard.weeks[-12:]]
    labels = {week.start.strftime("%d/%m"): week.start for week in weeks}
    choice = st.selectbox(
        "Ver el detalle de una semana",
        ["—"] + list(labels),
        index=0,
        key="week_select",
    )
    st.session_state.selected_week = labels.get(choice)


def _week_detail(dashboard: Dashboard) -> None:
    start = st.session_state.get("selected_week")
    if not start:
        return
    end = start + timedelta(days=7)
    analyses = [
        analysis for analysis in dashboard.analyses
        if start <= analysis.activity.day < end
    ]
    if not analyses:
        return

    week = next((week for week in dashboard.weeks if week.start == start), None)
    if week:
        theme.eyebrow(f"Semana del {start.strftime('%d/%m')}")
        theme.card(
            theme.rows_html(
                [
                    ("Kilómetros", f"{fmt_num(week.km, 1)} km"),
                    ("Sesiones", str(week.sessions)),
                    ("Calidad", str(week.quality_sessions)),
                    ("Tirada larga", f"{fmt_num(week.long_run_km, 1)} km"),
                    ("Tiempo total", fmt_time(week.minutes * 60)),
                ]
            )
        )
    for analysis in analyses:
        session_teaser(analysis)
        if st.button(
            "Ver análisis", key=f"week_open_{analysis.activity.id}", use_container_width=True
        ):
            st.session_state.selected_activity = analysis.activity.id
            st.session_state.previous_screen = "progreso"
            st.session_state.screen = "sesion"
            st.rerun()
