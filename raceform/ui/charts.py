"""Charts.

Every chart is the same system: no chart junk, a single axis line, mono
numerals, red only where it means "you" or "now". Each one returns an Altair
chart the caller places, and each is paired with a written explanation in the
screen rather than left to speak for itself.
"""

from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd

from ..formats import fmt_pace, fmt_time
from . import theme

AXIS = alt.Axis(
    labelColor=theme.MUTED,
    titleColor=theme.MUTED,
    labelFont="-apple-system",
    labelFontSize=10,
    titleFontSize=10,
    tickColor=theme.LINE,
    domainColor=theme.LINE,
    grid=False,
)
Y_AXIS = alt.Axis(
    labelColor=theme.MUTED,
    labelFontSize=10,
    titleColor=theme.MUTED,
    titleFontSize=10,
    grid=True,
    gridColor="#F1F1EE",
    domain=False,
    tickSize=0,
)

# Axes that carry seconds must read as mm:ss — a runner does not think in 206.
_MMSS = (
    "floor(datum.value / 60) + ':' + "
    "(datum.value % 60 < 10 ? '0' : '') + format(datum.value % 60, '.0f')"
)


def _time_axis(title: str | None) -> alt.Axis:
    return alt.Axis(
        labelColor=theme.MUTED,
        labelFontSize=10,
        titleColor=theme.MUTED,
        titleFontSize=10,
        grid=True,
        gridColor="#F1F1EE",
        domain=False,
        tickSize=0,
        title=title,
        labelExpr=_MMSS,
    )


def _base(data: pd.DataFrame, height: int = 190) -> alt.Chart:
    return (
        alt.Chart(data)
        .properties(height=height, width="container")
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont="-apple-system")
    )


def rep_chart(reps: list, target_low: float | None = None, target_high: float | None = None) -> alt.Chart:
    """Pace per repetition, with the prescribed band behind it."""
    frame = pd.DataFrame(
        {
            "rep": [rep.number for rep in reps],
            "pace": [rep.pace_s_km for rep in reps],
            "gap": [rep.gap_s_km for rep in reps],
            "etiqueta": [fmt_pace(rep.pace_s_km) for rep in reps],
            "tiempo": [fmt_time(rep.time_s) for rep in reps],
        }
    )
    layers: list[alt.Chart] = []

    if target_low and target_high:
        band = pd.DataFrame({"low": [min(target_low, target_high)], "high": [max(target_low, target_high)]})
        layers.append(
            alt.Chart(band)
            .mark_rect(color=theme.RED, opacity=0.07)
            .encode(y=alt.Y("low:Q"), y2=alt.Y2("high:Q"))
        )

    line = (
        alt.Chart(frame)
        .mark_line(color=theme.RED, strokeWidth=2, point=False)
        .encode(
            x=alt.X("rep:O", axis=AXIS, title="Repetición"),
            y=alt.Y(
                "pace:Q",
                axis=_time_axis("Ritmo"),
                scale=alt.Scale(zero=False, reverse=True, nice=True),
            ),
        )
    )
    points = (
        alt.Chart(frame)
        .mark_point(color=theme.RED, filled=True, size=52)
        .encode(
            x=alt.X("rep:O"),
            y=alt.Y("pace:Q", scale=alt.Scale(zero=False, reverse=True)),
            tooltip=[
                alt.Tooltip("rep:O", title="Repetición"),
                alt.Tooltip("etiqueta:N", title="Ritmo"),
                alt.Tooltip("tiempo:N", title="Tiempo"),
            ],
        )
    )
    layers.extend([line, points])
    return (
        alt.layer(*layers)
        .properties(height=200, width="container")
        .configure_view(strokeWidth=0)
    )


def weekly_volume_chart(weeks: list, highlight: date | None = None) -> alt.Chart:
    """Weekly kilometres, with quality volume distinguished."""
    frame = pd.DataFrame(
        {
            "semana": [week.start for week in weeks],
            "km": [round(week.km, 1) for week in weeks],
            "calidad": [week.quality_sessions for week in weeks],
            "etiqueta": [week.start.strftime("%d/%m") for week in weeks],
        }
    )
    frame["destacada"] = frame["semana"] == highlight if highlight else False
    return (
        alt.Chart(frame)
        .mark_bar(size=13, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("etiqueta:O", axis=AXIS, title=None, sort=None),
            y=alt.Y("km:Q", axis=Y_AXIS, title="km"),
            color=alt.condition(
                alt.datum.destacada, alt.value(theme.RED), alt.value("#D6D6D2")
            ),
            tooltip=[
                alt.Tooltip("etiqueta:N", title="Semana del"),
                alt.Tooltip("km:Q", title="Kilómetros"),
                alt.Tooltip("calidad:Q", title="Sesiones de calidad"),
            ],
        )
        .properties(height=180, width="container")
        .configure_view(strokeWidth=0)
    )


def load_chart(series: list) -> alt.Chart:
    """Fitness against fatigue over time — the classic pair, minus the clutter."""
    frame = pd.DataFrame(
        {
            "día": [point.day for point in series],
            "Forma": [round(point.fitness, 1) for point in series],
            "Fatiga": [round(point.fatigue, 1) for point in series],
        }
    ).melt("día", var_name="serie", value_name="valor")

    return (
        alt.Chart(frame)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("día:T", axis=AXIS, title=None),
            y=alt.Y("valor:Q", axis=Y_AXIS, title=None),
            color=alt.Color(
                "serie:N",
                scale=alt.Scale(domain=["Forma", "Fatiga"], range=[theme.INK, theme.RED]),
                legend=alt.Legend(orient="top", title=None, labelColor=theme.MUTED, labelFontSize=11),
            ),
            tooltip=[
                alt.Tooltip("día:T", title="Día"),
                alt.Tooltip("serie:N", title=""),
                alt.Tooltip("valor:Q", title="Valor", format=".0f"),
            ],
        )
        .properties(height=190, width="container")
        .configure_view(strokeWidth=0)
    )


def prediction_chart(points: list[tuple[date, float]], target_s: float | None = None) -> alt.Chart:
    """How the predicted race time evolved."""
    frame = pd.DataFrame(
        {
            "día": [day for day, _ in points],
            "segundos": [seconds for _, seconds in points],
            "tiempo": [fmt_time(seconds) for _, seconds in points],
        }
    )
    line = (
        alt.Chart(frame)
        .mark_line(color=theme.RED, strokeWidth=2, point=alt.OverlayMarkDef(color=theme.RED, size=38))
        .encode(
            x=alt.X("día:T", axis=AXIS, title=None),
            y=alt.Y(
                "segundos:Q",
                axis=_time_axis("Predicción"),
                scale=alt.Scale(zero=False, reverse=True, nice=True),
            ),
            tooltip=[alt.Tooltip("día:T", title="Fecha"), alt.Tooltip("tiempo:N", title="Predicción")],
        )
    )
    layers = [line]
    if target_s:
        target = pd.DataFrame({"objetivo": [target_s]})
        layers.append(
            alt.Chart(target)
            .mark_rule(color=theme.INK, strokeDash=[4, 3], strokeWidth=1)
            .encode(y=alt.Y("objetivo:Q"))
        )
    return alt.layer(*layers).properties(height=190, width="container").configure_view(strokeWidth=0)


def pace_trend_chart(activities: list, label: str = "Ritmo") -> alt.Chart:
    """Pace over time for one family of sessions."""
    frame = pd.DataFrame(
        {
            "día": [activity.day for activity in activities],
            "ritmo": [activity.pace_s_km for activity in activities],
            "etiqueta": [fmt_pace(activity.pace_s_km) for activity in activities],
            "km": [round(activity.km, 1) for activity in activities],
        }
    )
    points = (
        alt.Chart(frame)
        .mark_point(color=theme.RED, filled=True, size=44, opacity=0.75)
        .encode(
            x=alt.X("día:T", axis=AXIS, title=None),
            y=alt.Y("ritmo:Q", axis=_time_axis(label), scale=alt.Scale(zero=False, reverse=True)),
            tooltip=[
                alt.Tooltip("día:T", title="Fecha"),
                alt.Tooltip("etiqueta:N", title="Ritmo"),
                alt.Tooltip("km:Q", title="km"),
            ],
        )
    )
    trend = points.transform_regression("día", "ritmo").mark_line(
        color=theme.INK, strokeWidth=1.5, opacity=0.55
    )
    return alt.layer(points, trend).properties(height=190, width="container").configure_view(strokeWidth=0)


def hr_chart(activities: list) -> alt.Chart:
    """Average heart rate against pace — efficiency drifting over a block."""
    usable = [activity for activity in activities if activity.average_heartrate]
    frame = pd.DataFrame(
        {
            "día": [activity.day for activity in usable],
            "pulso": [activity.average_heartrate for activity in usable],
            "ritmo": [fmt_pace(activity.pace_s_km) for activity in usable],
        }
    )
    return (
        alt.Chart(frame)
        .mark_point(color=theme.RED, filled=True, size=40, opacity=0.7)
        .encode(
            x=alt.X("día:T", axis=AXIS, title=None),
            y=alt.Y("pulso:Q", axis=Y_AXIS, title="ppm", scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("día:T", title="Fecha"),
                alt.Tooltip("pulso:Q", title="Pulso medio"),
                alt.Tooltip("ritmo:N", title="Ritmo"),
            ],
        )
        .properties(height=180, width="container")
        .configure_view(strokeWidth=0)
    )


def consistency_chart(analyses: list) -> alt.Chart:
    """Dispersion between reps, session by session. Lower is better."""
    rows = []
    for analysis in analyses:
        if not analysis.reps:
            continue
        dispersion = analysis.metrics.get("Dispersión", "")
        try:
            value = float(dispersion.replace(" %", "").replace(",", "."))
        except ValueError:
            continue
        rows.append({"día": analysis.activity.day, "dispersión": value, "sesión": analysis.title})
    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame({"día": [], "dispersión": [], "sesión": []})
    return (
        alt.Chart(frame)
        .mark_bar(size=10, color=theme.RED, opacity=0.8, cornerRadius=2)
        .encode(
            x=alt.X("día:T", axis=AXIS, title=None),
            y=alt.Y("dispersión:Q", axis=Y_AXIS, title="% de dispersión"),
            tooltip=[
                alt.Tooltip("día:T", title="Fecha"),
                alt.Tooltip("sesión:N", title="Sesión"),
                alt.Tooltip("dispersión:Q", title="Dispersión %", format=".1f"),
            ],
        )
        .properties(height=180, width="container")
        .configure_view(strokeWidth=0)
    )
