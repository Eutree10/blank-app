"""Race readiness broken into the five capabilities that decide a result.

A single "you are 82% ready" number is useless without knowing which 18% is
missing. Each capability is measured against what the *specific goal* demands,
so the same athlete can be ready for 1500 m and short for 5K.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, timedelta

from ..formats import fmt_num, fmt_pace
from ..models import Activity, Capability, Feedback, Goal, WorkoutType
from .classify import classify
from .physiology import (
    PaceZones,
    activity_pace,
    lap_pace,
    time_for_distance,
)
from .predict import required_vdot

# How much each capability matters, by race distance.
WEIGHTS: dict[str, dict[Capability, float]] = {
    "short": {  # 800–1500 m
        Capability.SPEED: 0.32,
        Capability.SPECIFIC_ENDURANCE: 0.28,
        Capability.AEROBIC_BASE: 0.15,
        Capability.CLOSING: 0.15,
        Capability.RECOVERY: 0.10,
    },
    "middle": {  # 2000–3000 m
        Capability.SPEED: 0.22,
        Capability.SPECIFIC_ENDURANCE: 0.33,
        Capability.AEROBIC_BASE: 0.20,
        Capability.CLOSING: 0.15,
        Capability.RECOVERY: 0.10,
    },
    "long": {  # 5 km and up
        Capability.SPEED: 0.15,
        Capability.SPECIFIC_ENDURANCE: 0.35,
        Capability.AEROBIC_BASE: 0.25,
        Capability.CLOSING: 0.15,
        Capability.RECOVERY: 0.10,
    },
}


def weight_profile(distance_m: float) -> dict[Capability, float]:
    if distance_m <= 1600:
        return WEIGHTS["short"]
    if distance_m <= 3200:
        return WEIGHTS["middle"]
    return WEIGHTS["long"]


@dataclass
class CapabilityScore:
    capability: Capability
    score: int  # 0–100
    detail: str  # the measurement behind the number
    gap: str  # what is missing, empty when there is no gap


@dataclass
class RaceReadiness:
    goal: Goal
    overall: int
    capabilities: list[CapabilityScore]
    limiter: CapabilityScore
    summary: str

    def by(self, capability: Capability) -> CapabilityScore:
        for score in self.capabilities:
            if score.capability is capability:
                return score
        raise KeyError(capability)


def _ratio_score(actual: float, required: float, tolerance: float = 0.09, anchor: int = 65) -> int:
    """`anchor` when the requirement is exactly met, 100 at `tolerance` above it.

    The requirements below are already demanding standards, so meeting one is a
    good score rather than a bare pass — hence the anchor sits well above 50.
    """
    if required <= 0:
        return anchor
    relative = actual / required - 1.0
    span = 100 - anchor
    return int(max(0, min(100, round(anchor + span * relative / tolerance))))


def _recent(activities: list[Activity], days: int, as_of: date | None = None) -> list[Activity]:
    reference = as_of or (max((act.day for act in activities), default=date.today()))
    cutoff = reference - timedelta(days=days)
    return [act for act in activities if act.day >= cutoff]


# --- individual capabilities -------------------------------------------------

def _speed(activities: list[Activity], zones: PaceZones, goal: Goal, goal_vdot: float) -> CapabilityScore:
    """Can the athlete access paces well faster than race pace?"""
    best_velocity = 0.0
    best_detail = ""
    for activity in _recent(activities, 56):
        classification = classify(activity, zones)
        seg = classification.segmentation
        # Hill reps are excluded: on a steep gradient the flat-equivalent pace
        # is too sensitive to the elevation estimate to stand as a speed mark.
        if not seg.structured or classification.workout_type is WorkoutType.HILLS:
            continue
        short = [lap for lap in seg.work if lap.distance_m <= 1000]
        if len(short) < 2:
            continue
        # Median rather than best single rep: one flyer is not speed.
        paces = sorted(lap_pace(lap) for lap in short)
        representative = paces[max(0, len(paces) // 3)]
        if representative <= 0:
            continue
        velocity = 1000 / representative
        if velocity > best_velocity:
            best_velocity = velocity
            best_detail = (
                f"{len(short)} × {seg.nominal_rep_distance_m:.0f} m a "
                f"{fmt_pace(representative)} ({activity.day.strftime('%d/%m')})"
            )

    if best_velocity <= 0:
        return CapabilityScore(
            Capability.SPEED, 40,
            "Sin repeticiones cortas registradas en las últimas 8 semanas.",
            "Falta trabajo de velocidad para tener margen sobre el ritmo objetivo.",
        )

    actual_pace = 1000 / best_velocity
    goal_pace = goal.target_pace_s_km or (time_for_distance(goal.distance_m, goal_vdot) / (goal.distance_m / 1000))
    # Reps should sit faster than race pace, but the margin shrinks as the race
    # gets shorter: a 1500 is run close to rep pace, a 5K is not.
    if goal.distance_m <= 1600:
        margin = 0.03
    elif goal.distance_m <= 3200:
        margin = 0.05
    else:
        margin = 0.07
    required_pace = goal_pace * (1 - margin)
    score = _ratio_score(required_pace / actual_pace, 1.0, tolerance=0.07)

    gap = ""
    if actual_pace > required_pace:
        gap = (
            f"Tus repeticiones cortas están a {fmt_pace(actual_pace)} y el objetivo pide "
            f"al menos {fmt_pace(required_pace)}."
        )
    return CapabilityScore(Capability.SPEED, score, f"Mejor referencia: {best_detail}.", gap)


def _specific_endurance(
    activities: list[Activity], zones: PaceZones, goal: Goal, goal_vdot: float
) -> CapabilityScore:
    """Volume accumulated at or near goal pace — the quality that decides the race."""
    goal_pace = goal.target_pace_s_km or (time_for_distance(goal.distance_m, goal_vdot) / (goal.distance_m / 1000))
    threshold_pace = goal_pace * 1.04  # within 4% of goal pace counts as specific
    window = _recent(activities, 28)

    specific_m = 0.0
    longest_block_m = 0.0
    for activity in window:
        classification = classify(activity, zones)
        seg = classification.segmentation
        if seg.structured:
            qualifying = [
                lap for lap in seg.work
                if lap_pace(lap) <= threshold_pace
            ]
            block = sum(lap.distance_m for lap in qualifying)
            specific_m += block
            longest_block_m = max(longest_block_m, max((lap.distance_m for lap in qualifying), default=0.0))
        elif classification.workout_type in {WorkoutType.TEMPO, WorkoutType.RACE, WorkoutType.TEST}:
            gap_pace = activity_pace(activity)
            if gap_pace <= threshold_pace:
                specific_m += activity.distance_m
                longest_block_m = max(longest_block_m, activity.distance_m)

    # Over four weeks a well-prepared runner covers roughly 2.5× race distance
    # at race pace or faster, for track distances.
    required_m = goal.distance_m * 2.5
    volume_score = _ratio_score(specific_m, required_m, tolerance=0.55, anchor=72)
    # Being able to hold it in one block matters as much as the total.
    block_score = _ratio_score(longest_block_m, goal.distance_m * 0.4, tolerance=0.7, anchor=72)
    score = int(round(volume_score * 0.6 + block_score * 0.4))

    detail = (
        f"{fmt_num(specific_m / 1000, 1)} km a ritmo objetivo o mejor en 4 semanas "
        f"(bloque más largo: {longest_block_m:.0f} m)."
    )
    gap = ""
    if specific_m < required_m:
        missing = max(0.0, required_m - specific_m) / 1000
        gap = (
            f"Faltan unos {fmt_num(missing, 1)} km a ritmo de carrera para sostener "
            f"{fmt_pace(goal_pace)} el día de la competencia."
        )
    return CapabilityScore(Capability.SPECIFIC_ENDURANCE, score, detail, gap)


def _aerobic_base(activities: list[Activity], zones: PaceZones, goal: Goal) -> CapabilityScore:
    """Weekly volume and long run relative to what the distance demands."""
    from .load import weekly_summaries

    weeks = weekly_summaries(activities, zones, weeks=6)
    if not weeks:
        return CapabilityScore(Capability.AEROBIC_BASE, 30, "Sin historial suficiente.", "Falta volumen registrado.")

    complete = weeks[:-1] if len(weeks) > 1 else weeks  # ignore the in-progress week
    mean_km = statistics.mean(week.km for week in complete[-4:])
    long_run = max(week.long_run_km for week in complete[-4:])

    # Required volume scales with the fitness the goal demands and with distance.
    distance_factor = 0.75 if goal.distance_m <= 1600 else 0.9 if goal.distance_m <= 3200 else 1.0
    required_km = (22 + 0.72 * zones.vdot) * distance_factor
    required_long = max(12.0, goal.distance_m / 1000 * (2.6 if goal.distance_m >= 5000 else 6.0))

    volume_score = _ratio_score(mean_km, required_km, tolerance=0.22, anchor=70)
    long_score = _ratio_score(long_run, required_long, tolerance=0.30, anchor=70)
    score = int(round(volume_score * 0.65 + long_score * 0.35))

    detail = f"{fmt_num(mean_km, 0)} km/semana de promedio, tirada larga de {fmt_num(long_run, 1)} km."
    gap = ""
    if mean_km < required_km:
        gap = (
            f"Tu base sostiene menos de lo que pide el objetivo: la referencia es "
            f"{fmt_num(required_km, 0)} km/semana."
        )
    return CapabilityScore(Capability.AEROBIC_BASE, score, detail, gap)


def _closing(activities: list[Activity], zones: PaceZones) -> CapabilityScore:
    """Does the athlete hold — or improve — pace at the end of hard work?"""
    deltas: list[float] = []
    for activity in _recent(activities, 42):
        classification = classify(activity, zones)
        seg = classification.segmentation
        if seg.structured and seg.rep_count >= 4:
            paces = [lap_pace(lap) for lap in seg.work]
            body = statistics.mean(paces[:-2])
            tail = statistics.mean(paces[-2:])
            deltas.append((tail - body) / body)
        elif classification.workout_type in {WorkoutType.LONG, WorkoutType.TEMPO}:
            splits = activity.splits_km or activity.laps
            usable = [lap for lap in splits if lap.distance_m > 800]
            if len(usable) >= 5:
                paces = [lap_pace(lap) for lap in usable]
                body = statistics.mean(paces[:-2])
                tail = statistics.mean(paces[-2:])
                deltas.append((tail - body) / body)

    if not deltas:
        return CapabilityScore(Capability.CLOSING, 50, "Sin datos suficientes de cierre.", "")

    mean_delta = statistics.mean(deltas)
    # 0% drift scores 70; finishing 3% faster scores 100; fading 3% scores 25.
    score = int(max(0, min(100, round(70 - mean_delta * 1000))))
    direction = "más rápido" if mean_delta < 0 else "más lento"
    detail = (
        f"En las últimas {len(deltas)} sesiones cerraste {fmt_num(abs(mean_delta) * 100, 1)} % "
        f"{direction} que el promedio."
    )
    gap = ""
    if score < 70:
        gap = "Perdés ritmo en el tramo final: el cierre es una capacidad a entrenar, no solo una consecuencia."
    return CapabilityScore(Capability.CLOSING, score, detail, gap)


def _recovery(
    activities: list[Activity],
    zones: PaceZones,
    feedback: dict[str, Feedback],
    form_ratio: float,
) -> CapabilityScore:
    """How well the athlete absorbs work: between reps, and between days."""
    components: list[float] = []
    details: list[str] = []
    window = _recent(activities, 42)
    # Only recent feedback counts — a niggle from three months ago says nothing
    # about how well the athlete is absorbing work today.
    recent_feedback = [feedback[act.id] for act in window if act.id in feedback]

    drops: list[float] = []
    for activity in window:
        seg = classify(activity, zones).segmentation
        if not seg.structured or not seg.recovery:
            continue
        for work_lap, rest_lap in zip(seg.work, seg.recovery):
            if work_lap.max_heartrate and rest_lap.average_heartrate:
                drops.append(work_lap.max_heartrate - rest_lap.average_heartrate)
    if drops:
        mean_drop = statistics.mean(drops)
        components.append(max(0.0, min(100.0, (mean_drop - 8) / 22 * 100)))
        details.append(f"caída de {fmt_num(mean_drop, 0)} ppm entre repeticiones")

    legs = [fb.legs for fb in recent_feedback if fb.legs]
    if legs:
        recent_legs = statistics.mean(legs[-10:])
        components.append(max(0.0, min(100.0, (recent_legs - 1) / 4 * 100)))
        details.append(f"sensación de piernas {fmt_num(recent_legs, 1)}/5")

    # Positive form means the athlete is absorbing the load rather than sinking.
    components.append(max(0.0, min(100.0, 60 + form_ratio * 180)))

    niggles = sum(1 for fb in recent_feedback if fb.niggle_severity >= 2)
    score = int(round(statistics.mean(components))) if components else 50
    if niggles:
        score = max(0, score - min(20, niggles * 6))
        details.append(f"{niggles} sesión(es) con molestias")

    gap = ""
    if score < 70:
        gap = "La recuperación limita cuántos estímulos fuertes podés encadenar por semana."
    return CapabilityScore(
        Capability.RECOVERY, score, ("Basado en " + ", ".join(details) + ".") if details else "Datos limitados.", gap
    )


# --- assembly ----------------------------------------------------------------

def assess_readiness(
    goal: Goal,
    activities: list[Activity],
    zones: PaceZones,
    feedback: dict[str, Feedback] | None = None,
    form_ratio: float = 0.0,
) -> RaceReadiness:
    """Full capability breakdown for one goal."""
    feedback = feedback or {}
    goal_vdot = required_vdot(goal) or zones.vdot

    scores = [
        _speed(activities, zones, goal, goal_vdot),
        _specific_endurance(activities, zones, goal, goal_vdot),
        _aerobic_base(activities, zones, goal),
        _closing(activities, zones),
        _recovery(activities, zones, feedback, form_ratio),
    ]

    weights = weight_profile(goal.distance_m)
    overall = int(round(sum(score.score * weights[score.capability] for score in scores)))

    # The limiter is the capability whose shortfall costs the most, not simply
    # the lowest number — a weak capability that barely matters is not the issue.
    limiter = max(scores, key=lambda score: (100 - score.score) * weights[score.capability])
    return RaceReadiness(
        goal=goal,
        overall=overall,
        capabilities=scores,
        limiter=limiter,
        summary=_summary(goal, scores, limiter, overall),
    )


def _summary(goal: Goal, scores: list[CapabilityScore], limiter: CapabilityScore, overall: int) -> str:
    strongest = max(scores, key=lambda score: score.score)
    parts: list[str] = []

    if strongest.score >= 85:
        parts.append(f"Ya tenés {strongest.capability.value.lower()} suficiente para el objetivo.")
    if limiter.gap:
        parts.append(f"La principal limitación es {limiter.capability.value.lower()}: {limiter.gap}")
    elif overall >= 90:
        parts.append("No hay una limitación clara: el trabajo pendiente es llegar fresco.")
    else:
        parts.append(f"El margen de mejora más grande está en {limiter.capability.value.lower()}.")
    return " ".join(parts)


def race_strategy(goal: Goal, prediction_time_s: float, readiness: RaceReadiness) -> tuple[list[tuple[str, float]], str]:
    """Recommended splits plus the reasoning for how to run the race."""
    distance_km = goal.distance_m / 1000
    target = goal.target_time_s or prediction_time_s
    mean_pace = target / distance_km

    closing = readiness.by(Capability.CLOSING).score
    # An athlete who fades gets a conservative opening; one who closes well can
    # afford an even start and use the last third.
    if closing >= 78:
        shape = [1.005, 1.002, 0.995, 0.990]
        note = (
            "Salí a ritmo medio y usá tu cierre: tus sesiones muestran que ganás "
            "terreno en el tramo final, no al principio."
        )
    elif closing >= 55:
        shape = [1.002, 1.000, 1.000, 0.996]
        note = "Ritmo parejo de principio a fin. No regales el primer kilómetro."
    else:
        shape = [1.012, 1.004, 0.998, 0.988]
        note = (
            "Arrancá 2–3 s/km por debajo del ritmo medio. Tu patrón reciente es "
            "perder ritmo en el tramo final, y salir rápido lo agrava."
        )

    splits: list[tuple[str, float]] = []
    segments = _split_points(goal.distance_m)
    for index, (label, segment_km) in enumerate(segments):
        factor = shape[min(index * len(shape) // max(len(segments), 1), len(shape) - 1)]
        splits.append((label, mean_pace * factor * segment_km))
    return splits, note


def _split_points(distance_m: float) -> list[tuple[str, float]]:
    """Sensible checkpoints for the distance, as (label, segment length in km)."""
    if distance_m <= 1600:
        count = int(distance_m // 400)
        return [(f"{(index + 1) * 400} m", 0.4) for index in range(count)]
    if distance_m <= 3200:
        count = int(distance_m // 800)
        return [(f"{(index + 1) * 800} m", 0.8) for index in range(count)]
    count = int(distance_m // 1000)
    return [(f"km {index + 1}", 1.0) for index in range(count)]


def cumulative_splits(splits: list[tuple[str, float]]) -> list[tuple[str, float, float]]:
    """(label, segment seconds, elapsed seconds) for display."""
    elapsed = 0.0
    rows = []
    for label, seconds in splits:
        elapsed += seconds
        rows.append((label, seconds, elapsed))
    return rows
