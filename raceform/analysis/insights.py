"""Insights: habit correlations and training milestones.

Habits only earn a place in the app when they demonstrably move performance,
so nothing here awards points for logging. Each insight compares two real
groups of sessions and reports the measured difference, or stays silent.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, timedelta

from ..formats import fmt_num, fmt_pace
from ..models import Activity, Feedback, HabitDay, WorkoutType
from .physiology import PaceZones, lap_pace
from .session import SessionAnalysis

MIN_GROUP = 3  # never claim a pattern from fewer sessions than this


@dataclass
class Insight:
    """One observed relationship, with the evidence attached."""

    headline: str
    detail: str
    strength: str  # fuerte | moderada | débil
    sample: int


def _second_half_drop(activity: Activity) -> float | None:
    """How much pace decayed in the second half, as a fraction."""
    splits = activity.splits_km or activity.laps
    usable = [lap for lap in splits if lap.distance_m > 700]
    if len(usable) < 4:
        return None
    half = len(usable) // 2
    first = statistics.mean(lap_pace(lap) for lap in usable[:half])
    second = statistics.mean(lap_pace(lap) for lap in usable[half:])
    if first <= 0:
        return None
    return (second - first) / first


def sleep_insight(
    activities: list[Activity], habits: dict[date, HabitDay], threshold_h: float = 7.0
) -> Insight | None:
    """Do sessions after short nights actually go worse?"""
    short_nights: list[float] = []
    normal_nights: list[float] = []

    for activity in activities:
        previous = habits.get(activity.day - timedelta(days=1))
        if not previous or previous.sleep_hours is None:
            continue
        drop = _second_half_drop(activity)
        if drop is None:
            continue
        (short_nights if previous.sleep_hours < threshold_h else normal_nights).append(drop)

    if len(short_nights) < MIN_GROUP or len(normal_nights) < MIN_GROUP:
        return None

    short_mean = statistics.mean(short_nights)
    normal_mean = statistics.mean(normal_nights)
    difference = short_mean - normal_mean
    if abs(difference) < 0.008:
        return None

    direction = "cayó" if difference > 0 else "mejoró"
    return Insight(
        headline=(
            f"En las últimas {len(short_nights)} sesiones realizadas después de dormir "
            f"menos de {fmt_num(threshold_h, 0)} horas, tu ritmo {direction} un promedio de "
            f"{fmt_num(abs(difference) * 100, 1)} % en la segunda mitad."
        ),
        detail=(
            f"Comparado con {len(normal_nights)} sesiones tras noches más largas "
            f"({fmt_num(normal_mean * 100, 1)} % de deriva frente a {fmt_num(short_mean * 100, 1)} %)."
        ),
        strength=_strength(abs(difference), len(short_nights), scale=0.03),
        sample=len(short_nights) + len(normal_nights),
    )


def strength_insight(
    analyses: list[SessionAnalysis], habits: dict[date, HabitDay]
) -> Insight | None:
    """Does the strength work show up in session quality?"""
    with_strength: list[float] = []
    without: list[float] = []
    for analysis in analyses:
        if not analysis.workout_type.is_quality:
            continue
        window = [
            habits[day] for day in (
                analysis.activity.day - timedelta(days=offset) for offset in range(1, 8)
            ) if day in habits
        ]
        if len(window) < 4:
            continue
        (with_strength if any(habit.strength for habit in window) else without).append(analysis.score)

    if len(with_strength) < MIN_GROUP or len(without) < MIN_GROUP:
        return None
    difference = statistics.mean(with_strength) - statistics.mean(without)
    if abs(difference) < 0.3:
        return None
    direction = "mejores" if difference > 0 else "peores"
    return Insight(
        headline=(
            f"Tus sesiones de calidad puntúan {fmt_num(abs(difference), 1)} puntos {direction} "
            "en las semanas con trabajo de fuerza."
        ),
        detail=f"{len(with_strength)} sesiones con fuerza frente a {len(without)} sin fuerza.",
        strength=_strength(abs(difference), len(with_strength), scale=1.5),
        sample=len(with_strength) + len(without),
    )


def niggle_insight(
    activities: list[Activity], feedback: dict[str, Feedback], zones: PaceZones
) -> Insight | None:
    """Do niggles follow a particular kind of load?"""
    flagged = [
        activity for activity in activities
        if feedback.get(activity.id) and feedback[activity.id].niggle_severity >= 1
    ]
    if len(flagged) < MIN_GROUP:
        return None

    from .classify import classify

    kinds = [classify(activity, zones).workout_type for activity in flagged]
    most_common = max(set(kinds), key=kinds.count)
    share = kinds.count(most_common) / len(kinds)
    if share < 0.45:
        return None
    return Insight(
        headline=(
            f"{kinds.count(most_common)} de tus {len(kinds)} molestias aparecieron en sesiones "
            f"de {most_common.value}."
        ),
        detail="Vale la pena revisar calzado, superficie o la progresión de ese estímulo.",
        strength=_strength(share, len(flagged), scale=1.0),
        sample=len(flagged),
    )


def _strength(effect: float, sample: int, scale: float) -> str:
    magnitude = min(1.0, effect / scale)
    if sample >= 8 and magnitude > 0.55:
        return "fuerte"
    if sample >= 5 and magnitude > 0.3:
        return "moderada"
    return "débil"


def collect_insights(
    activities: list[Activity],
    analyses: list[SessionAnalysis],
    feedback: dict[str, Feedback],
    habits: dict[date, HabitDay],
    zones: PaceZones,
) -> list[Insight]:
    """Every relationship that survived its own significance check."""
    candidates = [
        sleep_insight(activities, habits),
        strength_insight(analyses, habits),
        niggle_insight(activities, feedback, zones),
    ]
    found = [insight for insight in candidates if insight]
    order = {"fuerte": 0, "moderada": 1, "débil": 2}
    return sorted(found, key=lambda insight: order[insight.strength])


# --- milestones --------------------------------------------------------------

@dataclass
class Milestone:
    day: date
    headline: str
    detail: str


def detect_milestones(analyses: list[SessionAnalysis], limit: int = 5) -> list[Milestone]:
    """Concrete improvements worth telling the athlete about."""
    milestones: list[Milestone] = []
    ordered = sorted(analyses, key=lambda analysis: analysis.activity.start_date)

    # Rep sessions that improved against the same session a month or more ago.
    by_shape: dict[tuple[WorkoutType, int], list[SessionAnalysis]] = {}
    for analysis in ordered:
        if not analysis.reps:
            continue
        nominal = int(analysis.classification.segmentation.nominal_rep_distance_m)
        by_shape.setdefault((analysis.workout_type, nominal), []).append(analysis)

    for (workout_type, nominal), group in by_shape.items():
        if len(group) < 2:
            continue
        latest = group[-1]
        earlier = [
            analysis for analysis in group[:-1]
            if (latest.activity.day - analysis.activity.day).days >= 21
        ]
        if not earlier:
            continue
        reference = earlier[-1]
        latest_pace = statistics.mean(rep.gap_s_km for rep in latest.reps)
        reference_pace = statistics.mean(rep.gap_s_km for rep in reference.reps)
        gain_per_rep = (reference_pace - latest_pace) * (nominal / 1000)
        if gain_per_rep < 1.0:
            continue

        latest_recovery = _mean_recovery(latest)
        reference_recovery = _mean_recovery(reference)
        recovery_note = ""
        if latest_recovery and reference_recovery:
            change = latest_recovery - reference_recovery
            recovery_note = (
                " manteniendo una recuperación similar."
                if abs(change) < 12
                else f" con {fmt_num(abs(change), 0)} s {'más' if change > 0 else 'menos'} de recuperación."
            )
        milestones.append(
            Milestone(
                day=latest.activity.day,
                headline=(
                    f"Tus series de {nominal} m mejoraron {fmt_num(gain_per_rep, 0)} segundos "
                    f"por repetición{recovery_note or '.'}"
                ),
                detail=(
                    f"De {fmt_pace(reference_pace)} el {reference.activity.day.strftime('%d/%m')} "
                    f"a {fmt_pace(latest_pace)} el {latest.activity.day.strftime('%d/%m')}."
                ),
            )
        )

    # Best session of the block — quality only. A 10/10 easy run means the
    # athlete jogged at the right pace, which is not a milestone.
    quality = [analysis for analysis in ordered if analysis.workout_type.is_quality]
    best = max(quality, key=lambda analysis: analysis.score, default=None)
    if best and best.score >= 9:
        milestones.append(
            Milestone(
                day=best.activity.day,
                headline=f"Tu mejor sesión del bloque: {best.title} con {fmt_num(best.score, 1)}/10.",
                detail=best.verdict,
            )
        )

    milestones.sort(key=lambda milestone: milestone.day, reverse=True)
    return milestones[:limit]


def _mean_recovery(analysis: SessionAnalysis) -> float | None:
    values = [rep.recovery_s for rep in analysis.reps if rep.recovery_s]
    return statistics.mean(values) if values else None
